import random
from telegram.ext import run_async, Filters
from telegram import Message, Chat, Update, Bot, MessageEntity
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

SFW_STRINGS = (
    "പോടാ പട്ടി",
    "ഡാ പന്നി ",
    "പുന്നാര മോനെ",
    "പോടാ മാക്രി",
    "പോടാ നാറി",
    "വാടാ ... പട്ടീ",
    "പോയി ചാവടാ",
    "നീ പോടാ കാട്ടുകോഴി",
    "പോയി ചത്തൂടെ നിനക്ക്",
    "കോപ്പേ വല്യ ബഹളം വേണ്ട",
    "വല്യ മലരനാണല്ലോടാ നീ",
    "മണ്ണുണ്ണി",
    "ഡാ പന്നക്കിളവ",
    " നിന്റെ കുഞ്ഞമ്മേടെ നായർ",
    "നിന്റെ അപ്പൂപ്പനോട്‌ പോയി പറ",
    "പോ മലരേ"
  )

@run_async
def dark(bot: Bot, update: Update):
    bot.sendChatAction(update.effective_chat.id, "typing") # Bot typing before send messages
    message = update.effective_message
    if message.reply_to_message:
      message.reply_to_message.reply_text(random.choice(SFW_STRINGS))
    else:
      message.reply_text(random.choice(SFW_STRINGS))

__help__ = """
- /dark  🤬.
"""

__mod_name__ = "Abuse"

DARK_HANDLER = DisableAbleCommandHandler("dark", dark)

dispatcher.add_handler(DARK_HANDLER)
