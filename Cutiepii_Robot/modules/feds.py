"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

import ast
import csv
import json
import os
import re
import time
import uuid
import Cutiepii_Robot.modules.sql.feds_sql as sql

from io import BytesIO

from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_is_admin
from Cutiepii_Robot import (
    GBAN_LOGS,
    LOGGER,
    SUPPORT_CHAT,
    OWNER_ID,
    DEV_USERS,
    SUDO_USERS,
    WHITELIST_USERS,
    CUTIEPII_PTB,
)
from Cutiepii_Robot.modules.helper_funcs.alternate import (
    send_message,
    typing_action,
    send_action,
)
from Cutiepii_Robot.modules.helper_funcs.extraction import (
    extract_unt_fedban,
    extract_user,
    extract_user_fban,
)
from Cutiepii_Robot.modules.helper_funcs.string_handling import markdown_parser
from telegram import (
    Update,
    MessageEntity,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest, TelegramError, Forbidden
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,

)
from telegram.helpers import mention_html, mention_markdown

FBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Have no rights to send a message",
}

UNFBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Have no rights to send a message",
}


async def new_fed(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message
    if chat.type != "private":
        await update.effective_message.reply_text(
            "You can your federation in my PM, not in a group."
        )
        return
    fednam = message.text.split(None, 1)
    if len(fednam) >= 2:
        fednam = fednam[1]
        fed_id = str(uuid.uuid4())
        fed_name = fednam
        LOGGER.info(fed_id)

        # Currently only for creator
        # if fednam == 'Team Nusantara Disciplinary Circle':
        # fed_id = "TeamNusantaraDevs"

        x = sql.new_fed(user.id, fed_name, fed_id)
        if not x:
            await update.effective_message.reply_text(
                f"Can't federate! Report in @{SUPPORT_CHAT} if the problem persists."
            )
            return

        await update.effective_message.reply_text(
            "*You have successfully created a new federation!*"
            "\nName: `{}`"
            "\nID: `{}`"
            "\n\nUse the command below to join the federation:"
            "\n`/joinfed {}`".format(fed_name, fed_id, fed_id),
            parse_mode=ParseMode.MARKDOWN,
        )
        try:
            await context.bot.send_message(
                GBAN_LOGS,
                f"Federation <b>{fed_name}</b> has been created with ID: <pre>{fed_id}</pre>",
                parse_mode=ParseMode.HTML,
            )

        except Exception:
            LOGGER.warning("Cannot send a message to GBAN_LOGS")
    else:
        await update.effective_message.reply_text(
            "Please write down the name of the federation"
        )


async def del_fed(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    if chat.type != "private":
        await update.effective_message.reply_text(
            "You can delete your federation in my PM, not in the group."
        )
        return
    if args:
        is_fed_id = args[0]
        getinfo = sql.get_fed_info(is_fed_id)
        if getinfo is False:
            await update.effective_message.reply_text("This federation is not found")
            return
        if int(getinfo["owner"]) == int(user.id) or int(user.id) == OWNER_ID:
            fed_id = is_fed_id
        else:
            await update.effective_message.reply_text("Only federation owners can do this!")
            return
    else:
        await update.effective_message.reply_text("What should I delete?")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only federation owners can do this!")
        return

    await update.effective_message.reply_text(
        f"""Are you sure you want to delete your federation? This action cannot be canceled, you will lose your entire ban list, and '{getinfo["fname"]}' will be permanently lost.""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⚠️ Remove Federation ⚠️",
                        callback_data=f"rmfed_{fed_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Cancel", callback_data="rmfed_cancel"
                    )
                ],
            ]
        ),
    )


async def rename_fed(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(None, 2)

    if len(args) < 3:
        return await msg.reply_text("usage: /renamefed <fed_id> <newname>")

    fed_id, newname = args[1], args[2]
    verify_fed = sql.get_fed_info(fed_id)

    if not verify_fed:
        return await msg.reply_text("This fed not exist in my database!")

    if is_user_fed_owner(fed_id, user.id):
        sql.rename_fed(fed_id, user.id, newname)
        await msg.reply_text(f"Successfully renamed your fed name to {newname}!")
    else:
        await msg.reply_text("Only federation owner can do this!")

async def fed_chat(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    fed_id = sql.get_fed_id(chat.id)

    user_id = update.effective_message.from_user.id
    if not user_is_admin(update, user_id):
        await update.effective_message.reply_text(
            "You must be an admin to execute this command"
        )
        return

    if not fed_id:
        await update.effective_message.reply_text("This group is not in any federation!")
        return

    info = sql.get_fed_info(fed_id)
    text = (
        "This chat is part of the following federation:"
        + "\n{} (ID: <code>{}</code>)".format(info["fname"], fed_id)
    )

    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def join_fed(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM!",
        )
        return

    message = update.effective_message
    administrators = chat.get_administrators()
    fed_id = sql.get_fed_id(chat.id)
    args = context.args

    if user.id not in DEV_USERS:
        for admin in administrators:
            status = admin.status
            if status == "creator" and str(admin.user.id) != str(user.id):
                await update.effective_message.reply_text(
                    "Only group creators can use this command!"
                )
                return
    if fed_id:
        await message.reply_text("You cannot join two federations from one chat")
        return

    if len(args) >= 1:
        getfed = sql.search_fed_by_id(args[0])
        if getfed is False:
            await message.reply_text("Please enter a valid federation ID")
            return

        x = sql.chat_join_fed(args[0], chat.title, chat.id)
        if not x:
            await message.reply_text("Failed to join federation!")
            return

        if get_fedlog := sql.get_fed_log(args[0]):
            if ast.literal_eval(get_fedlog):
                await context.bot.send_message(
                    get_fedlog,
                    f'Chat *{chat.title}* has joined the federation *{getfed["fname"]}*',
                    parse_mode="markdown",
                )


        await message.reply_text(
            f'This chat has joined the federation: {getfed["fname"]}!'
        )


async def leave_fed(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        send_message(
            msg,
            "This command is specific to the group, not to our PM!",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    fed_info = sql.get_fed_info(fed_id)

    # administrators = chat.get_administrators().status
    getuser = bot.get_chat_member(chat.id, user.id).status
    if getuser in "creator" or user.id in SUDO_USERS:
        if sql.chat_leave_fed(chat.id) is True:
            get_fedlog = sql.get_fed_log(fed_id)
            if get_fedlog and ast.literal_eval(get_fedlog):
                await bot.send_message(
                    get_fedlog,
                    f'Chat *{chat.title}* has left the federation *{fed_info["fname"]}*',
                    parse_mode=ParseMode.MARKDOWN,
                )

            send_message(msg, f'This group has left the federation {fed_info["fname"]}!')
        else:
            await update.effective_message.reply_text(
                 "How can you leave a federation that you never joined?!",
             )
    else:
        await update.effective_message.reply_text("Only group creators can use this command!")


async def user_join_fed(update, context):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if is_user_fed_owner(fed_id, user.id) or user.id is OWNER_ID:
        user_id = extract_user(msg, args)
        if user_id:
            user = await context.bot.get_chat(user_id)
        elif not msg.reply_to_message and not args:
            user = msg.from_user
        elif not msg.reply_to_message and (
            not args
            or (
                len(args) >= 1
                and not args[0].startswith("@")
                and not args[0].isdigit()
                and not msg.parse_entities([MessageEntity.TEXT_MENTION])
            )
        ):
            await msg.reply_text("I cannot extract user from this message")
            return
        else:
            LOGGER.warning("error")
        getuser = sql.search_user_in_fed(fed_id, user_id)
        fed_id = sql.get_fed_id(chat.id)
        info = sql.get_fed_info(fed_id)
        get_owner = ast.literal_eval(info["fusers"])["owner"]
        get_owner = await context.bot.get_chat(get_owner).id
        if user_id == get_owner:
            await update.effective_message.reply_text(
                "You do know that the user is the federation owner, right? RIGHT?"
            )
            return
        if getuser:
            await update.effective_message.reply_text(
                "I cannot promote users who are already federation admins! But, I can remove them if you want!"
            )
            return
        if user_id == context.bot.id:
            await update.effective_message.reply_text(
                "I already am a federation admin in all federations!"
            )
            return
        if res := sql.user_join_fed(fed_id, user_id):
            await update.effective_message.reply_text("Successfully Promoted!")
        else:
            await update.effective_message.reply_text("Failed to promote!")
    else:
        await update.effective_message.reply_text("Only federation owners can do this!")


async def user_demote_fed(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if is_user_fed_owner(fed_id, user.id) or user.id is OWNER_ID:
        msg = update.effective_message  # type: Optional[Message]
        user_id = extract_user(msg, args)
        if user_id:
            user = await context.bot.get_chat(user_id)

        elif not msg.reply_to_message and not args:
            user = msg.from_user

        elif not msg.reply_to_message and (
            not args
            or (
                len(args) >= 1
                and not args[0].startswith("@")
                and not args[0].isdigit()
                and not msg.parse_entities([MessageEntity.TEXT_MENTION])
            )
        ):
            await msg.reply_text("I cannot extract user from this message")
            return
        else:
            LOGGER.warning("error")

        if user_id == context.bot.id:
            await update.effective_message.reply_text(
                "The thing you are trying to demote me from will fail to work without me! Just saying."
            )
            return

        if sql.search_user_in_fed(fed_id, user_id) is False:
            await update.effective_message.reply_text(
                "I cannot demote people who are not federation admins!"
            )
            return

        res = sql.user_demote_fed(fed_id, user_id)
        if res is True:
            await update.effective_message.reply_text("Get out of here!")
        else:
            await update.effective_message.reply_text("Demotion failed!")
    else:
        await update.effective_message.reply_text("Only federation owners can do this!")
        return


async def fed_info(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    if args := context.args:
        fed_id = args[0]
    else:
        fed_id = sql.get_fed_id(chat.id)
        if not fed_id:
            send_message(
                update.effective_message,
                "This group is not in any federation!",
            )
            return
    info = sql.get_fed_info(fed_id)
    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only a federation admin can do this!")
        return

    owner = await context.bot.get_chat(info["owner"])
    try:
        owner_name = f"{owner.first_name} {owner.last_name}"
    except:
        owner_name = owner.first_name
    FEDADMIN = sql.all_fed_users(fed_id)
    FEDADMIN.append(int(owner.id))
    TotalAdminFed = len(FEDADMIN)

    info = sql.get_fed_info(fed_id)

    text = (
        "<b>ℹ️ Federation Information:</b>"
        + "\nFedID: <code>{}</code>".format(fed_id)
    )

    text += "\nName: {}".format(info["fname"])
    text += "\nCreator: {}".format(mention_html(owner.id, owner_name))
    text += "\nAll Admins: <code>{}</code>".format(TotalAdminFed)
    getfban = sql.get_all_fban_users(fed_id)
    text += "\nTotal banned users: <code>{}</code>".format(len(getfban))
    getfchat = sql.all_fed_chats(fed_id)
    text += "\nNumber of groups in this federation: <code>{}</code>".format(
        len(getfchat)
    )

    await update.effective_message.reply_text(
    text,
    parse_mode=ParseMode.HTML
    )


async def fed_admin(update, context):

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        await update.effective_message.reply_text("This group is not in any federation!")
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only federation admins can do this!")
        return

    info = sql.get_fed_info(fed_id)

    text = "<b>Federation Admin {}:</b>\n\n".format(info["fname"]) + "👑 Owner:\n"
    owner = await context.bot.get_chat(info["owner"])
    try:
        owner_name = f"{owner.first_name} {owner.last_name}"
    except BaseException:
        owner_name = owner.first_name or 'Deleted'
    text += " ➛ {}\n".format(mention_html(owner.id, owner_name))

    members = sql.all_fed_members(fed_id)
    if len(members) == 0:
        text += "\n🔱 There is no admin in this federation"
    else:
        text += "\n🔱 Admin:\n"
        for x in members:
            try:
                user = await bot.get_chat(x)
            except BadRequest as excp:
                pass
            name = user.first_name or 'Deleted'
            text += " ➛ {}\n".format(mention_html(user.id, user.first_name))

    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def fed_ban(update, context):  # sourcery no-metrics

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        await update.effective_message.reply_text(
            "This group is not a part of any federation!"
        )
        return

    info = sql.get_fed_info(fed_id)
    getfednotif = sql.user_feds_report(info["owner"])

    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only federation admins can do this!")
        return

    message = update.effective_message

    user_id, reason = extract_unt_fedban(message, args)

    fban, fbanreason, fbantime = sql.get_fban_user(fed_id, user_id)

    if not user_id:
        await message.reply_text("You don't seem to be referring to a user")
        return

    if user_id == context.bot.id:
        await message.reply_text(
            "What is funnier than kicking the group creator? Self sacrifice."
        )
        return

    if is_user_fed_owner(fed_id, user_id) is True:
        await message.reply_text("Why did you try the federation fban?")
        return

    if is_user_fed_admin(fed_id, user_id) is True:
        await message.reply_text("He is a federation admin, I can't fban him.")
        return

    if user_id == OWNER_ID:
        await message.reply_text("That's a very STUPID idea!")
        return

    if int(user_id) in SUDO_USERS:
        await message.reply_text("I will not ban a Royal Nation")
        return

    if int(user_id) in WHITELIST_USERS:
        await message.reply_text("This person can't be fbanned!")
        return

    if int(user_id) in (777000, 1087968824):
        await message.reply_text("I'm not fbanning Telegram bots.")
        return

    try:
        user_chat = await context.bot.get_chat(user_id)
        isvalid = True
        fban_user_id = user_chat.id
        fban_user_name = user_chat.first_name
        fban_user_lname = user_chat.last_name
        fban_user_uname = user_chat.username
    except BadRequest as excp:
        if not str(user_id).isdigit():
            send_message(update.effective_message, excp.message)
            return
        elif not len(str(user_id)) == 9:
            send_message(update.effective_message, "That's so not a user!")
            return
        isvalid = False
        fban_user_id = int(user_id)
        fban_user_name = "user({})".format(user_id)
        fban_user_lname = None
        fban_user_uname = None

    if isvalid and user_chat.type != "private":
        send_message(update.effective_message, "That's so not a user!")
        return

    if isvalid:
        user_target = mention_html(fban_user_id, fban_user_name)
    else:
        user_target = fban_user_name

    if fban:
        fed_name = info["fname"]
        if reason == "":
            reason = "No reason given."

        temp = sql.un_fban_user(fed_id, fban_user_id)
        if not temp:
            await message.reply_text("Failed to update the reason for fedban!")
            return
        x = sql.fban_user(
            fed_id,
            fban_user_id,
            fban_user_name,
            fban_user_lname,
            fban_user_uname,
            reason,
            int(time.time()),
        )
        if not x:
            await message.reply_text("Failed to ban from the federation!")
            return

        fed_chats = sql.all_fed_chats(fed_id)
        # Will send to current chat
        await context.bot.send_message(
            chat.id,
            "<b>New FederationBan</b>"
            "\n<b>Federation:</b> {}"
            "\n<b>Federation Admin:</b> {}"
            "\n<b>User:</b> {}"
            "\n<b>User ID:</b> <code>{}</code>"
            "\n<b>Reason:</b> {}".format(
                fed_name,
                mention_html(user.id, user.first_name),
                user_target,
                fban_user_id,
                reason,
            ),
            parse_mode="HTML",
        )
        # Send message to owner if fednotif is enabled
        if getfednotif:
            await context.bot.send_message(
                info["owner"],
                "<b>FedBan reason updated</b>"
                "\n<b>Federation:</b> {}"
                "\n<b>Federation Admin:</b> {}"
                "\n<b>User:</b> {}"
                "\n<b>User ID:</b> <code>{}</code>"
                "\n<b>Initiated From:</b> <code>{}</code>"
                "\n<b>Reason:</b> {}".format(
                    fed_name,
                    mention_html(user.id, user.first_name),
                    user_target,
                    fban_user_id,
                    message.chat.title,
                    reason,
                ),
                parse_mode="HTML",
            )
        # If fedlog is set, then send message, except fedlog is current chat
        get_fedlog = await sql.get_fed_log(fed_id)
        if get_fedlog:
            if int(get_fedlog) != int(chat.id):
                await context.bot.send_message(
                    get_fedlog,
                    "<b>FedBan reason updated</b>"
                    "\n<b>Federation:</b> {}"
                    "\n<b>Federation Admin:</b> {}"
                    "\n<b>User:</b> {}"
                    "\n<b>User ID:</b> <code>{}</code>"
                    "\n<b>Initiated From:</b> <code>{}</code>"
                    "\n<b>Reason:</b> {}".format(
                        fed_name,
                        mention_html(user.id, user.first_name),
                        user_target,
                        fban_user_id,
                        message.chat.title,
                        reason,
                    ),
                    parse_mode="HTML",
                )
        for fedschat in fed_chats:
            try:
                # Do not spam all fed chats
                """
				context.bot.send_message(chat, "<b>FedBan reason updated</b>" \
							 "\n<b>Federation:</b> {}" \
							 "\n<b>Federation Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
				"""
                await context.bot.ban_chat_member(fedschat, fban_user_id)
            except BadRequest as excp:
                if excp.message in FBAN_ERRORS:
                    try:
                        await application.bot.getChat(fedschat)
                    except Forbidden:
                        sql.chat_leave_fed(fedschat)
                        log.info(
                            "Chat {} has leave fed {} because I was kicked".format(
                                fedschat, info["fname"]
                            )
                        )
                        continue
                elif excp.message == "User_id_invalid":
                    break
                else:
                    log.warning(
                        "Could not fban on {} because: {}".format(chat, excp.message)
                    )
            except TelegramError:
                pass
        # Also do not spam all fed admins

        # send_to_list(bot, FEDADMIN,
        # "<b>FedBan reason updated</b>" \
        # "\n<b>Federation:</b> {}" \
        # "\n<b>Federation Admin:</b> {}" \
        # "\n<b>User:</b> {}" \
        # "\n<b>User ID:</b> <code>{}</code>" \
        # "\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason),
        # html=True)

        # Fban for fed subscriber
        subscriber = list(sql.get_subscriber(fed_id))
        if len(subscriber) != 0:
            for fedsid in subscriber:
                all_fedschat = sql.all_fed_chats(fedsid)
                for fedschat in all_fedschat:
                    try:
                        await context.bot.ban_chat_member(fedschat, fban_user_id)
                    except BadRequest as excp:
                        if excp.message in FBAN_ERRORS:
                            try:
                                await application.bot.getChat(fedschat)
                            except Forbidden:
                                targetfed_id = sql.get_fed_id(fedschat)
                                sql.unsubs_fed(fed_id, targetfed_id)
                                log.info(
                                    "Chat {} has unsub fed {} because I was kicked".format(
                                        fedschat, info["fname"]
                                    )
                                )
                                continue
                        elif excp.message == "User_id_invalid":
                            break
                        else:
                            log.warning(
                                "Unable to fban on {} because: {}".format(
                                    fedschat, excp.message
                                )
                            )
                    except TelegramError:
                        pass
        # send_message(update.effective_message, "Fedban Reason has been updated.")
        return

    fed_name = info["fname"]

    starting = "Starting a federation ban for {} in the Federation <b>{}</b>.".format(
        user_target, fed_name
    )
    await update.effective_message.reply_text(starting, parse_mode=ParseMode.HTML)

    if reason == "":
        reason = "No reason given."

    x = sql.fban_user(
        fed_id,
        fban_user_id,
        fban_user_name,
        fban_user_lname,
        fban_user_uname,
        reason,
        int(time.time()),
    )
    if not x:
        await message.reply_text("Failed to ban from the federation!")
        return

    fed_chats = sql.all_fed_chats(fed_id)
    # Will send to current chat
    await context.bot.send_message(
        chat.id,
        "<b>FedBan reason updated</b>"
        "\n<b>Federation:</b> {}"
        "\n<b>Federation Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>User ID:</b> <code>{}</code>"
        "\n<b>Reason:</b> {}".format(
            fed_name,
            mention_html(user.id, user.first_name),
            user_target,
            fban_user_id,
            reason,
        ),
        parse_mode="HTML",
    )
    # Send message to owner if fednotif is enabled
    if getfednotif:
        await context.bot.send_message(
            info["owner"],
            "<b>FedBan reason updated</b>"
            "\n<b>Federation:</b> {}"
            "\n<b>Federation Admin:</b> {}"
            "\n<b>User:</b> {}"
            "\n<b>User ID:</b> <code>{}</code>"
            "\n<b>Initiated From:</b> <code>{}</code>"
            "\n<b>Reason:</b> {}".format(
                fed_name,
                mention_html(user.id, user.first_name),
                user_target,
                fban_user_id,
                message.chat.title,
                reason,
            ),
            parse_mode="HTML",
        )
    # If fedlog is set, then send message, except fedlog is current chat
    get_fedlog = await sql.get_fed_log(fed_id)
    if get_fedlog:
        if int(get_fedlog) != int(chat.id):
            await context.bot.send_message(
                get_fedlog,
                "<b>FedBan reason updated</b>"
                "\n<b>Federation:</b> {}"
                "\n<b>Federation Admin:</b> {}"
                "\n<b>User:</b> {}"
                "\n<b>User ID:</b> <code>{}</code>"
                "\n<b>Initiated From:</b> <code>{}</code>"
                "\n<b>Reason:</b> {}".format(
                    fed_name,
                    mention_html(user.id, user.first_name),
                    user_target,
                    fban_user_id,
                    message.chat.title,
                    reason,
                ),
                parse_mode="HTML",
            )
    chats_in_fed = 0
    for fedschat in fed_chats:
        chats_in_fed += 1
        try:
            # Do not spamming all fed chats
            """
			context.bot.send_message(chat, "<b>FedBan reason updated</b>" \
							"\n<b>Federation:</b> {}" \
							"\n<b>Federation Admin:</b> {}" \
							"\n<b>User:</b> {}" \
							"\n<b>User ID:</b> <code>{}</code>" \
							"\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
			"""
            await context.bot.ban_chat_member(fedschat, fban_user_id)
        except BadRequest as excp:
            if excp.message in FBAN_ERRORS:
                pass
            elif excp.message == "User_id_invalid":
                break
            else:
                log.warning(
                    "Could not fban on {} because: {}".format(chat, excp.message)
                )
        except TelegramError:
            pass

        # Also do not spamming all fed admins
        """
		send_to_list(bot, FEDADMIN,
				 "<b>FedBan reason updated</b>" \
							 "\n<b>Federation:</b> {}" \
							 "\n<b>Federation Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason),
							html=True)
		"""

        # Fban for fed subscriber
        subscriber = list(sql.get_subscriber(fed_id))
        if len(subscriber) != 0:
            for fedsid in subscriber:
                all_fedschat = sql.all_fed_chats(fedsid)
                for fedschat in all_fedschat:
                    try:
                        await context.bot.ban_chat_member(fedschat, fban_user_id)
                    except BadRequest as excp:
                        if excp.message in FBAN_ERRORS:
                            try:
                                await application.bot.getChat(fedschat)
                            except Forbidden:
                                targetfed_id = sql.get_fed_id(fedschat)
                                sql.unsubs_fed(fed_id, targetfed_id)
                                log.info(
                                    "Chat {} has unsub fed {} because I was kicked".format(
                                        fedschat, info["fname"]
                                    )
                                )
                                continue
                        elif excp.message == "User_id_invalid":
                            break
                        else:
                            log.warning(
                                "Unable to fban on {} because: {}".format(
                                    fedschat, excp.message
                                )
                            )
                    except TelegramError:
                        pass
    if chats_in_fed == 0:
        send_message(update.effective_message, "Fedban affected 0 chats. ")
    elif chats_in_fed > 0:
        send_message(
            update.effective_message,
            "Fedban affected {} chats. ".format(chats_in_fed),
        )



async def unfban(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        await update.effective_message.reply_text(
            "This group is not a part of any federation!"
        )
        return

    info = sql.get_fed_info(fed_id)
    getfednotif = sql.user_feds_report(info["owner"])

    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only federation admins can do this!")
        return

    user_id = extract_user_fban(message, args)
    if not user_id:
        await message.reply_text("You do not seem to be referring to a user.")
        return

    try:
        user_chat = await context.bot.get_chat(user_id)
        isvalid = True
        fban_user_id = user_chat.id
        fban_user_name = user_chat.first_name
        fban_user_lname = user_chat.last_name
        fban_user_uname = user_chat.username
    except BadRequest as excp:
        if not str(user_id).isdigit():
            send_message(update.effective_message, excp.message)
            return
        elif not len(str(user_id)) == 9:
            send_message(update.effective_message, "That's so not a user!")
            return
        isvalid = False
        fban_user_id = int(user_id)
        fban_user_name = "user({})".format(user_id)
        fban_user_lname = None
        fban_user_uname = None

    if isvalid and user_chat.type != "private":
        await message.reply_text("That's so not a user!")
        return

    if isvalid:
        user_target = mention_html(fban_user_id, fban_user_name)
    else:
        user_target = fban_user_name

    fban, fbanreason, fbantime = sql.get_fban_user(fed_id, fban_user_id)
    if fban is False:
        await message.reply_text("This user is not fbanned!")
        return

    await message.reply_text(
        "I'll give {} another chance in this federation".format(user_chat.first_name)
    )

    chat_list = sql.all_fed_chats(fed_id)
    # Will send to current chat
    await context.bot.send_message(
        chat.id,
        "<b>Un-FedBan</b>"
        "\n<b>Federation:</b> {}"
        "\n<b>Federation Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>User ID:</b> <code>{}</code>".format(
            info["fname"],
            mention_html(user.id, user.first_name),
            user_target,
            fban_user_id,
        ),
        parse_mode="HTML",
    )
    # Send message to owner if fednotif is enabled
    if getfednotif:
        await context.bot.send_message(
            info["owner"],
            "<b>Un-FedBan</b>"
            "\n<b>Federation:</b> {}"
            "\n<b>Federation Admin:</b> {}"
            "\n<b>User:</b> {}"
            "\n<b>User ID:</b> <code>{}</code>"
	    "\n<b>Initiated From:</b> <code>{}</code>".format(
                info["fname"],
                mention_html(user.id, user.first_name),
                user_target,
                fban_user_id,
		message.chat.title,
            ),
            parse_mode="HTML",
        )
        # If fedlog is set, then send message, except fedlog is current chat
        get_fedlog = await sql.get_fed_log(fed_id)
        if get_fedlog:
            if int(get_fedlog) != int(chat.id):
                await context.bot.send_message(
                    get_fedlog,
                    "<b>FedBan reason updated</b>"
                    "\n<b>Federation:</b> {}"
                    "\n<b>Federation Admin:</b> {}"
                    "\n<b>User:</b> {}"
                    "\n<b>User ID:</b> <code>{}</code>"
                    "\n<b>Initiated From:</b> <code>{}</code>"
                    "\n<b>Reason:</b> {}".format(
                        fed_name,
                        mention_html(user.id, user.first_name),
                        user_target,
                        fban_user_id,
                        message.chat.title,
                        reason,
                    ),
                    parse_mode="HTML",
                )
        for fedschat in fed_chats:
            try:
                # Do not spam all fed chats
                """
				context.bot.send_message(chat, "<b>FedBan reason updated</b>" \
							 "\n<b>Federation:</b> {}" \
							 "\n<b>Federation Admin:</b> {}" \
							 "\n<b>User:</b> {}" \
							 "\n<b>User ID:</b> <code>{}</code>" \
							 "\n<b>Reason:</b> {}".format(fed_name, mention_html(user.id, user.first_name), user_target, fban_user_id, reason), parse_mode="HTML")
				"""
                await context.bot.ban_chat_member(fedschat, fban_user_id)
            except BadRequest as excp:
                if excp.message in FBAN_ERRORS:
                    try:
                        await CUTIEPII_PTB.bot.getChat(fedschat)
                    except Forbidden:
                        sql.chat_leave_fed(fedschat)
                        log.info(
                            "Chat {} has leave fed {} because I was kicked".format(
                                fedschat, info["fname"]
                            )
                        )
                        continue
                elif excp.message == "User_id_invalid":
                    break
                else:
                    log.warning(
                        "Could not fban on {} because: {}".format(chat, excp.message)
                    )
            except TelegramError:
                pass

    if unfbanned_in_chats == 0:
        send_message(
            update.effective_message,
            "This person has been un-fbanned in 0 chats.",
        )
    if unfbanned_in_chats > 0:
        send_message(
            update.effective_message,
            "This person has been un-fbanned in {} chats.".format(unfbanned_in_chats),
        )
    # Also do not spamming all fed admins
    """
	FEDADMIN = sql.all_fed_users(fed_id)
	for x in FEDADMIN:
		getreport = sql.user_feds_report(x)
		if getreport == False:
			FEDADMIN.remove(x)
	send_to_list(bot, FEDADMIN,
			 "<b>Un-FedBan</b>" \
			 "\n<b>Federation:</b> {}" \
			 "\n<b>Federation Admin:</b> {}" \
			 "\n<b>User:</b> {}" \
			 "\n<b>User ID:</b> <code>{}</code>".format(info['fname'], mention_html(user.id, user.first_name),
												 mention_html(user_chat.id, user_chat.first_name),
															  user_chat.id),
			html=True)
	"""


async def set_frules(update, context):

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        await update.effective_message.reply_text("This chat is not in any federation!")
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only fed admins can do this!")
        return

    if len(args) >= 1:
        msg = update.effective_message  # type: Optional[Message]
        raw_text = msg.text
        args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
        if len(args) == 2:
            txt = args[1]
            offset = len(txt) - len(raw_text)  # set correct offset relative to command
            markdown_rules = markdown_parser(
                txt, entities=msg.parse_entities(), offset=offset
            )
        x = sql.set_frules(fed_id, markdown_rules)
        if not x:
            await update.effective_message.reply_text(
                "Big F! There is an error while setting federation rules!"
            )
            return

        rules = sql.get_fed_info(fed_id)["frules"]
        getfed = sql.get_fed_info(fed_id)
        get_fedlog = sql.get_fed_log(fed_id)
        if get_fedlog:
            if ast.literal_eval(get_fedlog):
                await context.bot.send_message(
                    get_fedlog,
                    "*{}* has changed federation rules for fed *{}*".format(
                        user.first_name, getfed["fname"]
                    ),
                    parse_mode="markdown",
                )
        await update.effective_message.reply_text(f"Rules have been changed to :\n{rules}!")
    else:
        await update.effective_message.reply_text("Please write rules to set it up!")


async def set_frules(update, context):

    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        await update.effective_message.reply_text("This chat is not in any federation!")
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only fed admins can do this!")
        return

    if len(args) >= 1:
        msg = update.effective_message  # type: Optional[Message]
        raw_text = msg.text
        args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
        if len(args) == 2:
            txt = args[1]
            offset = len(txt) - len(raw_text)  # set correct offset relative to command
            markdown_rules = markdown_parser(
                txt, entities=msg.parse_entities(), offset=offset
            )
        x = sql.set_frules(fed_id, markdown_rules)
        if not x:
            await update.effective_message.reply_text(
                "Big F! There is an error while setting federation rules!"
            )
            return

        rules = sql.get_fed_info(fed_id)["frules"]
        getfed = sql.get_fed_info(fed_id)
        get_fedlog = sql.get_fed_log(fed_id)
        if get_fedlog:
            if ast.literal_eval(get_fedlog):
                await context.bot.send_message(
                    get_fedlog,
                    "*{}* has changed federation rules for fed *{}*".format(
                        user.first_name, getfed["fname"]
                    ),
                    parse_mode="markdown",
                )
        await update.effective_message.reply_text(f"Rules have been changed to :\n{rules}!")
    else:
        await update.effective_message.reply_text("Please write rules to set it up!")


@typing_action
async def get_frules(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    if not fed_id:
        await update.effective_message.reply_text("This chat is not in any federation!")
        return

    rules = sql.get_frules(fed_id)
    text = "*Rules in this fed:*\n"
    text += rules
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@typing_action
async def fed_broadcast(update, context):
    msg = update.effective_message  # type: Optional[Message]
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    if args:
        chat = update.effective_chat  # type: Optional[Chat]
        fed_id = sql.get_fed_id(chat.id)
        fedinfo = sql.get_fed_info(fed_id)
        # Parsing md
        raw_text = msg.text
        args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args
        txt = args[1]
        offset = len(txt) - len(raw_text)  # set correct offset relative to command
        text_parser = markdown_parser(txt, entities=msg.parse_entities(), offset=offset)
        text = text_parser
        try:
            broadcaster = user.first_name
        except:
            broadcaster = user.first_name + " " + user.last_name
        text += "\n\n- {}".format(mention_markdown(user.id, broadcaster))
        chat_list = sql.all_fed_chats(fed_id)
        failed = 0
        for chat in chat_list:
            title = "*New broadcast from Fed {}*\n".format(fedinfo["fname"])
            try:
                await context.bot.sendMessage(chat, title + text, parse_mode="markdown")
            except TelegramError:
                try:
                    await CUTIEPII_PTB.bot.getChat(chat)
                except Forbidden:
                    failed += 1
                    sql.chat_leave_fed(chat)
                    LOGGER.info(
                        "Chat {} has leave fed {} because I was kicked".format(
                            chat, fedinfo["fname"]
                        )
                    )
                    continue
                failed += 1
                LOGGER.warning("Couldn't send broadcast to {}".format(str(chat)))

        send_text = "The federation broadcast is complete"
        if failed >= 1:
            send_text += "{} the group failed to receive the message, probably because it left the Federation.".format(
                failed
            )
        await update.effective_message.reply_text(send_text)


@send_action(ChatAction.UPLOAD_DOCUMENT)
async def fed_ban_list(update, context):  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    chat_data = context.chat_data

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    info = sql.get_fed_info(fed_id)

    if not fed_id:
        await update.effective_message.reply_text(
            "This group is not a part of any federation!"
        )
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only Federation owners can do this!")
        return

    user = update.effective_user  # type: Optional[Chat]
    chat = update.effective_chat  # type: Optional[Chat]
    getfban = sql.get_all_fban_users(fed_id)
    if len(getfban) == 0:
        await update.effective_message.reply_text(
            "The federation ban list of {} is empty".format(info["fname"]),
            parse_mode=ParseMode.HTML,
        )
        return

    if args:
        if args[0] == "json":
            jam = time.time()
            new_jam = jam + 1800
            cek = get_chat(chat.id, chat_data)
            if cek.get("status"):
                if jam <= int(cek.get("value")):
                    waktu = time.strftime(
                        "%H:%M:%S %d/%m/%Y", time.localtime(cek.get("value"))
                    )
                    await update.effective_message.reply_text(
                        "You can backup your data once every 30 minutes!\nYou can back up data again at `{}`".format(
                            waktu
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return
                else:
                    if user.id not in SUDO_USERS:
                        put_chat(chat.id, new_jam, chat_data)
            elif user.id not in SUDO_USERS:
                put_chat(chat.id, new_jam, chat_data)
            backups = ""
            for users in getfban:
                getuserinfo = sql.get_all_fban_users_target(fed_id, users)
                json_parser = {
                    "user_id": users,
                    "first_name": getuserinfo["first_name"],
                    "last_name": getuserinfo["last_name"],
                    "user_name": getuserinfo["user_name"],
                    "reason": getuserinfo["reason"],
                }
                backups += json.dumps(json_parser)
                backups += "\n"
            with BytesIO(str.encode(backups)) as output:
                output.name = "{}_fbanned_users.json".format(CUTIEPII_PTB.bot.username)
                update.effective_message.reply_document(
                    document=output,
                    filename="{}_fbanned_users.json".format(CUTIEPII_PTB.bot.username),
                    caption="Total {} User are blocked by the Federation {}.".format(
                        len(getfban), info["fname"]
                    ),
                )
            return
        elif args[0] == "csv":
            jam = time.time()
            new_jam = jam + 1800
            cek = get_chat(chat.id, chat_data)
            if cek.get("status"):
                if jam <= int(cek.get("value")):
                    waktu = time.strftime(
                        "%H:%M:%S %d/%m/%Y", time.localtime(cek.get("value"))
                    )
                    await update.effective_message.reply_text(
                        "You can back up data once every 30 minutes!\nYou can back up data again at `{}`".format(
                            waktu
                        ),
                        parse_mode=ParseMode.MARKDOWN,
                    )
                    return
                else:
                    if user.id not in SUDO_USERS:
                        put_chat(chat.id, new_jam, chat_data)
            elif user.id not in SUDO_USERS:
                put_chat(chat.id, new_jam, chat_data)
            backups = "id,firstname,lastname,username,reason\n"
            for users in getfban:
                getuserinfo = sql.get_all_fban_users_target(fed_id, users)
                backups += (
                    "{user_id},{first_name},{last_name},{user_name},{reason}".format(
                        user_id=users,
                        first_name=getuserinfo["first_name"],
                        last_name=getuserinfo["last_name"],
                        user_name=getuserinfo["user_name"],
                        reason=getuserinfo["reason"],
                    )
                )
                backups += "\n"
            with BytesIO(str.encode(backups)) as output:
                output.name = "{}_fbanned_users.csv".format(CUTIEPII_PTB.bot.username)
                update.effective_message.reply_document(
                    document=output,
                    filename="{}_fbanned_users.csv".format(CUTIEPII_PTB.bot.username),
                    caption="Total {} User are blocked by Federation {}.".format(
                        len(getfban), info["fname"]
                    ),
                )
            return

    text = "<b>{} users have been banned from the federation {}:</b>\n".format(
        len(getfban), info["fname"]
    )
    for users in getfban:
        getuserinfo = sql.get_all_fban_users_target(fed_id, users)
        if getuserinfo is False:
            text = "There are no users banned from the federation {}".format(
                info["fname"]
            )
            break
        user_name = getuserinfo["first_name"]
        if getuserinfo["last_name"]:
            user_name += " " + getuserinfo["last_name"]
        text += " ➛ {} (<code>{}</code>)\n".format(
            mention_html(users, user_name), users
        )

    try:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        jam = time.time()
        new_jam = jam + 1800
        cek = get_chat(chat.id, chat_data)
        if cek.get("status"):
            if jam <= int(cek.get("value")):
                waktu = time.strftime(
                    "%H:%M:%S %d/%m/%Y", time.localtime(cek.get("value"))
                )
                await update.effective_message.reply_text(
                    "You can back up data once every 30 minutes!\nYou can back up data again at `{}`".format(
                        waktu
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            else:
                if user.id not in SUDO_USERS:
                    put_chat(chat.id, new_jam, chat_data)
        elif user.id not in SUDO_USERS:
            put_chat(chat.id, new_jam, chat_data)
        cleanr = re.compile("<.*?>")
        cleantext = re.sub(cleanr, "", text)
        with BytesIO(str.encode(cleantext)) as output:
            output.name = "fbanlist.txt"
            update.effective_message.reply_document(
                document=output,
                filename="fbanlist.txt",
                caption="The following is a list of users who are currently fbanned in the Federation {}.".format(
                    info["fname"]
                ),
            )


@typing_action
async def fed_notif(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args
    fed_id = sql.get_fed_id(chat.id)

    if not fed_id:
        await update.effective_message.reply_text(
            "This group is not a part of any federation!"
        )
        return

    if args:
        if args[0] in ("yes", "on"):
            sql.set_feds_setting(user.id, True)
            await msg.reply_text(
                "Reporting Federation back up! Every user who is fban / unfban you will be notified via PM."
            )
        elif args[0] in ("no", "off"):
            sql.set_feds_setting(user.id, False)
            await msg.reply_text(
                "Reporting Federation has stopped! Every user who is fban / unfban you will not be notified via PM."
            )
        else:
            await msg.reply_text("Please enter `on`/`off`", parse_mode="markdown")
    else:
        getreport = sql.user_feds_report(user.id)
        await msg.reply_text(
            "Your current Federation report preferences: `{}`".format(getreport),
            parse_mode="markdown",
        )


@typing_action
async def fed_chats(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args
    chat_name = ""

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    info = sql.get_fed_info(fed_id)

    if not fed_id:
        await update.effective_message.reply_text(
            "This group is not a part of any federation!"
        )
        return

    if is_user_fed_admin(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only federation admins can do this!")
        return

    getlist = sql.all_fed_chats(fed_id)
    if len(getlist) == 0:
        await update.effective_message.reply_text(
            "No users are fbanned from the federation {}".format(info["fname"]),
            parse_mode=ParseMode.HTML,
        )
        return

    text = "<b>New chat joined the federation {}:</b>\n".format(info["fname"])
    for chats in getlist:
        try:
            chat_name = await CUTIEPII_PTB.bot.getChat(chats).title
        except Forbidden:
            sql.chat_leave_fed(chats)
            LOGGER.info(
                "Chat {} has leave fed {} because I was kicked".format(
                    chats, info["fname"]
                )
            )
            continue
        except BadRequest as excp:
            if excp.message in FBAN_ERRORS:
                pass
            text += " ➛ {} (<code>{}</code>)\n".format(chat_name, chats)

    try:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
    except:
        cleanr = re.compile("<.*?>")
        cleantext = re.sub(cleanr, "", text)
        with BytesIO(str.encode(cleantext)) as output:
            output.name = "fedchats.txt"
            update.effective_message.reply_document(
                document=output,
                filename="fedchats.txt",
                caption="Here is a list of all the chats that joined the federation {}.".format(
                    info["fname"]
                ),
            )


@typing_action
async def fed_import_bans(update, context):  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    chat_data = context.chat_data

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    # info = sql.get_fed_info(fed_id)
    getfed = sql.get_fed_info(fed_id)

    if not fed_id:
        await update.effective_message.reply_text(
            "This group is not a part of any federation!"
        )
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        await update.effective_message.reply_text("Only Federation owners can do this!")
        return

    if msg.reply_to_message and msg.reply_to_message.document:
        jam = time.time()
        new_jam = jam + 1800
        cek = get_chat(chat.id, chat_data)
        if cek.get("status"):
            if jam <= int(cek.get("value")):
                waktu = time.strftime(
                    "%H:%M:%S %d/%m/%Y", time.localtime(cek.get("value"))
                )
                await update.effective_message.reply_text(
                    "You can get your data once every 30 minutes!\nYou can get data again at `{}`".format(
                        waktu
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                return
            else:
                if user.id not in SUDO_USERS:
                    put_chat(chat.id, new_jam, chat_data)
        else:
            if user.id not in SUDO_USERS:
                put_chat(chat.id, new_jam, chat_data)
        # if int(int(msg.reply_to_message.document.file_size)/1024) >= 200:
        # 	msg.reply_text("This file is too big!")
        # 	return
        success = 0
        failed = 0
        try:
            file_info = await context.bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            await msg.reply_text(
                "Try downloading and re-uploading the file, this one seems broken!"
            )
            return
        fileformat = msg.reply_to_message.document.file_name.split(".")[-1]
        if fileformat == "json":
            multi_fed_id = []
            multi_import_userid = []
            multi_import_firstname = []
            multi_import_lastname = []
            multi_import_username = []
            multi_import_reason = []
            with BytesIO() as file:
                file_info.download(out=file)
                file.seek(0)
                reading = file.read().decode("UTF-8")
                splitting = reading.split("\n")
                for x in splitting:
                    if x == "":
                        continue
                    try:
                        data = json.loads(x)
                    except json.decoder.JSONDecodeError:
                        failed += 1
                        continue
                    try:
                        import_userid = int(data["user_id"])  # Make sure it int
                        import_firstname = str(data["first_name"])
                        import_lastname = str(data["last_name"])
                        import_username = str(data["user_name"])
                        import_reason = str(data["reason"])
                    except ValueError:
                        failed += 1
                        continue
                    # Checking user
                    if int(import_userid) == context.bot.id:
                        failed += 1
                        continue
                    if is_user_fed_owner(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if is_user_fed_admin(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if str(import_userid) == str(OWNER_ID):
                        failed += 1
                        continue
                    if int(import_userid) in SUDO_USERS:
                        failed += 1
                        continue
                    if int(import_userid) in WHITELIST_USERS:
                        failed += 1
                        continue
                    multi_fed_id.append(fed_id)
                    multi_import_userid.append(str(import_userid))
                    multi_import_firstname.append(import_firstname)
                    multi_import_lastname.append(import_lastname)
                    multi_import_username.append(import_username)
                    multi_import_reason.append(import_reason)
                    success += 1
                sql.multi_fban_user(
                    multi_fed_id,
                    multi_import_userid,
                    multi_import_firstname,
                    multi_import_lastname,
                    multi_import_username,
                    multi_import_reason,
                )
            text = "Blocks were successfully imported. {} people are blocked.".format(
                success
            )
            if failed >= 1:
                text += " {} Failed to import.".format(failed)
            get_fedlog = sql.get_fed_log(fed_id)
            if get_fedlog:
                if ast.literal_eval(get_fedlog):
                    teks = "Fed *{}* has successfully imported data. {} banned.".format(
                        getfed["fname"], success
                    )
                    if failed >= 1:
                        teks += " {} Failed to import.".format(failed)
                    await context.bot.send_message(get_fedlog, teks, parse_mode="markdown")
        elif fileformat == "csv":
            multi_fed_id = []
            multi_import_userid = []
            multi_import_firstname = []
            multi_import_lastname = []
            multi_import_username = []
            multi_import_reason = []
            file_info.download(
                "fban_{}.csv".format(msg.reply_to_message.document.file_id)
            )
            with open(
                "fban_{}.csv".format(msg.reply_to_message.document.file_id),
                "r",
                encoding="utf8",
            ) as csvFile:
                reader = csv.reader(csvFile)
                for data in reader:
                    try:
                        import_userid = int(data[0])  # Make sure it int
                        import_firstname = str(data[1])
                        import_lastname = str(data[2])
                        import_username = str(data[3])
                        import_reason = str(data[4])
                    except ValueError:
                        failed += 1
                        continue
                    # Checking user
                    if int(import_userid) == context.bot.id:
                        failed += 1
                        continue
                    if is_user_fed_owner(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if is_user_fed_admin(fed_id, import_userid) is True:
                        failed += 1
                        continue
                    if str(import_userid) == str(OWNER_ID):
                        failed += 1
                        continue
                    if int(import_userid) in SUDO_USERS:
                        failed += 1
                        continue
                    if int(import_userid) in WHITELIST_USERS:
                        failed += 1
                        continue
                    multi_fed_id.append(fed_id)
                    multi_import_userid.append(str(import_userid))
                    multi_import_firstname.append(import_firstname)
                    multi_import_lastname.append(import_lastname)
                    multi_import_username.append(import_username)
                    multi_import_reason.append(import_reason)
                    success += 1
                    # t = ThreadWithReturnValue(target=sql.fban_user, args=(fed_id, str(import_userid), import_firstname, import_lastname, import_username, import_reason,))
                    # t.start()
                sql.multi_fban_user(
                    multi_fed_id,
                    multi_import_userid,
                    multi_import_firstname,
                    multi_import_lastname,
                    multi_import_username,
                    multi_import_reason,
                )
            csvFile.close()
            os.remove("fban_{}.csv".format(msg.reply_to_message.document.file_id))
            text = "Files were imported successfully. {} people banned.".format(success)
            if failed >= 1:
                text += " {} Failed to import.".format(failed)
            get_fedlog = sql.get_fed_log(fed_id)
            if get_fedlog:
                if ast.literal_eval(get_fedlog):
                    teks = "Fed *{}* has successfully imported data. {} banned.".format(
                        getfed["fname"], success
                    )
                    if failed >= 1:
                        teks += " {} Failed to import.".format(failed)
                    await context.bot.send_message(get_fedlog, teks, parse_mode="markdown")
        else:
            send_message(update.effective_message, "This file is not supported.")
            return
        send_message(update.effective_message, text)


async def del_fed_button(update, context):
    query = update.callback_query
    fed_id = query.data.split("_")[1]

    if fed_id == "cancel":
        await query.message.edit_text("Federation deletion cancelled")
        return

    getfed = sql.get_fed_info(fed_id)
    if getfed:
        delete = sql.del_fed(fed_id)
        if delete:
            await query.message.edit_text(
                "You have removed your Federation! Now all the Groups that are connected with `{}` do not have a Federation.".format(
                    getfed["fname"]
                ),
                parse_mode="markdown",
            )


@typing_action
async def fed_stat_user(update, context):  # sourcery no-metrics
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if args:
        if args[0].isdigit():
            user_id = args[0]
        else:
            user_id = extract_user(msg, args)
    else:
        user_id = extract_user(msg, args)

    if user_id:
        if len(args) == 2 and args[0].isdigit():
            fed_id = args[1]
            user_name, reason, fbantime = sql.get_user_fban(fed_id, str(user_id))
            if fbantime:
                fbantime = time.strftime("%d/%m/%Y", time.localtime(fbantime))
            else:
                fbantime = "Unavaiable"
            if user_name is False:
                send_message(
                    update.effective_message,
                    "Fed {} not found!".format(fed_id),
                    parse_mode="markdown",
                )
                return
            if user_name == "" or user_name is None:
                user_name = "He/she"
            if not reason:
                send_message(
                    update.effective_message,
                    "{} is not banned in this federation!".format(user_name),
                )
            else:
                teks = "{} banned in this federation because:\n`{}`\n*Banned at:* `{}`".format(
                    user_name, reason, fbantime
                )
                send_message(update.effective_message, teks, parse_mode="markdown")
            return
        user_name, fbanlist = sql.get_user_fbanlist(str(user_id))
        if user_name == "":
            try:
                user_name = await context.bot.get_chat(user_id).first_name
            except BadRequest:
                user_name = "He/she"
            if user_name == "" or user_name is None:
                user_name = "He/she"
        if len(fbanlist) == 0:
            send_message(
                update.effective_message,
                "{} is not banned in any federation!".format(user_name),
            )
            return
        else:
            teks = "{} has been banned in this federation:\n".format(user_name)
            for x in fbanlist:
                teks += "- `{}`: {}\n".format(x[0], x[1][:20])
            teks += "\nIf you want to find out more about the reasons for Fedban specifically, use /fbanstat <FedID>"
            send_message(update.effective_message, teks, parse_mode="markdown")

    elif not msg.reply_to_message and not args:
        user_id = msg.from_user.id
        user_name, fbanlist = sql.get_user_fbanlist(user_id)
        if user_name == "":
            user_name = msg.from_user.first_name
        if len(fbanlist) == 0:
            send_message(
                update.effective_message,
                "{} is not banned in any federation!".format(user_name),
            )
        else:
            teks = "{} has been banned in this federation:\n".format(user_name)
            for x in fbanlist:
                teks += "- `{}`: {}\n".format(x[0], x[1][:20])
            teks += "\nIf you want to find out more about the reasons for Fedban specifically, use /fbanstat <FedID>"
            send_message(update.effective_message, teks, parse_mode="markdown")

    else:
        fed_id = args[0]
        fedinfo = sql.get_fed_info(fed_id)
        if not fedinfo:
            send_message(update.effective_message, "Fed {} not found!".format(fed_id))
            return
        name, reason, fbantime = sql.get_user_fban(fed_id, msg.from_user.id)
        if fbantime:
            fbantime = time.strftime("%d/%m/%Y", time.localtime(fbantime))
        else:
            fbantime = "Unavaiable"
        if not name:
            name = msg.from_user.first_name
        if not reason:
            send_message(
                update.effective_message,
                "{} is not banned in this federation".format(name),
            )
            return
        send_message(
            update.effective_message,
            "{} banned in this federation because:\n`{}`\n*Banned at:* `{}`".format(
                name, reason, fbantime
            ),
            parse_mode="markdown",
        )


@typing_action
def set_fed_log(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    if args:
        fedinfo = sql.get_fed_info(args[0])
        if not fedinfo:
            send_message(update.effective_message, "This Federation does not exist!")
            return
        isowner = is_user_fed_owner(args[0], user.id)
        if not isowner:
            send_message(
                update.effective_message,
                "Only federation creator can set federation logs.",
            )
            return
        setlog = sql.set_fed_log(args[0], chat.id)
        if setlog:
            send_message(
                update.effective_message,
                "Federation log `{}` has been set to {}".format(
                    fedinfo["fname"], chat.title
                ),
                parse_mode="markdown",
            )
    else:
        send_message(
            update.effective_message,
            "You have not provided your federated ID!",
        )


@typing_action
def unset_fed_log(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    if args:
        fedinfo = sql.get_fed_info(args[0])
        if not fedinfo:
            send_message(update.effective_message, "This Federation does not exist!")
            return
        isowner = is_user_fed_owner(args[0], user.id)
        if not isowner:
            send_message(
                update.effective_message,
                "Only federation creator can set federation logs.",
            )
            return
        setlog = sql.set_fed_log(args[0], None)
        if setlog:
            send_message(
                update.effective_message,
                "Federation log `{}` has been revoked on {}".format(
                    fedinfo["fname"], chat.title
                ),
                parse_mode="markdown",
            )
    else:
        send_message(
            update.effective_message,
            "You have not provided your federated ID!",
        )


@typing_action
async def subs_feds(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    fedinfo = sql.get_fed_info(fed_id)

    if not fed_id:
        send_message(update.effective_message, "This chat is not in any federation!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        send_message(update.effective_message, "Only fed owner can do this!")
        return

    if args:
        getfed = sql.search_fed_by_id(args[0])
        if getfed is False:
            send_message(
                update.effective_message, "Please enter a valid federation id."
            )
            return
        subfed = sql.subs_fed(args[0], fed_id)
        if subfed:
            send_message(
                update.effective_message,
                "Federation `{}` has subscribe the federation `{}`. Every time there is a Fedban from that federation, this federation will also banned that user.".format(
                    fedinfo["fname"], getfed["fname"]
                ),
                parse_mode="markdown",
            )
            get_fedlog = sql.get_fed_log(args[0])
            if get_fedlog:
                if int(get_fedlog) != int(chat.id):
                    await context.bot.send_message(
                        get_fedlog,
                        "Federation `{}` has subscribe the federation `{}`".format(
                            fedinfo["fname"], getfed["fname"]
                        ),
                        parse_mode="markdown",
                    )
        else:
            send_message(
                update.effective_message,
                "Federation `{}` already subscribe the federation `{}`.".format(
                    fedinfo["fname"], getfed["fname"]
                ),
                parse_mode="markdown",
            )
    else:
        send_message(
            update.effective_message,
            "You have not provided your federated ID!",
        )


@typing_action
async def unsubs_feds(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    fedinfo = sql.get_fed_info(fed_id)

    if not fed_id:
        send_message(update.effective_message, "This chat is not in any federation!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        send_message(update.effective_message, "Only fed owner can do this!")
        return

    if args:
        getfed = sql.search_fed_by_id(args[0])
        if getfed is False:
            send_message(
                update.effective_message, "Please enter a valid federation id."
            )
            return
        subfed = sql.unsubs_fed(args[0], fed_id)
        if subfed:
            send_message(
                update.effective_message,
                "Federation `{}` now unsubscribe fed `{}`.".format(
                    fedinfo["fname"], getfed["fname"]
                ),
                parse_mode="markdown",
            )
            get_fedlog = sql.get_fed_log(args[0])
            if get_fedlog:
                if int(get_fedlog) != int(chat.id):
                    await context.bot.send_message(
                        get_fedlog,
                        "Federation `{}` has unsubscribe fed `{}`.".format(
                            fedinfo["fname"], getfed["fname"]
                        ),
                        parse_mode="markdown",
                    )
        else:
            send_message(
                update.effective_message,
                "Federation `{}` is not subscribing `{}`.".format(
                    fedinfo["fname"], getfed["fname"]
                ),
                parse_mode="markdown",
            )
    else:
        send_message(
            update.effective_message,
            "You have not provided your federated ID!",
        )


@typing_action
def get_myfedsubs(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    if chat.type == "private":
        send_message(
            update.effective_message,
            "This command is specific to the group, not to the PM! ",
        )
        return

    fed_id = sql.get_fed_id(chat.id)
    fedinfo = sql.get_fed_info(fed_id)

    if not fed_id:
        send_message(update.effective_message, "This chat is not in any federation!")
        return

    if is_user_fed_owner(fed_id, user.id) is False:
        send_message(update.effective_message, "Only fed owner can do this!")
        return

    getmy = sql.get_mysubs(fed_id)

    if getmy is None:
        send_message(
            update.effective_message,
            "Federation `{}` is not subscribing any federation.".format(
                fedinfo["fname"]
            ),
            parse_mode="markdown",
        )
        return
    else:
        listfed = "Federation `{}` is subscribing federation:\n".format(
            fedinfo["fname"]
        )
        for x in getmy:
            listfed += "- `{}`\n".format(x)
        listfed += (
            "\nTo get fed info `/fedinfo <fedid>`. To unsubscribe `/unsubfed <fedid>`."
        )
        send_message(update.effective_message, listfed, parse_mode="markdown")


@typing_action
def get_myfeds_list(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    fedowner = sql.get_user_owner_fed_full(user.id)
    if fedowner:
        text = "*You are owner of feds:\n*"
        for f in fedowner:
            text += "- `{}`: *{}*\n".format(f["fed_id"], f["fed"]["fname"])
    else:
        text = "*You are not have any feds!*"
    send_message(update.effective_message, text, parse_mode="markdown")


def is_user_fed_admin(fed_id, user_id):
    fed_admins = sql.all_fed_users(fed_id)
    if fed_admins is False:
        return False
    if int(user_id) in fed_admins or int(user_id) == OWNER_ID:
        return True
    else:
        return False


def is_user_fed_owner(fed_id, user_id):
    getsql = sql.get_fed_info(fed_id)
    if getsql is False:
        return False
    getfedowner = ast.literal_eval(getsql["fusers"])
    if getfedowner == None or getfedowner == False:
        return False
    getfedowner = getfedowner["owner"]
    if str(user_id) == getfedowner or int(user_id) == OWNER_ID:
        return True
    else:
        return False


async def welcome_fed(update, chat, user_id):

    fed_id = sql.get_fed_id(chat.id)
    fban, fbanreason, fbantime = sql.get_fban_user(fed_id, user_id)
    if fban:
        msgg ="This user is banned in current federation! I will remove him.\n"
        if fbanreason != "No reason given.":
            msgg += "**Reason:** " + str(fbanreason)
        try:
            await update.effective_message.reply_text(msgg, parse_mode="markdown")
        except BadRequest:
            CUTIEPII_PTB.bot.send_message(chat.id, msgg, parse_mode="markdown")
        update.effective_chat.ban_member(user_id)
        return True
    else:
        return False


def __stats__():
    all_fbanned = sql.get_all_fban_users_global()
    all_feds = sql.get_all_feds_users_global()
    return "➛ {} users banned, in {} federations".format(
        len(all_fbanned), len(all_feds)
    )


def __user_info__(user_id, chat_id):
    fed_id = sql.get_fed_id(chat_id)
    if fed_id:
        fban, fbanreason, fbantime = sql.get_fban_user(fed_id, user_id)
        info = sql.get_fed_info(fed_id)
        infoname = info["fname"]

        if int(info["owner"]) == user_id:
            text = (
                "ㅤ<b>Fed owner of: \nㅤ{}</b>.".format(
                    infoname
                )
            )
        elif is_user_fed_admin(fed_id, user_id):
            text = (
                "ㅤ<b>Fed Admin in:\nㅤ{}</b>.".format(
                    infoname
                )
            )

        elif fban:
            text = "\nㅤ<b>FedBanned</b>: Yes"
            text += "\nㅤ<b>Reason</b>: {}".format(fbanreason)
        else:
            text = "ㅤ<b>FedBanned</b>: No"
    else:
        text = ""
    return text


# Temporary data
def put_chat(chat_id, value, chat_data):
    # print(chat_data)
    if value is False:
        status = False
    else:
        status = True
    chat_data[chat_id] = {"federation": {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # print(chat_data)
    try:
        value = chat_data[chat_id]["federation"]
        return value
    except KeyError:
        return {"status": False, "value": False}


async def fed_owner_help(update: Update, context: CallbackContext):
    await update.effective_message.reply_text(
        """*👑 Fed Owner Only:*
➛ /newfed <fed_name>*:* Creates a Federation, One allowed per user
➛ /renamefed <fed_id> <new_fed_name>*:* Renames the fed id to a new name
➛ /delfed <fed_id>*:* Delete a Federation, and any information related to it. Will not cancel blocked users
➛ /fpromote <user>*:* Assigns the user as a federation admin. Enables all commands for the user under `Fed Admins`
➛ /fdemote <user>*:* Drops the User from the admin Federation to a normal User
➛ /subfed <fed_id>*:* Subscribes to a given fed ID, bans from that subscribed fed will also happen in your fed
➛ /unsubfed <fed_id>*:* Unsubscribes to a given fed ID
➛ /setfedlog <fed_id>*:* Sets the group as a fed log report base for the federation
➛ /unsetfedlog <fed_id>*:* Removed the group as a fed log report base for the federation
➛ /fbroadcast <message>*:* Broadcasts a messages to all groups that have joined your fed
➛ /fedsubs*:* Shows the feds your group is subscribed to `(broken rn)`""",
        parse_mode=ParseMode.MARKDOWN,
    )


async def fed_admin_help(update: Update, context: CallbackContext):
    await update.effective_message.reply_text(
        """*🔱 Fed Admins:*
➛ /fban <user> <reason>*:* Fed bans a user
➛ /unfban <user> <reason>*:* Removes a user from a fed ban
➛ /fedinfo <fed_id>*:* Information about the specified Federation
➛ /joinfed <fed_id>*:* Join the current chat to the Federation. Only chat owners can do this. Every chat can only be in one Federation
➛ /leavefed <fed_id>*:* Leave the Federation given. Only chat owners can do this
➛ /setfrules <rules>*:* Arrange Federation rules
➛ /fedadmins*:* Show Federation admin
➛ /fbanlist*:* Displays all users who are victimized at the Federation at this time
➛ /fedchats*:* Get all the chats that are connected in the Federation
➛ /chatfed *:* See the Federation in the current chat\n""",
        parse_mode=ParseMode.MARKDOWN,
    )


async def fed_user_help(update: Update, context: CallbackContext):
    await update.effective_message.reply_text(
        """*🎩 Any user:*
➛ /fbanstat*:* Shows if you/or the user you are replying to or their username is fbanned somewhere or not
➛ /fednotif <on/off>*:* Federation settings not in PM when there are users who are fbaned/unfbanned
➛ /frules*:* See Federation regulations\n""",
        parse_mode=ParseMode.MARKDOWN,
    )

__help__ = """
Everything is fun, until a spammer starts entering your group, and you have to block it. Then you need to start banning more, and more, and it hurts.
But then you have many groups, and you don't want this spammer to be in one of your groups - how can you deal? Do you have to manually block it, in all your groups?\n
*No longer!* With Federation, you can make a ban in one chat overlap with all other chats.\n
You can even designate federation admins, so your trusted admin can ban all the spammers from chats you want to protect.\n

*Commands:*
Feds are now divided into 3 sections for your ease.
➛ /fedownerhelp*:* Provides help for fed creation and owner only commands
➛ /fedadminhelp*:* Provides help for fed administration commands
➛ /feduserhelp*:* Provides help for commands anyone can use
"""

__mod_name__ = "Federations"

NEW_FED_HANDLER = CommandHandler("newfed", new_fed)
DEL_FED_HANDLER = CommandHandler("delfed", del_fed)
RENAME_FED = CommandHandler("renamefed", rename_fed)
JOIN_FED_HANDLER = CommandHandler("joinfed", join_fed)
LEAVE_FED_HANDLER = CommandHandler("leavefed", leave_fed)
PROMOTE_FED_HANDLER = CommandHandler("fpromote", user_join_fed)
DEMOTE_FED_HANDLER = CommandHandler("fdemote", user_demote_fed)
INFO_FED_HANDLER = CommandHandler("fedinfo", fed_info)
BAN_FED_HANDLER = DisableAbleCommandHandler("fban", fed_ban)
UN_BAN_FED_HANDLER = CommandHandler("unfban", unfban)
FED_BROADCAST_HANDLER = CommandHandler("fbroadcast", fed_broadcast)
FED_SET_RULES_HANDLER = CommandHandler("setfrules", set_frules)
FED_GET_RULES_HANDLER = CommandHandler("frules", get_frules)
FED_CHAT_HANDLER = CommandHandler("chatfed", fed_chat)
FED_ADMIN_HANDLER = CommandHandler("fedadmins", fed_admin)
FED_USERBAN_HANDLER = CommandHandler("fbanlist", fed_ban_list)
FED_NOTIF_HANDLER = CommandHandler("fednotif", fed_notif)
FED_CHATLIST_HANDLER = CommandHandler("fedchats", fed_chats)
FED_IMPORTBAN_HANDLER = CommandHandler("importfbans", fed_import_bans)
FEDSTAT_USER = DisableAbleCommandHandler(["fedstat", "fbanstat"], fed_stat_user)
SET_FED_LOG = CommandHandler("setfedlog", set_fed_log)
UNSET_FED_LOG = CommandHandler("unsetfedlog", unset_fed_log)
SUBS_FED = CommandHandler("subfed", subs_feds)
UNSUBS_FED = CommandHandler("unsubfed", unsubs_feds)
MY_SUB_FED = CommandHandler("fedsubs", get_myfedsubs)
MY_FEDS_LIST = CommandHandler("myfeds", get_myfeds_list)
DELETEBTN_FED_HANDLER = CallbackQueryHandler(del_fed_button, pattern=r"rmfed_")
FED_OWNER_HELP_HANDLER = CommandHandler("fedownerhelp", fed_owner_help)
FED_ADMIN_HELP_HANDLER = CommandHandler("fedadminhelp", fed_admin_help)
FED_USER_HELP_HANDLER = CommandHandler("feduserhelp", fed_user_help)

CUTIEPII_PTB.add_handler(NEW_FED_HANDLER)
CUTIEPII_PTB.add_handler(DEL_FED_HANDLER)
CUTIEPII_PTB.add_handler(RENAME_FED)
CUTIEPII_PTB.add_handler(JOIN_FED_HANDLER)
CUTIEPII_PTB.add_handler(LEAVE_FED_HANDLER)
CUTIEPII_PTB.add_handler(PROMOTE_FED_HANDLER)
CUTIEPII_PTB.add_handler(DEMOTE_FED_HANDLER)
CUTIEPII_PTB.add_handler(INFO_FED_HANDLER)
CUTIEPII_PTB.add_handler(BAN_FED_HANDLER)
CUTIEPII_PTB.add_handler(UN_BAN_FED_HANDLER)
CUTIEPII_PTB.add_handler(FED_BROADCAST_HANDLER)
CUTIEPII_PTB.add_handler(FED_SET_RULES_HANDLER)
CUTIEPII_PTB.add_handler(FED_GET_RULES_HANDLER)
CUTIEPII_PTB.add_handler(FED_CHAT_HANDLER)
CUTIEPII_PTB.add_handler(FED_ADMIN_HANDLER)
CUTIEPII_PTB.add_handler(FED_USERBAN_HANDLER)
CUTIEPII_PTB.add_handler(FED_NOTIF_HANDLER)
CUTIEPII_PTB.add_handler(FED_CHATLIST_HANDLER)
# CUTIEPII_PTB.add_handler(FED_IMPORTBAN_HANDLER)
CUTIEPII_PTB.add_handler(FEDSTAT_USER)
CUTIEPII_PTB.add_handler(SET_FED_LOG)
CUTIEPII_PTB.add_handler(UNSET_FED_LOG)
CUTIEPII_PTB.add_handler(SUBS_FED)
CUTIEPII_PTB.add_handler(UNSUBS_FED)
CUTIEPII_PTB.add_handler(MY_SUB_FED)
CUTIEPII_PTB.add_handler(MY_FEDS_LIST)
CUTIEPII_PTB.add_handler(DELETEBTN_FED_HANDLER)
CUTIEPII_PTB.add_handler(FED_OWNER_HELP_HANDLER)
CUTIEPII_PTB.add_handler(FED_ADMIN_HELP_HANDLER)
CUTIEPII_PTB.add_handler(FED_USER_HELP_HANDLER)
