import random
from telegram.ext import run_async, Filters
from telegram import Message, Chat, Update, Bot, MessageEntity
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

SFW_STRINGS = (
   "What the fuck just happened?/What the fuck is going on here?",
   "(Respectfully), shut the fuck up!",
   "They may go fuck themselves",
   "I’m fucking with you",
   "Your software can choke on my fucking balls",
   "I’ll show you fucking vision",
   "fucking prick",
   "Oh, for fuck’s sake!",
   "Are you fucking serious right now?",
   "Let’s fucking do this!",
   "fuck off",
   "cool shit!/shit codebase /What a shit circus!/Oh, shit!",
   "beat the shit out of someone",
   "look like shit",
   "You’re fucking piece of shit!",
   "Why don’t you choke on my ball?",
   "cock-sucker",
   "pussy",
   "You saved my ass",
   "I was suck a dick to you",
   "You are working your ass off",
   "suck his dick",
   "dickhole",
   "Now, that’s just one episode full of curse words.",
   "son of a bitch or SOB",
   "backstabbing bitch",
   "Taking the piss",
)

@run_async
def abuse(bot: Bot, update: Update):
    bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send messages
    message = update.effective_message
    if message.reply_to_message:
      message.reply_to_message.reply_text(random.choice(SFW_STRINGS))
    else:
      message.reply_text(random.choice(SFW_STRINGS))

DARK_HANDLER = DisableAbleCommandHandler("abuse", abuse)

dispatcher.add_handler(DARK_HANDLER)
