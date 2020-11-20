from urllib.parse import quote_plus
from ..betterbot import Member
import discord
import random
import json

name = 'sub'
aliases = ['simp', 'bobuxsub', 'subscribe', 'bobuxsubscribe', 'bobuxsimp']


async def run(message, member: Member = None):
	if not member:
		return await message.channel.send('Invalid member.')
	await message.channel.send('ok')
