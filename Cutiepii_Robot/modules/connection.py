"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import time
import re
import html
import contextlib
import Cutiepii_Robot.modules.sql.connection_sql as sql

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, Bot
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes, CallbackQueryHandler, CommandHandler
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, SUDO_USERS, DEV_USERS, OWNER_ID
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, AdminPerms
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message, typing_action



@typing_action
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@cutiepii_cmd(command="allowconnect")
async def allow_connections(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat
    args = context.args

    if chat.type != chat.PRIVATE:
        if len(args) >= 1:
            var = args[0].lower().strip()
            if var == "no":
                sql.set_allow_connect_to_chat(chat.id, False)
                await send_message(
                    update.effective_message,
                    "<b>Connection Settings</b>\nConnections to this chat have been disabled.",
                    parse_mode=ParseMode.HTML,
                )
            elif var == "yes":
                sql.set_allow_connect_to_chat(chat.id, True)
                await send_message(
                    update.effective_message,
                    "<b>Connection Settings</b>\nConnections to this chat have been enabled.",
                    parse_mode=ParseMode.HTML,
                )
            else:
                await send_message(
                    update.effective_message,
                    "<b>Invalid Command Usage</b>\nPlease specify <code>yes</code> or <code>no</code>.",
                    parse_mode=ParseMode.HTML,
                )
        else:
            get_settings = sql.allow_connect_to_chat(chat.id)
            if get_settings:
                await send_message(
                    update.effective_message,
                    "<b>Connection Settings</b>\nConnections to this group are currently <b>allowed</b> for members.",
                    parse_mode=ParseMode.HTML,
                )
            else:
                await send_message(
                    update.effective_message,
                    "<b>Connection Settings</b>\nConnections to this group are currently <b>not allowed</b> for members.",
                    parse_mode=ParseMode.HTML,
                )
    else:
        await send_message(
            update.effective_message,
            "<b>Group Only Command</b>\nThis command can only be used in groups.",
            parse_mode=ParseMode.HTML,
        )


@typing_action
@cutiepii_cmd(command="connection")
async def connection_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat
    user = update.effective_user

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)

    if conn:
        chat_obj = await dispatcher.bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        if update.effective_message.chat.type == "private":
            return
        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if conn:
        message = f"<b>Connection Status</b>\nYou are currently connected to <b>{html.escape(chat_name)}</b>."
    else:
        message = "<b>Connection Status</b>\nYou are currently not connected to any group."
    await send_message(update.effective_message, message, parse_mode=ParseMode.HTML)

