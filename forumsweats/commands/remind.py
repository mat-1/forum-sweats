from forumsweats.commandparser import Context, Member, Time
from forumsweats.discordbot import client
from utils import seconds_to_string
from typing import Any, Callable, Union
from datetime import datetime
from forumsweats import db
import discord
import asyncio
import config
import random
import time

name = 'remind'
aliases = ('remindme', 'reminder')
channels = ('bot-commands',)

async def run(message, length: Time, reason: str):
	'Allows you to remind yourself about something after a specified amount of time'
	print('remind', length, reason)
	if not length:
		await message.reply(message.channel, f'Invalid time. Usage: {message.prefix}remind <time> <reason>')
		return
	if not reason:
		await message.reply(message.channel, f'You must say what you want to be reminded about. Usage: {message.prefix}remind <time> <reason>')
		return
	
	reminder_created_message = await message.reply(
		embed=discord.Embed(
			description=f'Ok, you\'ll be reminded in {seconds_to_string(length)} "**{reason}**"',
			colour=discord.Colour.green()
		)
	)
	
	await db.create_new_reminder(
		reminder_created_message.id,
		reminder_created_message.jump_url,
		message.author.id,
		int(time.time() + float(length)),
		reason
	)

async def continue_reminder(message_id: int, message_url: str, creator_id: int, end: int, reason: str):
	'Continues a reminder'
	await asyncio.sleep(end - time.time())

	creator = client.get_user(creator_id)
	if creator:
		await creator.send(f'**{reason}** {message_url}')
	await db.end_reminder(message_id)

async def init():
	for reminder in await db.get_active_reminders():
		await continue_reminder(reminder['id'], reminder['message_url'], reminder['creator_id'], reminder['end'], reminder['reason'])
