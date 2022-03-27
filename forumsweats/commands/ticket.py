from cProfile import label
import io
import config
from forumsweats import discordbot
from forumsweats.commandparser import Context, Member, Time
from discord.reaction import Reaction
from discord.message import Message
from forumsweats.logger import send_log_message
from forumsweats.setuptour import check_channel, check_content, prompt_input, quick_prompt
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
    view = discord.ui.View(timeout=30)
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

    setting_message = await message.send(embed=embed, view=view)

    async def timeout():
        await setting_message.edit(content='Timed out.', embed=None, view=None)

    view.on_timeout = timeout

async def create_html_from_channel(interaction: discord.Interaction):
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

    return html_template.replace('posts', posts)

def get_ticket_from_ticket_data(ticket_data, interaction):
    tickets = ticket_data['tickets']
    for ticket in tickets:
        if ticket['channel_id'] == interaction.channel.id: return ticket

async def delete_ticket(interaction: discord.Interaction):
    ticket_info_data = await db.get_ticket_by_channel(interaction.channel.id)
    if ticket_info_data is None: return

    ticket_data = get_ticket_from_ticket_data(ticket_info_data, interaction)
    if ticket_data is None: return
    ticket_id = get_text_id(ticket_data['id'])

    html = await create_html_from_channel(interaction);
    file = io.StringIO(html)
    ticket_name = ticket_info_data['name']
    discord_file = discord.File(file, filename=f'{ticket_name}-{ticket_id}.html')
    embed = discord.Embed(
        description=f'Ticket {ticket_name}-{ticket_id} deleted by {interaction.user.mention}',
    )
    await interaction.channel.delete()
    await send_log_message(file=discord_file, embed=embed)

async def reopen_ticket(interaction: discord.Interaction):
    ticket_info_data = await db.get_ticket_by_channel(interaction.channel.id)
    if ticket_info_data is None: return

    ticket_data = get_ticket_from_ticket_data(ticket_info_data, interaction)
    if ticket_data is None: return

    ticket_id = get_text_id(ticket_data['id'])
    user_id = ticket_data['user_id']
    user = discordbot.client.get_user(user_id)
    controller_message_id = ticket_data['controller_message']
    controller_message: discord.PartialMessage = interaction.channel.get_partial_message(controller_message_id)
    embed = discord.Embed(
        title=f'Welcome to { name }',
         description=f'Please use the reactions to interact with the ticket.',
    )
    ticket_name = ticket_info_data['name']
    await interaction.channel.edit(name=f"{ticket_name}-{ticket_id}")
    close_button = discord.ui.Button(
        custom_id='close',
        label='Close',
        style=discord.ButtonStyle.red,
        emoji='🗑️',
        row=1
    )
    view = discord.ui.View(timeout=None)
    view.add_item(close_button)

    await interaction.channel.set_permissions(user, read_messages=True, send_messages=True, view_channel=True)

    reopen_embed = discord.Embed(
        description=f'Ticket reopened by { interaction.user.mention }',
        color=discord.Color.green()
    )
    try:
        await controller_message.edit(embed=embed, view=view, content=f'Welcome { user.mention }!')
        await controller_message.reply(embed=reopen_embed)
    except discord.errors.NotFound:
        controller_message = await interaction.channel.send(embed=embed, view=view, content=f'Welcome { user.mention }!')
        await controller_message.reply(embed=reopen_embed)


async def close_ticket(interaction: discord.Interaction):
    ticket_info_data = await db.get_ticket_by_channel(interaction.channel.id)
    if ticket_info_data is None: return

    ticket_data = get_ticket_from_ticket_data(ticket_info_data, interaction)
    if ticket_data is None: return

    ticket_id = get_text_id(ticket_data['id'])
    user_id = ticket_data['user_id']
    user = discordbot.client.get_user(user_id)
    controller_message_id = ticket_data['controller_message']
    controller_message: discord.PartialMessage = interaction.channel.get_partial_message(controller_message_id)
    
    embed = discord.Embed(
        title=f'Ticket closed',
        description=f'Please use the reactions to interact with the ticket.',
    )
    reopen_button = discord.ui.Button(
        custom_id='reopen',
        label='Reopen',
        style=discord.ButtonStyle.green,
        emoji='🔓',
        row=1
    )
    delete_channel = discord.ui.Button(
        custom_id='delete_ticket',
        label='Delete channel',
        style=discord.ButtonStyle.red,
        emoji='🗑️',
        row=1
    )
    view = discord.ui.View(timeout=None)
    view.add_item(reopen_button)
    view.add_item(delete_channel)
    ticket_closed_embed = discord.Embed(
            description=f'Ticket closed by {interaction.user.mention}',
            color=discord.Color.red()
    )

    try:
        await controller_message.edit(content='Ticket closed.', embed=embed, view=view)
        await controller_message.reply(embed=ticket_closed_embed)
    except discord.errors.NotFound:
        ticket_closed_message = await interaction.channel.send(content='Ticket closed.', embed=embed, view=view)
        await ticket_closed_message.reply(embed=ticket_closed_embed)

    await db.close_ticket(ticket_id)

    await interaction.channel.edit(name=f"closed-{ticket_id}")
    await interaction.channel.set_permissions(user, read_messages=False, send_messages=False, view_channel=False)

def get_text_id(id: int):
    return '0' * (4 - len(str(id))) + str(id)

async def create_ticket(user: User, guild: discord.Guild, name: str, id: int):

    async def create_category():
        category_name = f'📩 ⼁ { name }s ⼁ 📩'
        categoires = guild.categories
        category = discord.utils.find(lambda m: m.name == category_name, categoires)
        if category:
            await category.set_permissions(user, view_channel=False)
            return category

        category = await guild.create_category(category_name)
        await category.edit(position=3)
        await category.set_permissions(guild.default_role, view_channel=False)
        return category

    async def create_channel(category: discord.CategoryChannel):
        text_id = get_text_id(id)
        channel = await category.create_text_channel(f'{name}-{text_id}')
        try:
            ticket_support_id = config.roles.get('tickets_support')
            ticket_support = guild.get_role(ticket_support_id)
            await channel.set_permissions(ticket_support, read_messages=True, send_messages=True, view_channel=True)
        except:
            pass
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
        
        return await channel.send(embed=embed, view=view, content=f'Welcome { user.mention }!')
    await db.set_cooldown('ticket', user.id)
    category = await create_category()
    channel = await create_channel(category)
    controller_message = await send_welcome_message(channel)
    await db.create_ticket(name, channel.id, user.id, id, controller_message.id)


async def create_new(message: Context):

    title: int = await quick_prompt(
        message,
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
    
    description: int = await quick_prompt(
        message,
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
    
    ticket_name: int = await quick_prompt(
        message,
        prompt_message='Please enter the ticket type name.',
        invalid_message='Invalid name',
        check=check_content
    )

    if ticket_name is None:
        return

    channel: int = await quick_prompt(
        message,
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
