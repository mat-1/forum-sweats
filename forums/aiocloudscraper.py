import cloudscraper
import asyncio
import aiohttp
from cloudscraper.exceptions import (
	CloudflareCode1020,
	CloudflareIUAMError,
	CloudflareChallengeError,
	CloudflareCaptchaProvider
)
import re
from copy import deepcopy
from urllib.parse import urlparse, urljoin
import sys
from cloudscraper.user_agent import User_Agent
from cloudscraper import CipherSuiteAdapter
import copyreg
import ssl

class AsyncCloudScraper(cloudscraper.CloudScraper):
	def __init__(self, *args, **kwargs):
		self.s = aiohttp.ClientSession()
		self.debug = kwargs.pop('debug', False)
		self.delay = kwargs.pop('delay', None)
		self.cipherSuite = kwargs.pop('cipherSuite', None)
		self.ssl_context = kwargs.pop('ssl_context', None)
		self.interpreter = kwargs.pop('interpreter', 'native')
		self.recaptcha = kwargs.pop('recaptcha', {})
		self.requestPreHook = kwargs.pop('requestPreHook', None)
		self.requestPostHook = kwargs.pop('requestPostHook', None)

		self.allow_brotli = kwargs.pop(
			'allow_brotli',
			True if 'brotli' in sys.modules.keys() else False
		)

		self.user_agent = User_Agent(
			allow_brotli=self.allow_brotli,
			browser=kwargs.pop('browser', None)
		)

		self._solveDepthCnt = 0
		self.solveDepth = kwargs.pop('solveDepth', 3)

		super(AsyncCloudScraper, self).__init__(*args, **kwargs)

		# pylint: disable=E0203
		if 'requests' in self.headers['User-Agent']:
			# ------------------------------------------------------------------------------- #
			# Set a random User-Agent if no custom User-Agent has been set
			# ------------------------------------------------------------------------------- #
			self.headers = self.user_agent.headers
			if not self.cipherSuite:
				self.cipherSuite = self.user_agent.cipherSuite

		if isinstance(self.cipherSuite, list):
			self.cipherSuite = ':'.join(self.cipherSuite)

		self.mount(
			'https://',
			CipherSuiteAdapter(
				cipherSuite=self.cipherSuite,
				ssl_context=self.ssl_context
			)
		)

		# purely to allow us to pickle dump
		copyreg.pickle(ssl.SSLContext, lambda obj: (obj.__class__, (obj.protocol,)))

	async def request(self, method, url, *args, **kwargs):
		# pylint: disable=E0203
		if kwargs.get('proxies') and kwargs.get('proxies') != self.proxies:
			self.proxies = kwargs.get('proxies')

		# ------------------------------------------------------------------------------- #
		# Pre-Hook the request via user defined function.
		# ------------------------------------------------------------------------------- #

		if self.requestPreHook:
			(method, url, args, kwargs) = self.requestPreHook(
				self,
				method,
				url,
				*args,
				**kwargs
			)

		# ------------------------------------------------------------------------------- #
		# Make the request via aiohttp.
		# ------------------------------------------------------------------------------- #

		# response = await self.decodeBrotli(
		# 	super(AsyncCloudScraper, self).request(method, url, *args, **kwargs)
		# )
		response = await self.s.request(method, url, *args, **kwargs)

		# ------------------------------------------------------------------------------- #
		# Debug the request via the Response object.
		# ------------------------------------------------------------------------------- #

		if self.debug:
			self.debugRequest(response)

		# ------------------------------------------------------------------------------- #
		# Post-Hook the request aka Post-Hook the response via user defined function.
		# ------------------------------------------------------------------------------- #

		if self.requestPostHook:
			response = self.requestPostHook(self, response)

			if self.debug:
				self.debugRequest(response)
		
		# Check if Cloudflare anti-bot is on
		if await self.is_Challenge_Request(response):
			# ------------------------------------------------------------------------------- #
			# Try to solve the challenge and send it back
			# ------------------------------------------------------------------------------- #

			if self._solveDepthCnt >= self.solveDepth:
				_ = self._solveDepthCnt
				self.simpleException(
					cloudscraper.CloudflareLoopProtection,
					"!!Loop Protection!! We have tried to solve {} time(s) in a row.".format(_)
				)

			self._solveDepthCnt += 1
			response = await self.Challenge_Response(response, **kwargs)
		else:
			if response.status not in {429, 503}:
				self._solveDepthCnt = 0

		return response

	async def Challenge_Response(self, resp, **kwargs):
		if self.is_Captcha_Challenge(resp):
			# ------------------------------------------------------------------------------- #
			# double down on the request as some websites are only checking
			# if cfuid is populated before issuing Captcha.
			# ------------------------------------------------------------------------------- #

			resp = self.decodeBrotli(
				super(AsyncCloudScraper, self).request(resp.method, str(resp.url), **kwargs)
			)

			if not self.is_Captcha_Challenge(resp):
				return resp

			# ------------------------------------------------------------------------------- #
			# if no Captcha provider raise a runtime error.
			# ------------------------------------------------------------------------------- #

			if not self.recaptcha or not isinstance(self.recaptcha, dict) or not self.recaptcha.get('provider'):
				self.simpleException(
					CloudflareCaptchaProvider,
					"Cloudflare Captcha detected, unfortunately you haven't loaded an anti Captcha provider "
					"correctly via the 'recaptcha' parameter."
				)

			# ------------------------------------------------------------------------------- #
			# if provider is return_response, return the response without doing anything.
			# ------------------------------------------------------------------------------- #

			if self.recaptcha.get('provider') == 'return_response':
				return resp

			self.recaptcha['proxies'] = self.proxies
			submit_url = self.Captcha_Challenge_Response(
				self.recaptcha.get('provider'),
				self.recaptcha,
				await resp.text(),
				str(resp.url)
			)
		else:
			# ------------------------------------------------------------------------------- #
			# Cloudflare requires a delay before solving the challenge
			# ------------------------------------------------------------------------------- #

			if not self.delay:
				try:
					delay = float(
						re.search(
							r'submit\(\);\r?\n\s*},\s*([0-9]+)',
							await resp.text()
						).group(1)
					) / float(1000)
					if isinstance(delay, (int, float)):
						self.delay = delay
				except (AttributeError, ValueError):
					self.simpleException(
						CloudflareIUAMError,
						"Cloudflare IUAM possibility malformed, issue extracing delay value."
					)
			
			await asyncio.sleep(self.delay)

			# ------------------------------------------------------------------------------- #
			body = await resp.text()
			
			submit_url = self.IUAM_Challenge_Response(
				body,
				str(resp.url),
				self.interpreter
			)

		# ------------------------------------------------------------------------------- #
		# Send the Challenge Response back to Cloudflare
		# ------------------------------------------------------------------------------- #

		if submit_url:

			def updateAttr(obj, name, newValue):
				try:
					obj[name].update(newValue)
					return obj[name]
				except (AttributeError, KeyError):
					obj[name] = {}
					obj[name].update(newValue)
					return obj[name]

			cloudflare_kwargs = deepcopy(kwargs)
			cloudflare_kwargs['allow_redirects'] = False
			cloudflare_kwargs['data'] = updateAttr(
				cloudflare_kwargs,
				'data',
				submit_url['data']
			)

			urlParsed = urlparse(str(resp.url))
			cloudflare_kwargs['headers'] = updateAttr(
				cloudflare_kwargs,
				'headers',
				{
					'Origin': '{}://{}'.format(urlParsed.scheme, urlParsed.netloc),
					'Referer': str(resp.url)
				}
			)

			challengeSubmitResponse = await self.request(
				'POST',
				submit_url['url'],
				**cloudflare_kwargs
			)

			# ------------------------------------------------------------------------------- #
			# Return response if Cloudflare is doing content pass through instead of 3xx
			# else request with redirect URL also handle protocol scheme change http -> https
			# ------------------------------------------------------------------------------- #

			if not str(challengeSubmitResponse.status)[0] == '3':
				return challengeSubmitResponse

			else:
				cloudflare_kwargs = deepcopy(kwargs)
				cloudflare_kwargs['headers'] = updateAttr(
					cloudflare_kwargs,
					'headers',
					{'Referer': str(challengeSubmitResponse.url)}
				)

				if not urlparse(challengeSubmitResponse.headers['Location']).netloc:
					redirect_location = urljoin(
						str(challengeSubmitResponse.url),
						challengeSubmitResponse.headers['Location']
					)
				else:
					redirect_location = challengeSubmitResponse.headers['Location']

				return await self.request(
					resp.method,
					redirect_location,
					**cloudflare_kwargs
				)

		# ------------------------------------------------------------------------------- #
		# We shouldn't be here...
		# Re-request the original query and/or process again....
		# ------------------------------------------------------------------------------- #

		return await self.request(resp.method, str(resp.url), **kwargs)

	# ------------------------------------------------------------------------------- #

	async def is_Challenge_Request(self, resp):
		if self.is_Firewall_Blocked(resp):
			self.simpleException(
				CloudflareCode1020,
				'Cloudflare has blocked this request (Code 1020 Detected).'
			)

		if self.is_New_IUAM_Challenge(resp):
			self.simpleException(
				CloudflareChallengeError,
				'Detected the new Cloudflare challenge.'
			)

		if self.is_Captcha_Challenge(resp) or await self.is_IUAM_Challenge(resp):
			if self.debug:
				print('Detected Challenge.')
			return True

		return False

	@staticmethod
	async def is_IUAM_Challenge(resp):
		try:
			return (
				resp.headers.get('Server', '').startswith('cloudflare')
				and resp.status in [429, 503]
				and re.search(
					r'<form .*?="challenge-form" action="/.*?__cf_chl_jschl_tk__=\S+"',
					await resp.text(),
					re.M | re.S
				)
			)
		except AttributeError:
			pass

		return False