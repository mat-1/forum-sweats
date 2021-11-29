# Forum Sweats

Discord bot for the [Forum Sweats Discord](https://discord.gg/xvjVjVB)

# [discord.gg/xvjVjVB](https://discord.gg/xvjVjVB)

Official website: https://forumsweats.matdoes.dev

# Self-hosting

## Adding the bot
1) Make an empty Discord server.
2) Make a new application in https://discord.com/developers/applications (name it Forum Sweats or something).
3) Go to the Bot tab and click Add Bot, and confirm.
4) Go to the OAuth2 tab, under scopes select "bot", and under bot permissions select "administrator".
5) Go to the url that shows up (should start with https://discord.com/api/oauth2/authorize?client_id=) and add the bot to your server.

## Installing & configs
6) Install Python 3.8+ from the Windows store (remove any existing Python installations).
7) Download the source from https://github.com/mat-1/forum-sweats/archive/master.zip and unzip it anywhere.
8) Install Git from https://git-scm.com/download/win
9) Install Poetry by running `pip install poetry` or running `(Invoke-WebRequest -Uri https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py -UseBasicParsing).Content | python -` in Powershell
10) Run `poetry install` to install the dependencies.
11) Enable Discord developer mode in settings -> advanced -> developer mode if it's not already enabled.
12) Right click your server in the sidebar and click "copy id".
13) In config/bot.json, replace 717904501692170260 with your own server id that you just copied.
14) In config/channels.json, replace the channel ids there with your own (you can right click -> copy id channels in your own server to get the ids).
15) In config/roles.json, replace the role ids with your own.
16) In the root directory with `main.py` and the `forumsweats` folder, create a file called ".env" (just .env, nothing before or after).
17) Go back to the Discord bot developer page, and in the Bot tab copy the token.
18) In the .env file put token=the token you just copied here.

## Setting up database
17) Go to https://mongodb.com.
18) Sign up to MongoDB Atlas.
19) In the "Let’s get your account set up" page, just click skip at the bottom.
20) In "Choose a path. Adjust anytime.", select the free "create a cluster" button.
21) Maybe change the location and stuff if you want, then at the bottom click Create Cluster.
22) Click the "Network Access" tab at the left.
23) Click the Add IP Address button.
24) Select the gray "Allow access from anywhere" button, then confirm.
25) Go back to the "clusters" tab at the left (you might have to wait for it to finish loading).
26) Click the gray "connect" button in the cluster.
27) Set the username as "admin", autogenerate a password, and save it somewhere, then click the green Create Database User button.
28) Click the green Choose a connection method button.
29) Select "connect your application".
30) Copy the long uri that shows up (should start with mongodb+srv://).
31) Paste it somewhere and replace \<password\> with the password you saved.
32) Replace \<dbname\> with discord.
33) Back in the .env file, put dburi=mongodb+srv://your mongodb uri here in a new line after the token one.

## Running the bot
33) In the terminal run `poetry run python main.py`, and cross your fingers.
