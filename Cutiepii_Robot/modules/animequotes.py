import html
import random
import time

from telegram import ParseMode, Update, ChatPermissions
from telegram.ext import CallbackContext, run_async
from telegram.error import BadRequest

import Cutiepii_Robot.modules.animequotes_strings as animequotes_strings
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.chat_status import (is_user_admin)
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user

def animequotes(update: Update, context: CallbackContext):
    message = update.effective_message
    name = message.reply_to_message.from_user.first_name if message.reply_to_message else message.from_user.first_name
    reply_photo = message.reply_to_message.reply_photo if message.reply_to_message else message.reply_photo
    reply_photo(
        random.choice(animequotes_strings.QUOTES_IMG))



ANIMEQUOTES_HANDLER = DisableAbleCommandHandler("animequotes", animequotes, run_async=True)

dispatcher.add_handler(ANIMEQUOTES_HANDLER)


__command_list__ = [

    "animequotes"

]

__handlers__ = [

    ANIMEQUOTES_HANDLER

]
