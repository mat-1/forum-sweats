from typing import List, Optional
from attr import attr
import config
import discord
import io

from forumsweats import discordbot
from forumsweats.commandparser import Member

async def send_log_message(embed: Optional[discord.Embed] = None, content: Optional[str] = None, file: Optional[discord.File] = None, files: Optional[List[discord.File]] = None):
    try:
        log_channel = discordbot.client.get_channel(config.channels['logs'])
        await log_channel.send(embed=embed, content=content, file=file, files=files)
    except:
        print('Failed to log')

async def log_message_deletion(message):
    content = message.content
    attachments = message.attachments
    member = message.author
    avatar = member.avatar or member.default_avatar
    additional_content = ''
    message_file = None
    if attachments:
        additional_content = 'Attachments:'
        for attachment in attachments:
            additional_content += f'\n<{attachment.url}>'

    
    if len(content) > 500:
        buffer = io.StringIO(content)
        message_file = discord.File(buffer, 'message.txt')
        content = content[:500] + '...'
        additional_content += "\n[Message too long to display. See attachment for the full message.]"


    embed = discord.Embed(
        description=f'**Message by {message.author.mention} deleted in {message.channel.mention}** \n {content}',
        color=0xA40985
    )
    embed.set_author(name=f'{message.author}', icon_url=avatar)
    embed.set_footer(text=f'Message #{message.id}')

    await send_log_message(embed=embed, content=additional_content, file=message_file)

async def log_message_edition(before_message, after_message):
    content_before = before_message.content
    content_after = after_message.content
    files = []
    additional_content = ''

    if content_before == content_after:
        return
    
    if len(content_before) > 250:
        buffer = io.StringIO(content_before)
        files.append(discord.File(buffer, 'message_before_edition.txt'))
        additional_content += "\n[The message before edition was too long to display. See attachment for the full message.]"
        content_before = content_before[:250] + '...'

    if len(content_after) > 250:
        buffer = io.StringIO(content_after)
        files.append(discord.File(buffer, 'message_after_edition.txt'))
        additional_content += "\n[The message after edition was too long to display. See attachment for the full message.]"
        content_after = content_after[:250] + '...'

    
    member = before_message.author
    avatar = member.avatar or member.default_avatar
    embed = discord.Embed(
        description=f'**Message by {before_message.author.mention} edited in {before_message.channel.mention}** \n {content_before} \n **After** \n {content_after}',
        color=0xA40985,
    )
    embed.set_author(name=f'{before_message.author}', icon_url=avatar)
    embed.set_footer(text=f'Message #{before_message.id}')

    await send_log_message(embed=embed, content=additional_content, files=files)

async def log_role_update(before, after):
    content = f'**{after.mention} updated**'

    if(before.name != after.name):
        content += f'\nName: {before.name} -> {after.name}'
    if(before.color != after.color):
        content += f'\nColor: {before.color} -> {after.color}'
    if(before.permissions != after.permissions):
        content += f'\nPermissions: '
        for permission in after.permissions:
            if not permission in before.permissions:
                content += f'\n+ {permission}'
        for permission in before.permissions:
            if not permission in after.permissions:
                content += f'\n- {permission}'
    if(before.hoist != after.hoist):
        content += f'\nHoist: {before.hoist} -> {after.hoist}'
    if(before.mentionable != after.mentionable):
        content += f'\nMentionable: {before.mentionable} -> {after.mentionable}'
    if(before.managed != after.managed):
        content += f'\nManaged: {before.managed} -> {after.managed}'
    if(before.position != after.position):
        content += f'\nPosition: {before.position} -> {after.position}'

        

    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)


async def log_guild_channel_changes(before, after):
    content = ''
    if(not isinstance(before, discord.TextChannel)):
        return
    
    if not before.name == after.name:
        content += f'\nName: {before.name} -> {after.name}'
    if not before.topic == after.topic:
        content += f'\nTopic: {before.topic} -> {after.topic}'
    if not before.position == after.position:
        content += f'\nPosition: {before.position} -> {after.position}'
    if not before.slowmode_delay == after.slowmode_delay:
        content += f'\nSlowmode: {before.slowmode_delay} -> {after.slowmode_delay}'
    if not before.category == after.category:
        content += f'\nCategory: {before.category} -> {after.category}'
    if not before.nsfw == after.nsfw:
        content += f'\nNSFW: {before.nsfw} -> {after.nsfw}'
    
    if content == '':
        return
    content = f'**{after.mention} updated**\n{content}'

    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)

def match_role(role, list):
    for item in list:
        if item.id == role.id:
            return True
    return False

async def log_member_update(before: Member, after: Member):
    content = ''
    embed = discord.Embed(
        color=0xA40985,
    )
    before_avatar = before.avatar or before.default_avatar
    after_avatar = after.avatar or after.default_avatar
    if not before.nick == after.nick:
        content += f'\nNick: {before.nick} -> {after.nick}'
    if not before.roles == after.roles:
        for role_before in after.roles:
            exits = match_role(role_before, before.roles)
            if not exits:
                content += f'\nAdded role {role_before.mention}'
        for role_after in before.roles:
            exits = match_role(role_after, after.roles)
            if not exits:
                content += f'\nRemoved role {role_after.mention}'
    if before_avatar != after_avatar:
        before_avatar = before.avatar or before.default_avatar
        after_avatar = after.avatar or after.default_avatar
        content += f'\nAvatar updated.'
        embed.set_thumbnail(after_avatar)

    content = f'**Member updated {after.mention}**\n{content}'
    embed.description = content
    await send_log_message(embed=embed)

async def log_user_update(before, after):
    content = f'**User updated {after.mention}**\n'
    if before.avatar == after.avatar:
        return
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    embed.set_image(url=after.avatar)
    await send_log_message(embed=embed)

async def log_member_join(member):
    content = f'**{member.mention} joined**'
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)

async def log_member_leave(member):
    content = f'**{member.mention} left**'
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)

async def log_role_create(role):
    content = f'**{role.mention} created**\n {role.mention}'
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)

async def log_role_delete(role):
    content = f'**{role.mention} deleted**\n {role.name}'
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)

async def log_channel_creation(channel):
    content = f'**{channel.mention} created**'
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)

async def log_channel_deletion(channel):
    content = f'**{channel.name} ({channel.id}) deleted**'
    embed = discord.Embed(
        description=content,
        color=0xA40985,
    )
    await send_log_message(embed=embed)