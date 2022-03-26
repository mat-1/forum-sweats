from cProfile import label
import io
import config
from forumsweats import discordbot
from forumsweats.commandparser import Context, Member, Time
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
aliases = ('ticket')
roles = ('mod', 'helper')
channels = None
args = ''
allowed_roles = ['mod', 'helper', 'admin']

image_template = '''<img src="%s">'''

post_template = '''
    <div class="post">
        <img src="%s" alt="Avatar" class="avatar">
        <div class="content">
            <br>%s</br>
            %s
        </div>
        %s
    </div>

'''

html_template = '''
<!DOCTYPE html>
<html lang="en">

</html>
<body>
    posts
</body>

<style>

body {
  background-color: #23272a;
}
.post {
    float: inline-start;
    width: 100%;
}
.content {
    color: white;
    padding-left: 10px;
    float: left;
    inline-size: 50%;
    overflow-wrap: break-word;
}
.avatar {
  float: left;
  vertical-align: middle;
  width: 50px;
  height: 50px;
  border-radius: 50%;
}
</style>
'''


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

async def close_ticket(interaction: discord.Interaction):
    messages = interaction.channel.history(limit=200, oldest_first=True)

    posts = ''
    async for message in messages:
        avatar = message.author.avatar or message.author.default_avatar
        name = message.author.name
        content = message.content
        attachments = ''
        for image in message.attachments:
            attachments += image_template % (image.url)

        posts += post_template % (avatar, name, content, attachments)
    finale = html_template.replace('posts', posts)
    file = io.StringIO(finale)
    log_channel = message.guild.get_channel(config.channels['logs'])
    await log_channel.send(file=discord.File(file, filename=f'{interaction.channel.name}.html'))
    await interaction.channel.delete()

    '''
    channel = interaction.channel
    await channel.edit(name=f'closed-{channel.name.rsplit("-", 1)[1]}')
    await channel.send(f'This ticket has been closed by { interaction.user.mention }.')
    ticket_types = await db.get_ticket_types()
    for _tickets in ticket_types: # Ugly, but it works.
        for tickets in _tickets:
            for ticket in tickets:
                print(ticket)
                user = discordbot.client.get_user(ticket['user_id'])
                if ticket['channel_id'] == interaction.channel_id:
                    await channel.set_permissions(user, read_messages=False, send_messages=False, view_channel=False)
    await interaction.response.defer()
    await interaction.delete_original_message()
    '''

async def create_ticket(user: User, guild: discord.Guild, name: str, id: int):
    async def create_category():
        category_name = f'📩 ⼁ { name }s ⼁ 📩'
        categoires = guild.categories
        category = discord.utils.find(lambda m: m.name == category_name, categoires)
        if category:
            await category.set_permissions(user, view_channel=False)
            return category

        category = await guild.create_category(category_name)
        await category.set_permissions(guild.default_role, view_channel=False)
        return category
    async def create_channel(category: discord.CategoryChannel):
        text_id = '0' * (4 - len(str(id))) + str(id)
        channel = await category.create_text_channel(f'{name}-{text_id}')
        await channel.set_permissions(user, read_messages=True, send_messages=True, view_channel=True)
        return channel
    async def send_welcome_message(channel: discord.TextChannel):
        embed = discord.Embed(
            title=f'Welcome to { name }',
            description=f'Please use the reactions to interact with the ticket.',
        )
        close_button = discord.ui.Button(
            custom_id='close',
            label='Close',
            style=discord.ButtonStyle.red,
            emoji='🗑️',
            row=1
        )
        view = discord.ui.View(timeout=None)
        view.add_item(close_button)
        
        await channel.send(embed=embed, view=view, content=f'Welcome { user.mention }!')

    category = await create_category()
    channel = await create_channel(category)
    await send_welcome_message(channel)


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

    embed = discord.Embed(
        title=f'{title}',
        description=f'{description}',
    )
    button = discord.ui.Button(
        custom_id='create_ticket',
        emoji='📩',
        style=discord.ButtonStyle.gray,
        row=1
    )
    view = discord.ui.View(timeout=None)
    view.add_item(button)


    ticket_message = await channel.send(embed=embed, view=view)
    await db.create_new_ticket_type(ticket_name, ticket_message.id)
    discordbot.ticket_types = await db.get_ticket_types()

    await message.send(f'Ok, created message {ticket_message.jump_url}')
