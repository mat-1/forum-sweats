import asyncio
import inspect
from typing import Any, Callable, Optional, TypeVar, Union
import discord

from forumsweats import discordbot


def check_content(content) -> str:
        return content

async def check_channel(content: str) -> discord.TextChannel:
    if not (content.startswith('<#') and content.endswith('>')):
        return
    channel_id = content[2:-1]
    try: channel_id = int(channel_id)
    except: return None
    channel = discordbot.client.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return
    return channel

async def prompt_input(client: discord.Client, user: discord.Member, channel: discord.abc.Messageable, prompt_message: str, invalid_message: str, check: Callable[[Any], Any], **kwargs) -> Any:
    message = None
    try:
        user_response = None
        preview = kwargs.get('preview')
        
        if preview is not None:
            prompt_message += '\n**Preview:**'
            message = await channel.send(prompt_message, embed=preview)
        else:
            message = await channel.send(prompt_message)

        

        while user_response is None:
            m: discord.Message = await client.wait_for(
                'message',
                check=lambda m:
                    m.author.id == user.id
                    and channel.id == channel.id, # type: ignore (the typings on discord.py are wrong)
                timeout=60
            )

            if m.content.lower() == 'cancel':
                return await m.add_reaction('👍')
            
            user_response = None

            if inspect.iscoroutinefunction(check):
                user_response = await check(m.content)
            else:
                user_response = check(m.content)

            if user_response is None:
                await channel.send(invalid_message + ' (Type "cancel" to cancel the auction creation)')
        return user_response
    except asyncio.TimeoutError:
        if message is not None:
            await message.edit(content='Timed out.', embed=None)
        return