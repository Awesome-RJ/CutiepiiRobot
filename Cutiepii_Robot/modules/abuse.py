import html
import random
import time
from typing import List

from telegram import Bot, Update, ParseMode
from telegram.ext import run_async

import Cutiepii_Robot.modules.fun_strings as fun_strings
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.chat_status import is_user_admin
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user

@run_async
def abuse(update: Update, context: CallbackContext):
    msg = update.effective_message
    reply_text = (
        msg.reply_to_message.reply_text if msg.reply_to_message else msg.reply_text
    )
    reply_text(random.choice(fun_strings.ABUSE_STRINGS))

ABUSE_HANDLER = DisableAbleCommandHandler("abuse", abuse)

dispatcher.add_handler(ABUSE_HANDLER)

__handlers__ = [
    ABUSE_HANDLER
]
