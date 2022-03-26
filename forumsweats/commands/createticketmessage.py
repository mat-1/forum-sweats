from cProfile import label
from forumsweats.commandparser import Context, Member, Time
from forumsweats.discordbot import client
from discord.reaction import Reaction
from discord.message import Message
from forumsweats.setuptour import check_channel, check_content, prompt_input
from utils import seconds_to_string
from typing import Any, Callable
from discord.user import User
from datetime import datetime
from forumsweats import db
import discord
import asyncio
import time

name = 'tickets'
roles = ('mod', 'helper')
channels = None
args = ''


async def run(message: Context):
    async def on_interact(interaction: discord.interactions.Interaction):
        await interaction.response.defer()
        return interaction.user == message.author

    embed = discord.Embed(
        title='Ticket configuration menu',
        description='Press the corresponding button to change the configuration.',
        timestamp=datetime.fromtimestamp(time.time())
    )
    view = discord.ui.View(timeout=None)
    add_ticket = discord.ui.Button(
		custom_id='new_ticket',
        label='New ticket type',
		style=discord.ButtonStyle.success,
		emoji='🎫',
		row=1
	)
    remove_ticket = discord.ui.Button(
		custom_id='remove_ticket',
        label='Remove ticket type',
		style=discord.ButtonStyle.red,
		emoji='🗑️',
		row=1
	)
    add_ticket.callback = lambda _: create_new(message)
    view.interaction_check = on_interact
    view.add_item(add_ticket)
    view.add_item(remove_ticket)

    await message.send(embed=embed, view=view)


async def create_new(message: Context):

    title: int = await prompt_input(
        message.client,
        message.author,
        message.channel,
        prompt_message='Creating the embed for the ticket type.\nPlease enter the title you want to use.',
        invalid_message='Invalid name',
        check=check_content,
        preview=discord.Embed(
            title='**👉 Your title here 👈**',
            description='Description',
        )
    )

    if title is None:
        return
    
    description: int = await prompt_input(
        message.client,
        message.author,
        message.channel,
        prompt_message='Enter Description',
        invalid_message='Invalid name',
        check=check_content,
        preview=discord.Embed(
            title=f'**{title}**',
            description='**👉 Your description here 👈**',
        )
    )

    if description is None:
        return
    
    ticket_name: int = await prompt_input(
        message.client,
        message.author,
        message.channel,
        prompt_message='Please enter the ticket type name.',
        invalid_message='Invalid name',
        check=check_content
    )

    if ticket_name is None:
        return

    channel: int = await prompt_input(
        message.client,
        message.author,
        message.channel,
        prompt_message='Please enter the channel to post the message in.',
        invalid_message='Invalid channel',
        check=check_channel
    )

    if not isinstance(channel, discord.TextChannel):
        return

    ticket_message = await channel.send(embed=discord.Embed(
        title=f'{title}',
        description=f'{description}',
    ))
    

    await message.send(f'Ok, created message {ticket_message.jump_url}')
