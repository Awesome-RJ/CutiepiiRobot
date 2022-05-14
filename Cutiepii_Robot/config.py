"""
BSD 2-Clause License
Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>
All rights reserved.
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import json
import os


def get_user_list(config, key):
    with open(f'{os.getcwd()}/Cutiepii_Robot/{config}', 'r') as json_file:
        return json.load(json_file)[key]


# Create a new config.py or rename this to config.py file in same dir and import, then extend this class.
class Config:
    LOGGER = True
    # REQUIRED
    #Login to https://my.telegram.org and fill in these slots with the details given by it

    API_ID = 991649  # integer value, dont use ""
    API_HASH = "3c929d4c9c4ecb54d70bb425647fceaf"
    TOKEN = "1241223850:AAGCzDppaQCY82ctckpasCu2g2R-MU8CuXI"  #This var used to be API_KEY but it is now TOKEN, adjust accordingly.
    OWNER_ID = 2131857711  # If you dont know, run the bot and do /id in your private chat with it, also an integer
    OWNER_USERNAME = "Awesome_RJ_Offical"
    SUPPORT_CHAT = 'Black_Knights_Union_Support'  #Your own group for support, do not add the @
    JOIN_LOGGER = "-1001256555401"  #Prints any new group the bot is added to, prints just the name and ID.
    ERROR_LOGS = "-1001151980503"
    EVENT_LOGS = "-1001256555401"  #Prints information like gbans, sudo promotes, AI enabled disable states that may help in debugging and shit
    GBAN_LOGS = "-1001256555401"

    #RECOMMENDED
    SQLALCHEMY_DATABASE_URI = 'something://somewhat:user@hosturl:port/databasename'  # needed for any database modules
    LOAD = []
    NO_LOAD = ['rss', 'cleaner', 'connection', 'math']
    WEBHOOK = False
    INFOPIC = True
    URL = None
    SPAMWATCH_API = "w1I3qFo7KXTmT~6CfH~r2o7lAx9K7cAwFGqA4ElD6moFMQMVeUZp6odO~WRH~u_g"  # go to support.spamwat.ch to get key
    SPAMWATCH_SUPPORT_CHAT = "@SpamWatchSupport"

    #OPTIONAL
    ##List of id's -  (not usernames) for users which have sudo access to the bot.
    SUDO_USERS = get_user_list('elevated_users.json', 'sudos')
    ##List of id's - (not usernames) for developers who will have the same perms as the owner
    DEV_USERS = get_user_list('elevated_users.json', 'devs')
    ##List of id's (not usernames) for users which are allowed to gban, but can also be banned.
    SUPPORT_USERS = get_user_list('elevated_users.json', 'supports')
    #List of id's (not usernames) for users which WONT be banned/kicked by the bot.
    TIGER_USERS = get_user_list('elevated_users.json', 'tigers')
    WHITELIST_USERS = get_user_list('elevated_users.json', 'whitelists')
    DONATION_LINK = None  # EG, paypal
    CERT_PATH = None
    PORT = 5000
    DEL_CMDS = True  #Delete commands that users dont have access to, like delete /ban if a non admin uses it.
    STRICT_GBAN = True
    WORKERS = 8  # Number of subthreads to use. Set as number of threads your processor uses
    BAN_STICKER = "CAACAgQAAx0CU_rCTAABAczQXyBOv1TsVK4EfwnkCUT1H0GCkPQAAtwAAwEgTQaYsMtAltpEwhoE"  # banhammer marie sticker id, the bot will send this sticker before banning or kicking a user in chat.
    ALLOW_EXCL = True  # Allow ! commands as well as / (Leave this to true so that blacklist can work)
    CASH_API_KEY = '-UN7567OXRP0EP4WD'  # Get your API key from https://www.alphavantage.co/support/#api-key
    TIME_API_KEY = '-HW6LQCYX43HS'  # Get your API key from https://timezonedb.com/api
    WALL_API = '2795f44dad7746122baaa83d01db8541'  #For wallpapers, get one from https://wall.alphacoders.com/api.php
    BL_CHATS = []  # List of groups that you want blacklisted.
    SPAMMERS = None
    YOUTUBE_API_KEY = "AIzaSyAPu1vLJF0_XKcwWnjhV4Iz6OJJfK_qaOs"
    STRING_SESSION = "1BVtsOMcBu1ShuqW9nmrMj9fxGKvkNbo19BIF2zoKnvTuyaJW8aZS_sv2q3YyUo4R57WDCrork5dYyMO13khqsOlmz6TFzWz0K9H89HtJnJNbMuoCG7zi6ZbPvisdQYqi-4R7CT0Y_Wg-ElGJHJaOZ0CRgvEKQeD1kzX8zYi1ruly9Dacn1WLeM-Vv9ir8p53aJ0G8g0a23LSa6qWKknm8A0awX7zprdkaAFJJuCFX2CgE0PM8PsLvRTNq-4idLN3Kg19r5oi2sKB2R0btGy9TYf5OY4ByRnWWypl8t3tfzTEHSpVqplv3Vnds-cMVdVwuGD2gJ_IbH0VOFci8cO-wBfpq8Gnz1c="1BVtsOMcBu1ShuqW9nmrMj9fxGKvkNbo19BIF2zoKnvTuyaJW8aZS_sv2q3YyUo4R57WDCrork5dYyMO13khqsOlmz6TFzWz0K9H89HtJnJNbMuoCG7zi6ZbPvisdQYqi-4R7CT0Y_Wg-ElGJHJaOZ0CRgvEKQeD1kzX8zYi1ruly9Dacn1WLeM-Vv9ir8p53aJ0G8g0a23LSa6qWKknm8A0awX7zprdkaAFJJuCFX2CgE0PM8PsLvRTNq-4idLN3Kg19r5oi2sKB2R0btGy9TYf5OY4ByRnWWypl8t3tfzTEHSpVqplv3Vnds-cMVdVwuGD2gJ_IbH0VOFci8cO-wBfpq8Gnz1c="
    REM_BG_API_KEY = "tC5i7cG4MF7QFwNmHFrk7ATA"
    REDIS_URL = "redis://majid-bez:Majid100$@redis-18817.c114.us-east-1-4.ec2.cloud.redislabs.com:18817/Majid"
    OPENWEATHERMAP_ID = "7aa571ada613e68f618409baccade8a0"
    MONGO_DB_URL = "mongodb+srv://Cutiepii_Robot:Rajkumar27$@cluster0.peb0l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"
    GENIUS_API_TOKEN = "2C5v3NkSz9t_gE4g6bbeYyK7fh7Ze1yNdCUWHi6kHc2J_CZam64MnJ2ozb6gxlsx"
    BOT_ID = "1241223850"
    APP_ID = 18529561
    APP_HASH = "8a3a5640f9280e1aae4a8706c1443d38"
    TEMP_DOWNLOAD_DIRECTORY = "./" # Don't Change
    ARQ_API_URL = "https://thearq.tech"
    GOOGLE_CHROME_BIN = "/usr/bin/google-chrome"
    CHROME_DRIVER = "/usr/bin/chromedriver"
    ALLOW_CHATS = True
    BOT_API_URL = "https://api.telegram.org/bot"
    BOT_API_FILE_URL = "https://api.telegram.org/file/bot"
    MONGO_DB = "Cutiepii"
    CUTIEPII_PHOTO = "https://telegra.ph/file/ec3a62516c541f858b5e0.jpg"
    GROUP_START_IMG = "https://c.tenor.com/OuuIlFh2_vYAAAAd/akame-edit.gif"
    HELP_IMG = "https://telegra.ph/file/e8f3310b943b8b8699dcd.jpg"
    REMINDER_LIMIT = int(20)
    
    DATABASE_URL = "postgresql://cutiepii:Rajkumar27$@cutiepii.postgres.database.azure.com/postgres"
    DB_URL = "postgresql://cutiepii:Rajkumar27$@cutiepii.postgres.database.azure.com/postgres"
    TG_API = "https://api.telegram.org/bot"
    TG_FILE_API = "https://api.telegram.org/file/bot"
    DATABASE_NAME = "postgres"
    BACKUP_PASS = "Rajkumar27$"
   

class Production(Config):
    LOGGER = True


class Development(Config):
    LOGGER = True