@typing_action
@cutiepii_cmd(command="connect")
async def connect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics

    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if update.effective_chat.type == "private":
        if args and len(args) >= 1:
            try:
                connect_chat = int(args[0])
                getstatusadmin = await context.bot.get_chat_member(
                    connect_chat, update.effective_message.from_user.id
                )
            except ValueError:
                try:
                    connect_chat = str(args[0])
                    get_chat = await context.bot.get_chat(connect_chat)
                    connect_chat = get_chat.id
                    getstatusadmin = await context.bot.get_chat_member(
                        connect_chat, update.effective_message.from_user.id
                    )
                except BadRequest:
                    await send_message(update.effective_message, "<b>Error</b>\nInvalid Chat ID or username.", parse_mode=ParseMode.HTML)
                    return
            except BadRequest:
                await send_message(update.effective_message, "<b>Error</b>\nInvalid Chat ID or username.", parse_mode=ParseMode.HTML)
                return

            is_owner = (user.id == OWNER_ID)
            isadmin = getstatusadmin.status in ("administrator", "creator")
            if isadmin and not is_owner:
                # Require can_change_info permission unless creator
                if getstatusadmin.status != "creator" and not getstatusadmin.can_change_info:
                    isadmin = False
            ismember = getstatusadmin.status == "member"
            isallow = sql.allow_connect_to_chat(connect_chat)

            if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS) or is_owner:
                connection_status = sql.connect(
                    update.effective_message.from_user.id, connect_chat
                )
                if connection_status:
                    conn_id = await connected(context.bot, update, chat, user.id, need_admin=False)
                    conn_chat = await dispatcher.bot.get_chat(conn_id)
                    chat_name = conn_chat.title
                    await send_message(
                        update.effective_message,
                        f"<b>Connection Successful</b>\nConnected to <b>{html.escape(chat_name)}</b>.\nUse <code>/helpconnect</code> to check available commands.",
                        parse_mode=ParseMode.HTML,
                    )
                    sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
                else:
                    await send_message(update.effective_message, "<b>Connection Failed</b>\nUnable to establish a connection.", parse_mode=ParseMode.HTML)
            else:
                await send_message(
                    update.effective_message, "<b>Action Denied</b>\nConnection to this chat is not allowed.", parse_mode=ParseMode.HTML
                )
        else:
            gethistory = sql.get_history_conn(user.id)
            if gethistory:
                buttons = [
                    InlineKeyboardButton(
                        text="Close", callback_data="connect_close"
                    ),
                    InlineKeyboardButton(
                        text="Clear history", callback_data="connect_clear"
                    ),
                ]
            else:
                buttons = []
            conn = await connected(context.bot, update, chat, user.id, need_admin=False)
            if conn:
                connectedchat = await context.bot.get_chat(conn)
                text = f"You are currently connected to <b>{html.escape(connectedchat.title)}</b> (<code>{conn}</code>)"
                buttons.append(
                    InlineKeyboardButton(
                        text="Disconnect", callback_data="connect_disconnect"
                    )
                )
            else:
                text = "Please specify a chat ID or username to connect."
            if gethistory:
                text += "\n\n<b>Connection History:</b>\n"
                text += "<b>Information:</b>\n"
                text += "Sorted: Newest\n\n"
                buttons = [buttons]
                for x in sorted(gethistory.keys(), reverse=True):
                    htime = time.strftime("%d/%m/%Y", time.localtime(x))
                    text += f"<b>{html.escape(gethistory[x]['chat_name'])}</b>\nID: <code>{gethistory[x]['chat_id']}</code>\nDate: {htime}\n\n"
                    buttons.append(
                        [
                            InlineKeyboardButton(
                                text=gethistory[x]["chat_name"],
                                callback_data="connect({})".format(
                                    gethistory[x]["chat_id"]
                                ),
                            )
                        ]
                    )
                text += "Total: {} chats".format(
                    str(len(gethistory)) + " (max)"
                    if len(gethistory) == 5
                    else str(len(gethistory))
                )
                conn_hist = InlineKeyboardMarkup(buttons)
            elif buttons:
                conn_hist = InlineKeyboardMarkup([buttons])
            else:
                conn_hist = None
            await send_message(
                update.effective_message,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=conn_hist,
            )

    else:
        getstatusadmin = await context.bot.get_chat_member(
            chat.id, update.effective_message.from_user.id
        )
        is_owner = (user.id == OWNER_ID)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        if isadmin and not is_owner:
            # Require can_change_info permission unless creator
            if getstatusadmin.status != "creator" and not getstatusadmin.can_change_info:
                isadmin = False
        ismember = getstatusadmin.status == "member"
        isallow = sql.allow_connect_to_chat(chat.id)
        if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS) or is_owner:
            connection_status = sql.connect(
                update.effective_message.from_user.id, chat.id
            )
            if connection_status:
                chat_obj = await context.bot.get_chat(chat.id)
                chat_name = chat_obj.title
                await send_message(
                    update.effective_message,
                    f"<b>Connection Successful</b>\nConnected to <b>{html.escape(chat_name)}</b>.",
                    parse_mode=ParseMode.HTML,
                )
                try:
                    sql.add_history_conn(user.id, str(chat.id), chat_name)
                    await context.bot.send_message(
                        update.effective_message.from_user.id,
                        f"You are connected to <b>{html.escape(chat_name)}</b>.\nUse <code>/helpconnect</code> to check available commands.",
                        parse_mode=ParseMode.HTML,
                    )
                except BadRequest:
                    pass
                except Forbidden:
                    pass
            else:
                await send_message(update.effective_message, "<b>Connection Failed</b>\nUnable to establish a connection.", parse_mode=ParseMode.HTML)
        else:
            await send_message(
                update.effective_message, "<b>Action Denied</b>\nConnection to this chat is not allowed.", parse_mode=ParseMode.HTML
            )


