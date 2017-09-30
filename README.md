# PokeBot

![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg) ![License](https://img.shields.io/github/license/tallypokemap/PokeBot.svg) [![Build Status](https://travis-ci.org/tallypokemap/PokeBot.svg?branch=master)](https://travis-ci.org/tallypokemap/PokeBot)

A pokemon notification bot.

This discord bot will allow users to subscribe to PokeAlarm notifcations to be sent to them as a DM.

Requirements:

1. Python3
2. A working implementation of PokeAlarm
3. At least one discord bot user.  Here is a link on how to set it up: https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token
4. At least one google maps api key with geocoding and static maps enabled. [optional]  Here is another link on how to set that up: https://github.com/kvangent/PokeAlarm/wiki/Google-Maps-API-Key

How to install (for Windows):

1. `git clone https://github.com/tallypokemap/PokeBot.git`
2. `cd ./PokeBot`
3. `python3 -m pip install -r requirements.txt`

How to set up (always use Notepad++ and never notepad!):

* PokeAlarm's title line should be `"<pkmn> <iv_0>% ...`
* Set all variables in the config file.
* Required variables are token_list, client_id_list, and feed_channel.
* If you need more than one bot account, you can put them in a list.  You can do the same with google map api keys.

How to run:

1. `python3 start_pokebot.py`
