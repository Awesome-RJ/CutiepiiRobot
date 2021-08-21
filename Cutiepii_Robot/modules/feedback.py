import html

from telegram import Update, Bot, ParseMode
from telegram.ext import run_async
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot import dispatcher
from requests import get
from telegram import InlineKeyboardMarkup, InlineKeyboardButton


def feedback(bot: Bot, update: Update):
  name = update.effective_message.from_user.first_name
  message = update.effective_message
  userid=message.from_user.id
  text = message.text[len('/feedback '):]
   

  feed_text = f"Cutiepii Robot *New* feedback from [{name}](tg://user?id={userid})\n\nfeed: {text}"
  

  bot.send_message(-1001151980503, feed_text, parse_mode=ParseMode.MARKDOWN)
 
  text = html.escape(text)
  reply_text=f"Thankyou for giving us your feedback."
  message.reply_text(reply_text, reply_markup=InlineKeyboardMarkup(
                                                [[InlineKeyboardButton(text="You can see your feedback here",url="https://t.me/Black_Knights_Union_Support")]]))
                                               
 

__help__ = """
 - /feedback : You can give us your feedbacks 
               can can see your feeds here.
"""

__mod_name__ = "FEEDBACK"
feed_handle = DisableAbleCommandHandler("feedback", feedback, run_async=True)
dispatcher.add_handler(feed_handle)
