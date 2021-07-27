import httpx
import requests

from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async

from Cutiepii_Robot import pgram, http, dispatcher
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

def paste(update: Update, context: CallbackContext):
    args = context.args
    message = update.effective_message

    if message.reply_to_message:
        pasting = message.reply_to_message.text    
    
    elif len(args) >= 1:
        pasting = message.text.split(None, 1)[1]

    else:
        message.reply_text("What am I supposed to do with this?")
        return
   
    TIMEOUT = 3
    key = (
        requests.post("https://nekobin.com/", data=pasting, timeout=TIMEOUT)
        .json()
        .get("result")
        .get("key")
    )

    url = f"https://nekobin.com/{key}"

    reply_text = f"Pasted to *Nekobin* : {url}"

    message.reply_text(
        reply_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True,
    )


def hastebin(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    msg = update.effective_message  
    
    if msg.reply_to_message:        
        mean = msg.reply_to_message.text
               
    elif len(args) >= 1:
        mean = msg.text.split(None, 1)[1]
   
    else:
    	msg.reply_text("reply to any message or just do /paste <what you want to paste>")  
    	return
                                                                              
    url = "https://hastebin.com/documents"
    key = (
        requests.post(url, data=mean.encode("UTF-8"))
        .json()       
        .get('key')
    )
    pasted = f"Pasted to HasteBin: https://hastebin.com/{key}"
    msg.reply_text(pasted, disable_web_page_preview=True)
    
    
    

NEKO_BIN_HANDLER = DisableAbleCommandHandler("npaste", paste, run_async=True)
HASTE_BIN_HANDLER = DisableAbleCommandHandler("paste", hastebin, run_async=True)

dispatcher.add_handler(NEKO_BIN_HANDLER)
dispatcher.add_handler(HASTE_BIN_HANDLER)

__command_list__ = ["npaste", "hpaste"]
__handlers__ = [HASTE_BIN_HANDLER]
