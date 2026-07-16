from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE

import Cutiepii_Robot.modules.sql.private_notes as sql
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin


@user_admin
@cutiepii_cmd(command="privatenotes")
async def privatenotes(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    msg = ""

    if message.chat.type == "private":
        msg = "This command is meant to use in group not in PM"

    elif len(args) == 0:
        setting = await getprivatenotes(chat.id)
        msg = f"Private notes value is *{setting}* in *{chat.title}*"

    elif len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0", "disable", "false"]:
            await setprivatenotes(chat.id, False)
            msg = f"Private notes has been disabled in *{chat.title}*"
        elif val in ["on", "yes", "1", "enable", "true"]:
            await setprivatenotes(chat.id, True)
            msg = f"Private notes has been enabled in *{chat.title}*"
        else: 
            msg = "Sorry, wrong value"

    await message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN
    )

async def setprivatenotes(chat_id, setting):
    sql.set_private_notes(chat_id, setting)
            

async def getprivatenotes(chat_id):
    setting = sql.get_private_notes(chat_id)
    return setting


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)




__mod_name__ = "Private Notes"

__help__ = True

