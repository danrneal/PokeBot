# PokeBot

[![python](https://img.shields.io/badge/Python-3.6-blue.svg)]() [![license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://img.shields.io/gitlab/license/alphapokes/pokebot) [![pipeline status](https://gitlab.com/alphapokes/PokeBot/badges/master/pipeline.svg)](https://gitlab.com/alphapokes/PokeBot/commits/master) [![Discord](https://img.shields.io/discord/314040044052545538.svg)](https://discordapp.com/channels/314040044052545538/314040595456983040) [![donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://paypal.me/dneal12)

A pokemon notification bot.

This discord bot will allow users to subscribe to notifcations to be sent to them as a DM.

Requirements:

1. Python3
2. At least one discord bot user.  Here is a link on how to set it up: https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token
3. At least one google maps api key with geocoding and static maps enabled. [optional]  Here is another link on how to set that up: https://github.com/kvangent/PokeAlarm/wiki/Google-Maps-API-Key

How to install (for Windows):

1. `git clone git@gitlab.com:alphapokes/PokeBot.git`
2. `cd ./CounterSniper`
3. `python3 -m pip install -r requirements.txt`

![](https://i.imgur.com/1i3FSqe.png)

How to set up (always use Notepad++ and never notepad!):

1. Rename `config.ini.example` to `config.ini` in the config folder.
2. Set all required variables in config file.
3. Create all webhook alarms files in `/alarms` using the template `alarms.json.example` and name them all in the format `alarms_*.json`
4. Create all webhook alarms files in `/filters` using the template `filters.json.example` and name them all in the format `filterss_*.json`
5. Create all webhook alarms files in `/geofences` using the template `geofence.txt.example` and name them all in the format `geofence_*.json`
6. Create DM alarms file in `/user_dicts` using the template `user_alarms.json.example` and name it `user_alarms.json`

How to run:

1. `python3 start_pokebot.py`
2. Type `!commands` in your commands channel if you need a list of commands.

**Credit:**

Thanks to Deadly for [PokeAlarm](https://github.com/PokeAlarm/PokeAlarm) which provided a framework for a lot of the code.