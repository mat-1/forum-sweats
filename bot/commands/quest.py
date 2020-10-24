import jsonminify
import os.path
import discord
import asyncio
import json

name = 'quest'
aliases = ['bobuxquest', 'quests', 'bobuxquests']


def read_quest_json(quest_id):
	quest_path = os.path.join(os.path.dirname(__file__), '..', '..', 'quests', quest_id + '.json')
	with open(quest_path, 'rb') as f:
		data = f.read().decode()
		quest_data = json.loads(jsonminify.json_minify(data))
	return quest_data


class QuestArea:
	def __init__(self, area_data):
		self.id = area_data['id']
		self.text = area_data.get('text') or None
		self.footer_text = area_data.get('footer') or None
		self.next_area_requirements = area_data.get('next', [])

		self.is_dead = area_data.get('dead', False)
		self.is_win = area_data.get('win', False)


class Quest:
	def __init__(self, quest_id):
		self.quest_data = read_quest_json(quest_id)
		self.name = self.quest_data['name']

		self.reward_data = self.quest_data['reward']
		self.areas_data = self.quest_data['areas']

		self.areas = {area['id']: QuestArea(area) for area in self.areas_data}


class QuestSession:
	def __init__(self, member, quest_id):
		self.user = member
		self.quest = Quest(quest_id)
		self.area_id = 'start'
		self.quest_message = None
		self.ended = False
		self.completed = False

	def get_area(self):
		return self.quest.areas[self.area_id]

	def get_current_reactions(self):
		area = self.get_area()
		reactions = []
		for requirement in area.next_area_requirements:
			if 'react' in requirement:
				reactions.append(requirement['react'])
		return reactions

	def matches_requirement_reaction_add(self, reaction, user):
		if user.id != self.user.id: return False
		if reaction.message.id != self.quest_message.id: return False
		if str(reaction.emoji) not in self.get_current_reactions(): return False
		return True

	def register_reaction(self, reaction):
		area = self.get_area()
		for requirement in area.next_area_requirements:
			if 'react' in requirement:
				if requirement['react'] == str(reaction.emoji):
					self.area_id = requirement['area']
					return True
		return False

	def build_embed(self):
		area = self.get_area()
		description = area.text
		if area.is_dead:
			description += '\n\n**You failed the quest.**'
			self.ended = True
		if area.is_win:
			description += '\n\n**You have completed the quest.**'
			self.ended = True
			self.completed = True
		embed = discord.Embed(
			title=self.quest.name,
			description=description,
		)
		if area.footer_text:
			embed.set_footer(text=area.footer_text)
		return embed


async def wait_for_any(client, events, checks=[], timeout=None):
	futures = []
	for event, check in zip(events, checks):
		futures.append(client.wait_for(event, check=check))

	done, pending = await asyncio.wait(futures, return_when=asyncio.FIRST_COMPLETED)
	result = done.pop().result()

	for future in done:
		future.exception()

	for future in pending:
		future.cancel()

	return result


async def do_quest(client, member, channel, quest_id):
	q = QuestSession(member, quest_id)
	quest_message = await channel.send('...')
	q.quest_message = quest_message

	while not q.ended:
		area = q.get_area()
		embed = q.build_embed()

		await quest_message.clear_reactions()
		await quest_message.edit(content='', embed=embed)

		for emoji in q.get_current_reactions():
			await quest_message.add_reaction(emoji)

		events = []
		checks = []
		for requirement in area.next_area_requirements:
			if 'react' in requirement:
				events.append('reaction_add')
				checks.append(q.matches_requirement_reaction_add)
		result = await wait_for_any(client, events, checks)

		if isinstance(result[0], discord.Reaction):
			q.register_reaction(result[0])

	print('quest over')


async def run(message, quest_id: str):
	if not quest_id:
		await message.channel.send('soon')

	await do_quest(message.client, message.author, message.channel, quest_id)
