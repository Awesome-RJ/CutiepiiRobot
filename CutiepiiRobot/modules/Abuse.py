import random
from telegram.ext import run_async, Filters
from telegram import Message, Chat, Update, Bot, MessageEntity
from CutiepiiRobot import dispatcher
from CutiepiiRobot.modules.disable import DisableAbleCommandHandler

ABUSE_STRINGS = (
    "Fuck off",
    "Stfu go fuck yourself",
    "Oh, for fuck’s sake!",
    "Let’s fucking do this!",
    "I’m fucking with you",
    "motherfuck",
    "You’re fucking piece of shit!",
    "look like shit",
    "cool shit!",
    "Ur mum gey",
    "Ur dad lesbo",
    "Bsdk",
    "Nigga",
    "Ur granny tranny",
    "you noob",
    "Relax your Rear,ders nothing to fear,The Rape train is finally here",
    "Stfu bc",
    "Stfu and Gtfo U nub",
    "GTFO bsdk",
    "CUnt",
    " Gay is here",
    "Ur dad gey bc ",
    "gando",
"sakura",
"son of a bitch",
"fuck you bitch",
"wtf",
"sala",
"dick",
"whore",
"lesbians",
"son of a bitch",
"butt hole",
"bhosdike",
"lund",
"oppai",
"bastard",
"bhenchodh",
"bhen ke lode",
"anal",
  )

@run_async
def abuse(bot: Bot, update: Update):
    bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send messages
    message = update.effective_message
    if message.reply_to_message:
      message.reply_to_message.reply_text(random.choice(ABUSE_STRINGS))
    else:
      message.reply_text(random.choice(ABUSE_STRINGS))

__help__ = """
 • /abuse : Abuse someone in Hindi/English.
"""

__mod_name__ = "Abuse"

ABUSE_HANDLER = DisableAbleCommandHandler(("abuse", abuse)

dispatcher.add_handler(ABUSE_HANDLER)
