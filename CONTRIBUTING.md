## Adding a new command
All the bot commands are seperate Python files, in forum-sweats/bot/commands/. The name of the file does not actually matter, but I recommend you make it the name of the command to make it easier to find.
#### Required variables
- `name` - The name of the command. (You can add alternative names using aliseses)
- `run` - This is actually an asynchronous function, not a variable. The first argument for this function will be the discord.py Message object, and all other arguments are for parsing the command itself.
#### Optional variables
- `aliases` - A list with other names for the command.
- `bot_channel` - If the command will only run when used in the #bot-commands channel. If this is false, the command will work anywhere, but you can add further limits (such as !rock working in #bot-commands and gulag)
- `pad_none` - Usually extra arguments specified by the user will be ignored, only useful if a command is defined multiple times (such as !forum)
If the command has multiple complex uses, you should put them in different files with the same name. See forum.py, forum_user.py, and forum_thread.py for an example. Additionally, you should have pad_none=True for these commands.

#### Arguments
The arguments that are used for running the command. The names of the arguments don't matter, but the types are listed below (can be set by doing `(message, argumentname: Member)`).
The first argument is always the `message` object.
Member and Time can be imported by doing `from ..betterbot import Member, Time`
- `Member` - Using a server member in a command. This will intelligently figure out who the user is, and even allows for putting part of the user's name or nickname, and it can include spaces. See mute.py for an example.
- `Time` - Using an amount of time, like 5 minutes, in a command. See mute.py for an exmaple.
- `str` - A string of unknown length, will intelligently change based on the arguments around it.
- `int` - Any full number

Omitting the type of argument will default to a string.
