
# hypixel forums.py v0.7

from bs4 import BeautifulSoup
import time
from . import aiocloudscraper
import aiohttp
import asyncio

ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0'

s = aiocloudscraper.AsyncCloudScraper()

'''
User data:
- id (forum id)
- title (forum title, new member, well known, etc)
- name (forum username)
- follower_count (forum follower acount)

'''

async def login(email, password):
	r = await s.get('https://hypixel.net/login')
	if r.status == 429:
		await asyncio.sleep(1)
		return await login(email, password)
	login_html = await r.text()
	soup = BeautifulSoup(login_html, features='html5lib')
	_xfToken_el = soup.find(attrs={'name': '_xfToken'})
	_xfToken = _xfToken_el['value']
	r = await s.post('https://hypixel.net/login/login', data={
		'login': email,
		'password': password,
		'remember': '1',
		'_xfRedirect': 'https://hypixel.net/',
		'_xfToken': _xfToken
	}, headers={
		'content-type': 'application/x-www-form-urlencoded'
	})

async def get_recent_posts(forum='skyblock', page=1):
	forum_ids = {
		'skyblock': 157,
		'skyblock-patch-notes': 158,
		'news-and-announcements': 4,
	}
	forum_id = forum_ids.get(forum.lower().replace(' ', '-'), forum)
	r = await s.get(f'https://hypixel.net/forums/{forum_id}/page-{page}')
	url_page_part = str(r.url).split('/')[-1]
	# Reached max page
	if url_page_part.startswith('page-'):
		if url_page_part[5:] != str(page):
			return {}
	forum_listing_html = await r.text()
	soup = BeautifulSoup(forum_listing_html, features='html5lib')
	bs4_post_lists = soup.findAll(class_='structItem-cell--main')

	posts = []
	for post_main_el in bs4_post_lists:
		title = post_main_el.find(class_='structItem-title').text.strip()
		url = post_main_el.find(class_='structItem-title').a['href']
		author_id = post_main_el.find(class_='username')['data-user-id']
		author_name = post_main_el.find(class_='username').text.strip()
		created_time_string = post_main_el.find(class_='u-dt')['data-time']
		created_time = int(created_time_string)
		post_id = url.split('/')[-2].split('.')[-1]

		last_message_author_id = post_main_el.findAll(class_='username')[-1]['data-user-id']
		last_message_author_name = post_main_el.findAll(class_='username')[-1].text.strip()

		is_recent = (time.time() - created_time) < 60 * 60 * 24 * 2

		posts.append({
			'title': title,
			'url': url,
			'author': {
				'id': int(author_id),
				'name': author_name,
			},
			'last_message_author': {
				'id': int(last_message_author_id),
				'name': last_message_author_name
			},
			'time': created_time,
			'is_recent': is_recent,
			'id': int(post_id)
		})
	return posts

async def get_post(post_id):
	post_url = f'https://hypixel.net/threads/{post_id}/'
	r = await s.get(post_url)
	forum_post_html = await r.text()
	soup = BeautifulSoup(forum_post_html, features='html5lib')
	post_element = soup.find(class_='message-inner')
	body_text = post_element.find(class_='message-body').text.strip()
	user_title = post_element.find(class_='userTitle').text.strip()
	post_title = soup.find(class_='p-title-value').text.strip()

	created_time_string = soup.find(class_='u-dt')['data-time']
	created_time = int(created_time_string)

	is_recent = (time.time() - created_time) < 60 * 60 * 24 * 2

	return {
		'body': body_text,
		'title': post_title,
		'id': int(post_id),
		'is_recent': is_recent,
		'url': str(r.url),
		'author': {
			'title': user_title
		}
	}

