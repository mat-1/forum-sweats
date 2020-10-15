
# hypixel forums.py v0.13

from bs4 import BeautifulSoup
import time
from . import aiocloudscraper
import aiohttp
import asyncio

ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:78.0) Gecko/20100101 Firefox/78.0'

s = aiocloudscraper.AsyncCloudScraper()
# s = aiohttp.ClientSession()

'''
User data:
- id (forum id)
- title (forum title, new member, well known, etc)
- name (forum username)
- follower_count (forum follower acount)
- messages (total number of forum posts)
'''

reaction_id_to_names = {
	'': 'All',
	'1': 'Like',

	'3': 'Funny',
	'4': 'Creative',
	'5': 'Dislike',

	'7': 'Agree',
	'8': 'Disagree',
	'9': 'Useful',
	'10': 'Mod Emerald',
	'11': 'Hype Train',
	'12': 'Admin Diamond',
	'13': 'Helper Lapis',
	'14': 'Wat',
	'15': 'Bug',
}


def avatar_from_id(user_id):
	id_start = str(user_id)[:-3]
	print('id_start', id_start)
	return f'https://hypixel.net/data/avatars/l/{id_start}/{user_id}.jpg'


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
		'content-type': 'application/x-www-form-urlencoded',
	})

async def get_recent_posts(forum='skyblock', page=1):
	forum_ids = {
		'skyblock': 157,
		'skyblock-patch-notes': 158,
		'news-and-announcements': 4,
		'official-hypixel-minecraft-server': 'official-hypixel-minecraft-server',
		'hypixel-server-discussion': 'official-hypixel-minecraft-server'
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
		author_id = int(post_main_el.find(class_='username')['data-user-id'])
		author_name = post_main_el.find(class_='username').text.strip()
		created_time_string = post_main_el.find(class_='u-dt')['data-time']
		created_time = int(created_time_string)
		post_id = url.split('/')[-2].split('.')[-1]

		last_message_author_id = int(post_main_el.findAll(class_='username')[-1]['data-user-id'])
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

async def get_thread(post_id, is_thread=True):
	post_url = f'https://hypixel.net/threads/{post_id}/'
	r = await s.get(post_url)
	forum_post_html = await r.text()
	soup = BeautifulSoup(forum_post_html, features='html5lib')
	post_element = soup.find(class_='message-inner')
	if not post_element: return
	body_text = post_element.find(class_='message-body').text.strip()
	body_image_element = post_element.find(class_='message-body').find('img')
	if body_image_element:
		body_image = body_image_element['src']
	else:
		body_image = None

	user_name = post_element.find(class_='username').text.strip()
	user_id = post_element.find(class_='username')['data-user-id'].strip()
	user_title = post_element.find(class_='userTitle').text.strip()
	user_avatar_url = avatar_from_id(user_id)
	user_url = f'https://hypixel.net/members/{user_id}'


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
		'image': body_image,
		'author': {
			'name': user_name,
			'url': user_url,
			'id': user_id,
			'title': user_title,
			'avatar_url': user_avatar_url,
		}
	}

async def get_post_reactions(post_id):
	post_url = f'https://hypixel.net/posts/{post_id}/reactions'
	r = await s.get(post_url)
	post_reactions_html = await r.text()
	soup = BeautifulSoup(post_reactions_html, features='html5lib')
	

	reactions = {}

	for tab_el in soup.findAll(class_='tabs-tab'):
		if not tab_el['id']:
			continue
		reaction_id = tab_el['id'].split('-')[-1]
		reaction_count = int(tab_el.text.strip().split(' ')[-1].strip('()'))
		if reaction_id not in reactions:
			reactions[reaction_id] = 0
		reactions[reaction_id] += reaction_count
	return reactions


async def get_member(member_id, ratings=False):
	member_data = {}

	try:
		member_about_data = await get_member_about(member_id)
		if member_about_data['name'] == 'Oops! We ran into some problems.':
			print('Oops! We ran into some problems.')
		else:
			member_data.update(member_about_data)
	except:
		pass

	r = await s.get(f'https://hypixel.net/members/{member_id}/tooltip')

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

	icon_url = avatar_from_id(member_id)

	forum_username = soup.find(class_='username').text.strip()

	member_data.update({
		'id': int(member_id),
		'name': forum_username,
		'messages': message_count,
		'reactions': {
			'positive_total': positive_reactions_count
		},
		'avatar_url': icon_url
	})

	return member_data

class ProfileLimited(Exception): pass

async def get_member_about(member_id):
	r = await s.get(f'https://hypixel.net/members/{member_id}/about')
	if r.status == 429:
		await asyncio.sleep(1)
		return await get_member_about(member_id)
	if r.status == 403:
		raise ProfileLimited('This member limits who may view their full profile.')
	member_about_html = await r.text()
	soup = BeautifulSoup(member_about_html, features='html5lib')
	
	try:
		followers_block_row = soup\
			.find(class_='block-body')\
			.findAll(class_='block-row', recursive=False)\
			[-2]
		preview_count = len(followers_block_row.find(class_='listHeap').findAll('li'))
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

async def get_posts_from_member(member_id):
	posts = []

	actual_last_page = False

	url = f'https://hypixel.net/search/member?user_id={member_id}'
	while not actual_last_page:
		r = None
		while not r:
			r = await s.get(url)
			if r.status == 429:
				await asyncio.sleep(5)
				r = None
		initial_url = str(r.url)
		page = 1
		last_page = False
		while not last_page:
			soup = BeautifulSoup(await r.text(), features='html5lib')
			post_els = soup.findAll(class_='contentRow-main')
			for post_el in post_els:
				post_url = post_el.find('h3').find('a')['href']
				post_title = post_el.find('h3').text.strip()
				post_id = int(post_url.strip('/').split('/')[-1].split('-')[-1].split('.')[-1])
				post_time = int(post_el.find('time')['data-time'])
				forum_url = post_el.find(class_='listInline').findAll('a')[-1]['href']
				try:
					forum_id = int(forum_url.split('.')[-1].strip('/'))
				except ValueError:
					forum_id = 1
				author_id = int(post_el.find(class_='username')['data-user-id'])
				author_name = post_el.find(class_='username').text.strip()
				posts.append({
					'title': post_title,
					'id': post_id,
					'forum_id': forum_id,
					'time': post_time,
					'author': {
						'id': author_id,
						'name': author_name,
					}
				})
			if not post_els:
				actual_last_page = True
				last_page = True
				# with open('e.html', 'w') as f:
				# 	f.write(soup.prettify())
			else:
				page += 1
				url = initial_url + f'?page={page}'
				# r = await s.get(url)
				r = None
				while not r:
					r = await s.get(url)
					if r.status == 429:
						await asyncio.sleep(5)
						r = None
				if r.url.query.get('page', '1') != str(page):
					last_page = True
					url = initial_url + 'older?before=' + str(post_time)
	return posts