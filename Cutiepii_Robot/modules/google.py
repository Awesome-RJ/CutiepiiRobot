import subprocess
from telegram import Update, Bot
from telegram.ext import run_async, Filters

from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

def google(bot: Bot, update: Update):
        query = update.effective_message.text.split(" ", 1)
        result_ = subprocess.run(['gsearch', str(query[1])], stdout=subprocess.PIPE)
        result = str(result_.stdout.decode())
        update.effective_message.reply_markdown('*Searching:*\n`' + str(query[1]) + '`\n\n*RESULTS:*\n' + result)

__help__ = """
 - /google: Google search
 """

__mod_name__ = "Google"

GOOGLE_HANDLER = DisableAbleCommandHandler("google", google)

dispatcher.add_handler(GOOGLE_HANDLER)