@cutiepii_cmd(command="disconnect")
async def disconnect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.type == "private":
        disconnection_status = sql.disconnect(update.effective_message.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = await send_message(
                update.effective_message, "<b>Connection Status</b>\nDisconnected from chat.", parse_mode=ParseMode.HTML
            )
        else:
            await send_message(update.effective_message, "<b>Connection Status</b>\nYou are not connected.", parse_mode=ParseMode.HTML)
    else:
        await send_message(update.effective_message, "<b>Private Message Only Command</b>\nThis command is only available in private messages.", parse_mode=ParseMode.HTML)


async def reconnect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    message = update.effective_message

    if chat.type != "private":
        await send_message(message, "<b>Private Message Only Command</b>\nThis command is only available in private messages.", parse_mode=ParseMode.HTML)
        return

    gethistory = sql.get_history_conn(user.id)
    if not gethistory:
        await send_message(message, "<b>No History</b>\nYou do not have any connection history to reconnect to.", parse_mode=ParseMode.HTML)
        return

    newest_key = max(gethistory.keys())
    last_chat_id = int(gethistory[newest_key]["chat_id"])
    last_chat_name = gethistory[newest_key]["chat_name"]

    try:
        getstatusadmin = await context.bot.get_chat_member(last_chat_id, user.id)
    except BadRequest:
        await send_message(message, "<b>Error</b>\nCould not access the last connected chat. Please ensure the bot is still a member and you are in the chat.", parse_mode=ParseMode.HTML)
        return

    is_owner = (user.id == OWNER_ID)
    isadmin = getstatusadmin.status in ("administrator", "creator")
    if isadmin and not is_owner:
        if getstatusadmin.status != "creator" and not getstatusadmin.can_change_info:
            isadmin = False

    is_allow = sql.allow_connect_to_chat(last_chat_id)
    is_member = getstatusadmin.status == "member"

    if (isadmin) or (isallow and is_member) or (user.id in SUDO_USERS) or is_owner:
        connection_status = sql.connect(user.id, last_chat_id)
        if connection_status:
            await send_message(
                message,
                f"<b>Reconnected</b>\nSuccessfully reconnected to <b>{html.escape(last_chat_name)}</b>.",
                parse_mode=ParseMode.HTML
            )
        else:
            await send_message(message, "<b>Connection Failed</b>\nUnable to establish a connection.", parse_mode=ParseMode.HTML)
    else:
        await send_message(message, "<b>Action Denied</b>\nConnection to this chat is not allowed.", parse_mode=ParseMode.HTML)


async def connected(bot: Bot, update: Update, chat, user_id, need_admin=True):
    user = update.effective_user

    if chat.type == chat.PRIVATE and sql.get_connected_chat(user_id):

        conn_id = sql.get_connected_chat(user_id).chat_id
        getstatusadmin = await bot.get_chat_member(
            conn_id, update.effective_message.from_user.id
        )
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status == "member"
        isallow = sql.allow_connect_to_chat(conn_id)

        if (
            (isadmin)
            or (isallow and ismember)
            or (user.id in SUDO_USERS)
            or (user.id in DEV_USERS)
        ):
            if need_admin is not True:
                return conn_id
            if (
                getstatusadmin.status in ("administrator", "creator")
                or user_id in SUDO_USERS
                or user.id in DEV_USERS
            ):
                return conn_id
            else:
                await send_message(
                    update.effective_message,
                    "<b>Action Denied</b>\nYou must be an administrator in the connected group.",
                    parse_mode=ParseMode.HTML,
                )
        else:
            await send_message(
                update.effective_message,
                "<b>Disconnected</b>\nThe group changed connection permissions or you are no longer an administrator. Connection terminated.",
                parse_mode=ParseMode.HTML,
            )
            sql.disconnect(update.effective_message.from_user.id)
            return False
    else:
        return False


CONN_HELP = """
<b>Connection Options</b>

The following actions are available with connected groups:
- View and edit Notes
- View and edit Filters
- Get invite link of chat
- Set and control AntiFlood settings
- Set and control Blacklist settings
- Set Locks and Unlocks in chat
- Enable and Disable commands in chat
- Export and import chat backups
"""


@cutiepii_cmd(command="helpconnect")
async def help_connect_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):

    args = context.args

    if update.effective_message.chat.type == "private":
        await send_message(update.effective_message, "<b>Private Message Only</b>\nPlease use this command in a private message to get help.", parse_mode=ParseMode.HTML)
        return
    else:
        await send_message(update.effective_message, CONN_HELP, parse_mode=ParseMode.HTML)



@cutiepii_callback(pattern=r"connect")
async def connect_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    connect_match = re.match(r"connect\((.+?)\)", query.data)
    disconnect_match = query.data == "connect_disconnect"
    clear_match = query.data == "connect_clear"
    connect_close = query.data == "connect_close"

    if connect_match:
        target_chat = connect_match[1]
        getstatusadmin = await context.bot.get_chat_member(target_chat, query.from_user.id)
        isadmin = getstatusadmin.status in ("administrator", "creator")
        ismember = getstatusadmin.status == "member"
        isallow = sql.allow_connect_to_chat(target_chat)

        if (isadmin) or (isallow and ismember) or (user.id in SUDO_USERS):
            connection_status = sql.connect(query.from_user.id, target_chat)

            if connection_status:
                conn_id = await connected(context.bot, update, chat, user.id, need_admin=False)
                conn_chat = await dispatcher.bot.get_chat(conn_id)
                chat_name = conn_chat.title
                await query.message.edit_text(
                    f"<b>Connection Successful</b>\nConnected to <b>{html.escape(chat_name)}</b>.\nUse <code>/helpconnect</code> to check available commands.",
                    parse_mode=ParseMode.HTML,
                )
                sql.add_history_conn(user.id, str(conn_chat.id), chat_name)
            else:
                await query.message.edit_text("<b>Connection Failed</b>\nUnable to establish a connection.", parse_mode=ParseMode.HTML)
        else:
            await context.bot.answer_callback_query(
                query.id, "Connection to this chat is not allowed.", show_alert=True
            )
    elif disconnect_match:
        disconnection_status = sql.disconnect(query.from_user.id)
        if disconnection_status:
            sql.disconnected_chat = await query.message.edit_text("<b>Connection Status</b>\nDisconnected from chat.", parse_mode=ParseMode.HTML)
        else:
            await context.bot.answer_callback_query(
                query.id, "You are not connected.", show_alert=True
            )
    elif clear_match:
        sql.clear_history_conn(query.from_user.id)
        await query.message.edit_text("<b>History Cleared</b>\nConnection history has been cleared.", parse_mode=ParseMode.HTML)
    elif connect_close:
        await query.message.edit_text("<b>Closed</b>\nTo open again, type <code>/connect</code>", parse_mode=ParseMode.HTML)
    else:
        await connect_chat(update, context)




__help__ = True

__mod_name__ = "Connection"

__handlers__ = [
]
