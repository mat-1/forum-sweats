# Contributing

## Setting up the bot

### Environment variables

There's a few env variables you have to set if you want to run the bot locally, however the unit tests still work without them.

- `token` - The Discord bot token, obtained from the [developers page](https://discord.com/developers/applications)
- `keys` - Your Hypixel API key, this isn't used I think idk someone check pls
- `dburi` - The MongoDB URI, you can get a free one from [mongodb.com](https://mongodb.com)
- `forumemail` - Your Hypixel forums email, you shouldn't put your main account in case it gets leaked
- `forumpassword` - Your Hypixel forums password, you shouldn't put your main account in case it gets leaked
- `perspective_key` - Your [Perspective API](https://perspectiveapi.com/#/home) key, used for detecting toxic messages
- `dev` - true/false, whether this is the main bot

## Adding stuff

### Adding a new command

All the bot commands are seperate Python files, in [forum-sweats/bot/commands/](https://github.com/mat-1/forum-sweats/tree/master/bot/commands). The name of the file does not actually matter, but I recommend you make it the name of the command to make it easier to find.

#### Required variables

- `name` - The name of the command. (You can add alternative names using aliases)
- `run` - This is actually an asynchronous function, not a variable. The first argument for this function will be the discord.py Message object, and all other arguments are for parsing the command itself.

#### Optional variables

- `init` - Another asynchronous function like `run`, but with no arguments. It is executed when the bot starts up (on_ready)
- `aliases` - A list with other names for the command.
- `channels` - A list of strings of channel names (from config/channels.json) that define what channels the command should work in. `['bot-commands']` by default. Set to `None` to work in all channels
- `pad_none` - Usually extra arguments specified by the user will be ignored, only useful if a command is defined multiple times (such as !forum)
If the command has multiple complex uses, you should put them in different files with the same name. See [forum.py](https://github.com/mat-1/forum-sweats/blob/master/bot/commands/forum.py), [forum_user.py](https://github.com/mat-1/forum-sweats/blob/master/bot/commands/forum_user.py), and [forum_thread.py](https://github.com/mat-1/forum-sweats/blob/master/bot/commands/forum_thread.py) for an example. Additionally, you should have pad_none=True for these commands.

#### Arguments

The arguments that are used for running the command. The names of the arguments don't matter, but the types are listed below (can be set by doing `(message, argumentname: Member)`).
The first argument is always the `message` object.

Member and Time can be imported by doing `from ..betterbot import Member, Time`

- `Member` - Using a server member in a command. This will intelligently figure out who the user is, and even allows for putting part of the user's name or nickname, and it can include spaces. See mute.py for an example.
- `Time` - Using an amount of time, like 5 minutes, in a command. See [mute.py](https://github.com/mat-1/forum-sweats/blob/master/bot/commands/mute.py) for an exmaple.
- `str` - A string of unknown length, will intelligently change based on the arguments around it.
- `int` - Any full number

Omitting the type of argument will default to a string.