async def reply(post_id, content):
	r = await s.get(f'https://hypixel.net/threads/post.{post_id}/')
	forum_post_html = await r.text()
	soup = BeautifulSoup(forum_post_html, features='html5lib')

	attachment_hash_el = soup.find(attrs={'name': 'attachment_hash'})
	attachment_hash_combined_el = soup.find(attrs={'name': 'attachment_hash_combined'})
	last_date_el = soup.find(attrs={'name': 'last_date'})
	last_known_date_el = soup.find(attrs={'name': 'last_known_date'})
	_xfToken_el = soup.find(attrs={'name': '_xfToken'})

	attachment_hash = attachment_hash_el['value']
	attachment_hash_combined = attachment_hash_combined_el['value']
	last_date = last_date_el['value']
	last_known_date = last_known_date_el['value']
	_xfToken = _xfToken_el['value']


	content_html = content
	r = await s.post(
		f'https://hypixel.net/threads/post.{post_id}/add-reply',
		data={
			'message_html': content_html,
			'attachment_hash': attachment_hash,
			'attachment_hash_combined': attachment_hash_combined,
			'last_date': last_date,
			'last_known_date': last_known_date,
			'_xfToken': _xfToken,
			'_xfRequestUri': f'/threads/post.{post_id}/',
			'_xfWithData': '1',
			'_xfToken': _xfToken,
			'_xfResponseType': 'json'
		}
	)

async def get_member(member_id):
	member_data = {}

	member_about_data = await get_member_about(member_id)
	member_data.update(member_about_data)

	r = await s.get(f'https://hypixel.net/members/{member_id}/')

	if r.status == 429:
		await asyncio.sleep(5)
		return await get_member(member_id)

	member_html = await r.text()
	soup = BeautifulSoup(member_html, features='html5lib')
	try:
		message_count = int(soup.find(class_='fauxBlockLink-linkRow').text.strip().replace(',', ''))
	except AttributeError:
		message_count = 0

	try:	
		positive_reactions_count = int(soup.find(class_='rating-summary').text.strip().replace(',', ''))
	except AttributeError:
		positive_reactions_count = 0

	member_id = member_about_data['id']

	icon_url = f'https://hypixel.net/data/avatars/l/{str(member_id)[:-3]}/{member_id}.jpg'

	member_data.update({
		'messages': message_count,
		'reactions': {
			'positive_total': positive_reactions_count
		},
		'avatar_url': icon_url
	})

	return member_data

async def get_member_about(member_id):
	r = await s.get(f'https://hypixel.net/members/{member_id}/about')
	if r.status == 429:
		await asyncio.sleep(1)
		return await get_member_about(member_id)
	member_about_html = await r.text()
	soup = BeautifulSoup(member_about_html, features='html5lib')
	
	try:
		followers_block_row = soup\
			.find(class_='block-body')\
			.findAll(class_='block-row', recursive=False)\
			[-2]
		preview_count = len(followers_block_row.find(class_='listHeap').find('li'))
		try:
			extra_count = int(followers_block_row.findAll('a')[-1].text.strip().split(' ')[2])
		except IndexError:
			extra_count = 0
		follower_count = preview_count + extra_count
	except:
		follower_count = 0

	forum_username = soup.find(class_='p-title-value').text.strip()


	return {
		'id': member_id,
		'name': forum_username,
		'follower_count': follower_count,
	}

async def search_members(query):
	r = await s.get(f'https://hypixel.net/')
	if r.status == 429:
		await asyncio.sleep(1)
		return await search_members(query)
	forum_index_html = await r.text()
	soup = BeautifulSoup(forum_index_html, features='html5lib')

	_xfToken_el = soup.find(attrs={'name': '_xfToken'})
	_xfToken = _xfToken_el['value'].replace(',', '%2C')

	url = f'https://hypixel.net/index.php?members/find&q={query}&_xfToken={_xfToken}&_xfResponseType=json'

	r = await s.get(url)
	if r.status == 429:
		await asyncio.sleep(2)
		return await search_members(query)

	try:
		data = await r.json()
	except aiohttp.client_exceptions.ContentTypeError:
		pass
	if 'results' not in data:
		await asyncio.sleep(2)
		return await search_members(query)
	results = data['results']

	results_clean = []

	for result in results:
		name = result['text']
		icon_html = result['iconHtml']
		icon_soup = BeautifulSoup(icon_html, features='html5lib')
		member_id = int(icon_soup.find(class_='avatar')['data-user-id'])
		results_clean.append({
			'id': member_id,
			'name': name
		})
	return results_clean

async def member_id_from_name(username):
	results = await search_members(username)
	for result in results:
		if username.lower() == result['name'].lower():
			return result['id']