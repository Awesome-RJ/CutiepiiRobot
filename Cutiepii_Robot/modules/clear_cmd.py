import Cutiepii_Robot.modules.sql.clear_cmd_sql as sql

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility

from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)

@cutiepii_cmd(command='clearcmd')
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def clearcmd(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    msg = ""

    commands = [
    "afk",
    "cash",
    "checkfw",
    "covid",
    "filters",
    "fun",
    "getfw",
    "github",
    "imdb",
    "info",
    "lyrics",
    "magisk",
    "miui",
    "notes",    
    "orangefox",
    "phh",
    "ping",
    "purge",
    "reverse",
    "speedtest",
    "time",
    "tr",
    "tts",
    "twrp",
    "ud",
    "wall",
    "weather",
    "welcome",
    "wiki",
    "youtube",
    "zombies",
    ]

    if len(args) == 0:
        commands = sql.get_allclearcmd(chat.id)
        if commands:
            msg += "*Command - Time*\n"
            for cmd in commands:
                msg += f"`{cmd.cmd} - {cmd.time} secs`\n"  
        else:
            msg = f"No deletion time has been set for any command in *{chat.title}*"

    elif len(args) == 1:
        cmd = args[0].lower()
        if cmd == "list":
            msg = "The commands available are:\n"
            for cmd in commands:
                msg += f"- `{cmd}`\n"
        elif cmd == "restore":
            delcmd = sql.del_allclearcmd(chat.id)
            msg = "Removed all commands from list"
        else:
            cmd = sql.get_clearcmd(chat.id, cmd)
            if cmd:
                msg = f"`{cmd.cmd}` output is set to be deleted after *{cmd.time}* seconds in *{chat.title}*"
            else:
                if cmd not in commands:
                    msg = "Invalid command. Check module help for more details"
                else:
                    msg = f"This command output hasn't been set to be deleted in *{chat.title}*"

    elif len(args) == 2:
        cmd = args[0].lower()
        time = args[1]
        if cmd in commands:
            if time == "restore":
                sql.del_clearcmd(chat.id, cmd)
                msg = f"Removed `{cmd}` from list"
            else:
                time = parse_to_seconds(time)
                if not time:
                    msg = "Time must be in seconds or minutes"
                elif (5 <= time <= 300):
                    sql.set_clearcmd(chat.id, cmd, time)
                    msg = f"`{cmd}` output will be deleted after *{time}* seconds in *{chat.title}*"
                else:
                    msg = "Time must be between 5 and 300 seconds"
        else:
            msg = "Specify a valid command. Use `/clearcmd list` to see available commands"
                
    else:
        msg = "I don't understand what are you trying to do. Check module help for more details"

    message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN
    )


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

__mod_name__ = "Clear Commands"

__help__ = True