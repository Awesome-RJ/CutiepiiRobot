"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

import html
import os
import requests
import datetime
import asyncio
import contextlib

from pyrogram import filters, Client
from pyrogram.errors import PeerIdInvalid
from pyrogram.types import Message, User

from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import ChannelParticipantsAdmins, InputMessagesFilterContacts, InputMessagesFilterDocument, InputMessagesFilterGeo, InputMessagesFilterGif, InputMessagesFilterMusic, InputMessagesFilterPhotos, InputMessagesFilterRoundVideo, InputMessagesFilterUrl, InputMessagesFilterVideo
from telethon import events

from telegram import Update, MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, MessageLimit, ChatType
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from telegram.helpers import escape_markdown, mention_html

from Cutiepii_Robot.utils.sections import section
from Cutiepii_Robot import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    TIGER_USERS,
    WHITELIST_USERS,
    INFOPIC,
    CUTIEPII_PTB,
    ubot,
    telethn,
    pgram,
)
from Cutiepii_Robot.__main__ import TOKEN, USER_INFO
import Cutiepii_Robot.modules.sql.userinfo_sql as sql
from Cutiepii_Robot.modules.helper_funcs.misc import delete
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.sql.global_bans_sql import is_user_gbanned
from Cutiepii_Robot.modules.redis.afk_redis import is_user_afk, afk_reason
from Cutiepii_Robot.modules.sql.users_sql import get_user_num_chats
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user

Cutiepii_PYRO_Whois = filters.command("whois")


# whois
def ReplyCheck(message: Message):
    reply_id = None
    if message.reply_to_message:
        reply_id = message.reply_to_message.id
    elif not message.from_user.is_self:
        reply_id = message.id
    return reply_id


infotext = ("**[{full_name}](tg://user?id={user_id})**\n"
            " * UserID: `{user_id}`\n"
            " * First Name: `{first_name}`\n"
            " * Last Name: `{last_name}`\n"
            " * Username: `{username}`\n"
            " * Last Online: `{last_online}`\n"
            " * Bio: {bio}")


def LastOnline(user: User):
    if user.is_bot:
        return ""
    if user.status == "recently":
        return "Recently"
    if user.status == "within_week":
        return "Within the last week"
    if user.status == "within_month":
        return "Within the last month"
    if user.status == "long_time_ago":
        return "A long time ago :("
    if user.status == "online":
        return "Currently Online"
    if user.status == "offline":
        return datetime.fromtimestamp(
            user.status.date).strftime("%a, %d %b %Y, %H:%M:%S")


def FullName(user: User):
    return (f"{user.first_name} {user.last_name}"
            if user.last_name else user.first_name)


@pgram.on_message(Cutiepii_PYRO_Whois)
@pgram.on_edited_message(Cutiepii_PYRO_Whois)
async def whois(client: Client, message: Message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        with contextlib.suppress(ValueError):
            get_user = int(cmd[1])
    try:
        user = await client.get_users(get_user)
    except PeerIdInvalid:
        await message.reply("I don't know that User.")
        return
    desc = await client.get_users(get_user)
    desc = desc.description
    await message.reply_text(
        infotext.format(
            full_name=FullName(user),
            user_id=user.id,
            user_dc=user.dc_id,
            first_name=user.first_name,
            last_name=user.last_name or "",
            username=user.username or "",
            last_online=LastOnline(user),
            bio=desc or "`No bio set up.`",
        ),
        disable_web_page_preview=True,
    )


def biome(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    result = ""
    if me:
        result += f"<b>About user:</b>\n{me}\n"
    if bio:
        result += f"<b>What others say:</b>\n{bio}\n"
    result = result.strip("\n")
    return result


def no_by_per(totalhp, percentage):
    """
    rtype: num of `percentage` from total
    eg: 1000, 10 -> 10% of 1000 (100)
    """
    return totalhp * percentage / 100


def get_percentage(totalhp, earnedhp):
    """
    rtype: percentage of `totalhp` num
    eg: (1000, 100) will return 10%
    """

    matched_less = totalhp - earnedhp
    per_of_totalhp = 100 - matched_less * 100.0 / totalhp
    per_of_totalhp = str(int(per_of_totalhp))
    return per_of_totalhp


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(
            seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += f'{time_list.pop()}, '

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


def hpmanager(user):
    total_hp = (get_user_num_chats(user.id) + 10) * 10

    if not is_user_gbanned(user.id):

        # Assign new var `new_hp` since we need `total_hp` in
        # end to calculate percentage.
        new_hp = total_hp

        # if no username decrease 25% of hp.
        if not user.username:
            new_hp -= no_by_per(total_hp, 25)
        try:
            CUTIEPII_PTB.bot.get_user_profile_photos(user.id).photos[0][-1]
        except IndexError:
            # no profile photo ==> -25% of hp
            new_hp -= no_by_per(total_hp, 25)
        # if no /setme exist ==> -20% of hp
        if not sql.get_user_me_info(user.id):
            new_hp -= no_by_per(total_hp, 20)
        # if no bio exsit ==> -10% of hp
        if not sql.get_user_bio(user.id):
            new_hp -= no_by_per(total_hp, 10)

        if is_user_afk(user.id):
            afkst = afk_reason(user.id)
            # if user is afk and no reason then decrease 7%
            # else if reason exist decrease 5%
            new_hp -= no_by_per(total_hp, 5) if afkst else no_by_per(
                total_hp, 7)
            # fbanned users will have (2*number of fbans) less from max HP
            # Example: if HP is 100 but user has 5 diff fbans
            # Available HP is (2*5) = 10% less than Max HP
            # So.. 10% of 100HP = 90HP

    else:
        new_hp = no_by_per(total_hp, 5)

    return {
        "earnedhp": int(new_hp),
        "totalhp": int(total_hp),
        "percentage": get_percentage(total_hp, new_hp),
    }


def make_bar(per):
    done = min(round(per / 10), 10)
    return "■" * done + "□" * (10 - done)


async def get_id(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    msg = update.effective_message
    if user_id := extract_user(msg, args):

        if msg.reply_to_message and msg.reply_to_message.forward_from:

            user1 = message.reply_to_message.from_user
            user2 = message.reply_to_message.forward_from

            await msg.reply_text(
                f"➛ <b>Sender:</b> {mention_html(user2.id, user2.first_name)} - <code>{user2.id}</code>.\n"
                f"➛ <b>Forwarder:</b> {mention_html(user1.id, user1.first_name)} - <code>{user1.id}</code>.",
                parse_mode=ParseMode.HTML,
            )

        else:

            user = await bot.get_chat(user_id)
            await msg.reply_text(
                f"➛ <b>Replied to:</b> {mention_html(user.id, user.first_name)}\n➛ <b>ID of the user:</b> <code>{user.id}</code>",
                parse_mode=ParseMode.HTML,
            )

    elif chat.type == "private":
        await msg.reply_text(f"➛ Your id is <code>{chat.id}</code>.",
                             parse_mode=ParseMode.HTML)

    else:
        await msg.reply_text(
            f"➛ <b>User:</b> {mention_html(msg.from_user.id, msg.from_user.first_name)}\n➛ <b>From User ID:</b> <code>{update.effective_message.from_user.id}</code>\n➛ <b>This Group ID:</b> <code>{chat.id}</code>",
            parse_mode=ParseMode.HTML,
        )


@telethn.on(
    events.NewMessage(
        pattern="/ginfo ",
        from_users=(TIGER_USERS or []) + (SUDO_USERS or []) +
        (SUPPORT_USERS or []),
    ), )
async def group_info(event) -> None:
    chat = event.text.split(" ", 1)[1]
    try:
        entity = await event.client.get_entity(chat)
        totallist = await event.client.get_participants(
            entity,
            filter=ChannelParticipantsAdmins,
        )
        ch_full = await event.client(GetFullChannelRequest(channel=entity))
    except:
        await event.reply(
            "Can't for some reason, maybe it is a private one or that I am banned there.",
        )
        return
    msg = f"**ID**: `{entity.id}`"
    msg += f"\n**Title**: `{entity.title}`"
    msg += f"\n**Datacenter**: `{entity.photo.dc_id}`"
    msg += f"\n**Video PFP**: `{entity.photo.has_video}`"
    msg += f"\n**Supergroup**: `{entity.megagroup}`"
    msg += f"\n**Restricted**: `{entity.restricted}`"
    msg += f"\n**Scam**: `{entity.scam}`"
    msg += f"\n**Slowmode**: `{entity.slowmode_enabled}`"
    if entity.username:
        msg += f"\n**Username**: {entity.username}"
    msg += "\n\n**Member Stats:**"
    msg += f"\n`Admins:` `{len(totallist)}`"
    msg += f"\n`Users`: `{totallist.total}`"
    msg += "\n\n**Admins List:**"
    for x in totallist:
        msg += f"\n• [{x.id}](tg://user?id={x.id})"
    msg += f"\n\n**Description**:\n`{ch_full.full_chat.about}`"
    await event.reply(msg)


async def gifid(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    if await msg.reply_to_message and await msg.reply_to_message.animation:
        await update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.effective_message.reply_text(
            "Please reply to a gif to get its ID.")


"""
def info(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id and (user_id) != 777000 and (user_id) != 1087968824:
        user = await bot.get_chat(user_id)
         elif user_id and (user_id) == 777000:
            await message.reply_text(
                "This is Telegram. Unless you manually entered this reserved account's ID, it is likely a old broadcast from a linked channel."
                )
                return
         elif user_id and (user_id) == 1087968824:
                        await message.reply_text(
                            "This is Group Anonymous Bot. Unless you manually entered this reserved account's ID, it is likely a broadcast from a linked channel or anonymously sent message."
                            )
        return
        elif not message.reply_to_message and not args:
    user = (
            message.sender_chat
            if message.sender_chat is not None
            else message.from_user
        )

    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].isdigit()
            and notawait message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        delmsg = await message.reply_text("I can't extract a user from this.")

        cleartime = get_clearcmd(chat.id, "info")

        if cleartime:
            context.bot.run_async(delete, delmsg, cleartime.time)
return
else:return

    rep = await message.reply_text("<code>Checking Info...</code>", parse_mode=ParseMode.HTML)

    if hasattr(user, 'type') and user.type != "private":
        text = (
            f"<b>Chat Info: </b>"
            f"\nID: <code>{user.id}</code>"
            f"\nTitle: {user.title}"
        )
    if user.username:
      text += f"\nUsername: @{html.escape(user.username)}"
      text += f"\nChat Type: {user.type.capitalize()}"

    if INFOPIC:
            try:
                profile = bot.getChat(user.id).photo
                _file = await bot.get_file(profile["big_file_id"])
                _file.download(f"{user.id}.png")

                delmsg = message.reply_document(
                    document=open(f"{user.id}.png", "rb"),
                    caption=(text),
                    parse_mode=ParseMode.HTML,
                )

                os.remove(f"{user.id}.png")
            # Incase chat don't have profile pic, send normal text
            except:
                delmsg = await message.reply_text(
                    text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                )

        else:
            delmsg = await message.reply_text(
                text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            )
            else:
               text = (
                  f"╔═━「<b> Appraisal results:</b> 」\n"
                  f"ID: <code>{user.id}</code>\n"
                  f"First Name: {html.escape(user.first_name)}"
               )
               if user.username:
                  text += f"\nUsername: @{html.escape(user.username)}"
                  text += f"\nPermanent user link: {mention_html(user.id, 'link')}"
                  text += "\nNumber of profile pics: {}".format(
                     context.bot.get_user_profile_photos(user.id).total_count
                  )
                  if ChatType.PRIVATE and user_id != bot.id:
                     _stext = "\nStatus: <code>{}</code>"
                     afk_st = is_user_afk(user.id)
                     if afk_st:
                        text += _stext.format("AFK")
                        else:
                           status = bot.get_chat_member(chat.id, user.id).status
                           if status:
                              if status in {"left", "kicked"}:
                                 text += _stext.format("Not here")
                                 elif status == "member":
                                    text += _stext.format("Detected")
                                    elif status in {"administrator", "creator"}:
                                       text += _stext.format("Admin")
                                       if user_id not in [bot.id, 777000, 1087968824]:
                                          userhp = hpmanager(user)
                                          text += f"\n\n<b>Health:</b> <code>{userhp['earnedhp']}/{userhp['totalhp']}</code>\n[<i>{make_bar(int(userhp['percentage']))} </i>{userhp['percentage']}%]"
                                                # don't crash if api is down somehow...

    disaster_level_present = False

    if user.id == OWNER_ID:
        text += "\n\nUser level: <b>god</b>"

    elif user.id in DEV_USERS:
        text += "\n\nUser level: <b>developer</b>"

    elif user.id in SUDO_USERS:
        text += "\n\nUser level: <b>sudo</b>"

    elif user.id in SUPPORT_USERS:
        text += "\n\nUser level: <b>support</b>"

    elif user.id in WHITELIST_USERS:
        text += "\n\nUser level: <b>whitelist</b>"

    elif user.id == 1482952149:
         text += "\n\nCo-Owner Of A Bot. Queen Of @Awesome_RJ. Bot Name Inspired From 'Rabeeka'."


    if disaster_level_present:
        text += ' [<a href="https://telegram.dog/Black_Knights_Union/35">?</a>]'.format(
            await bot.username,
        )

    with contextlib.suppress(BadRequest):
        user_member = chat.get_member(user.id)
        if user_member.status == "administrator":
            result = requests.post(
                f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}",
            )
            result = result.json()["result"]
            if "custom_title" in result.keys():
                custom_title = result["custom_title"]
                text += f"\n\nTitle:\n<b>{custom_title}</b>"

    for mod in USER_INFO:
        try:
            mod_info = mod.__user_info__(user.id).strip()
        except TypeError:
            mod_info = mod.__user_info__(user.id, chat.id).strip()
        if mod_info:
            text += "\n\n" + mod_info

    if INFOPIC:
        try:

            profile = context.bot.get_user_profile_photos(user.id).photos[0][-1]
            await context.bot.sendChatAction(chat.id, "upload_photo")
            context.bot.reply_document(
                chat.id,
                photo=profile,
                caption=(text),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Health", url="https://t.me/Black_Knights_Union/33"
                            ),
                            InlineKeyboardButton(
                                "Disaster", url="https://t.me/Black_Knights_Union/35"
                            ),
                        ],
                        [
                            InlineKeyboardButton(" [❌] ", callback_data="close"),
                        ],
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        # Incase user don't have profile pic, send normal text
        except IndexError:
            await message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Health", url="https://t.me/Black_Knights_Union/33"
                            ),
                            InlineKeyboardButton(
                                "Disaster", url="https://t.me/Black_Knights_Union/35"
                            ),
                        ],
                        [
                            InlineKeyboardButton(" [❌] ", callback_data="close"),
                        ],
                    ]
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )

    else:
        await message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )

    rep.delete()

"""


async def info(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = extract_user(update.effective_message, args)

    if user_id and (user_id) != 777000 and (user_id) != 1087968824:
        user = await bot.get_chat(user_id)

    elif user_id and (user_id) == 777000:
        await message.reply_text(
            "This is Telegram. Unless you manually entered this reserved account's ID, it is likely a old broadcast from a linked channel."
        )
        return

    elif user_id:
        await message.reply_text(
            "This is Group Anonymous Bot. Unless you manually entered this reserved account's ID, it is likely a broadcast from a linked channel or anonymously sent message."
        )
        return

    elif not message.reply_to_message and not args:
        user = message.from_user

    elif not message.reply_to_message and (
            not args or
        (len(args) >= 1 and not args[0].startswith("@")
         and not args[0].lstrip("-").isdigit()
         and not await message.parse_entities([MessageEntity.TEXT_MENTION]))):
        delmsg = await message.reply_text("I can't extract a user from this.")

        if cleartime := get_clearcmd(chat.id, "info"):
            context.bot.run_async(delete, delmsg, cleartime.time)

        return

    else:
        return

    rep = await message.reply_text("<code>Appraising...</code>",
                                   parse_mode=ParseMode.HTML)

    if hasattr(user, 'type') and user.type != "private":
        text = (f"<b>Chat Info: </b>"
                f"\nID: <code>{user.id}</code>"
                f"\nTitle: {user.title}")
        if user.username:
            text += f"\nUsername: @{html.escape(user.username)}"
        text += f"\nChat Type: {user.type.capitalize()}"

        if INFOPIC:
            try:
                profile = bot.getChat(user.id).photo
                _file = await bot.get_file(profile["big_file_id"])
                _file.download(f"{user.id}.png")

                delmsg = message.reply_document(
                    document=open(f"{user.id}.png", "rb"),
                    caption=(text),
                    parse_mode=ParseMode.HTML,
                )

                os.remove(f"{user.id}.png")
            # Incase chat don't have profile pic, send normal text
            except:
                delmsg = await message.reply_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True)

        else:
            delmsg = await message.reply_text(text,
                                              parse_mode=ParseMode.HTML,
                                              disable_web_page_preview=True)

    else:
        text = (
            f"<b>╔═━「 User info: 」</b>\n"
            f"➛ ID: <code>{user.id}</code>\n"
            f"➛ First Name: {mention_html(user.id, user.first_name)} or '<code>Deleted Account</code>'"
        )

        if user.last_name:
            text += f"\n➛ Last Name: {html.escape(user.last_name)}"

        if user.username:
            text += f"\n➛ Username: @{html.escape(user.username)}"

        text += f"\n➛ Permalink: {mention_html(user.id, 'link')}"

        if ChatType.PRIVATE and user_id != bot.id:
            _stext = "\n➛ Status: <code>{}</code>"

            if afk_st := is_user_afk(user.id):
                text += _stext.format("AFK")
            elif status := bot.get_chat_member(chat.id, user.id).status:
                if status == "left":
                    text += _stext.format("Not here")
                if status == "kicked":
                    text += _stext.format("Banned")
                elif status == "member":
                    text += _stext.format("Detected")
                elif status in {"administrator", "creator"}:
                    text += _stext.format("Admin")

        if user.id == OWNER_ID:
            text += "\n\n➛ User level: <b>god</b>"

        elif user.id in DEV_USERS:
            text += "\n\n➛ User level: <b>developer</b>"

        elif user.id in SUDO_USERS:
            text += "\n\n➛ User level: <b>sudo</b>"

        elif user.id in SUPPORT_USERS:
            text += "\n\n➛ User level: <b>support</b>"

        elif user.id in WHITELIST_USERS:
            text += "\n\n➛ User level: <b>whitelist</b>"

        # if disaster_level_present:
        #     text += ' [<a href="https://t.me/OnePunchUpdates/155">?</a>]'.format(
        #         await bot.username)

        with contextlib.suppress(BadRequest):
            user_member = chat.get_member(user.id)
            if user_member.status == "administrator":
                result = requests.post(
                    f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={chat.id}&user_id={user.id}"
                )
                result = result.json().get("result")
                if "custom_title" in result.keys():
                    custom_title = result.get("custom_title")
                    text += f"\n\nAdmin Title:\n<b>{custom_title}</b>"

        for mod in USER_INFO:
            try:
                mod_info = mod.__user_info__(user.id).strip()
            except TypeError:
                mod_info = mod.__user_info__(user.id, chat.id).strip()
            if mod_info:
                text += "\n\n" + mod_info

        text += "\n\n" + biome(user.id)

        if INFOPIC:
            try:
                profile = context.bot.get_user_profile_photos(
                    user.id).photos[0][-1]
                _file = await bot.get_file(profile["file_id"])
                _file.download(f"{user.id}.png")

                delmsg = message.reply_document(
                    document=open(f"{user.id}.png", "rb"),
                    caption=(text),
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                "Health",
                                url="https://t.me/Black_Knights_Union/33"),
                            InlineKeyboardButton(
                                "Disaster",
                                url="https://t.me/Black_Knights_Union/35"),
                        ],
                        [
                            InlineKeyboardButton(" [❌] ",
                                                 callback_data="close"),
                        ],
                    ]),
                    parse_mode=ParseMode.HTML,
                )

                os.remove(f"{user.id}.png")
            # Incase user don't have profile pic, send normal text
            except IndexError:
                delmsg = await message.reply_text(
                    text,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton(
                                "Health",
                                url="https://t.me/Black_Knights_Union/33"),
                            InlineKeyboardButton(
                                "Disaster",
                                url="https://t.me/Black_Knights_Union/35"),
                        ],
                        [
                            InlineKeyboardButton(" [❌] ",
                                                 callback_data="close"),
                        ],
                    ]),
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )

        else:
            delmsg = await message.reply_text(text,
                                              parse_mode=ParseMode.HTML,
                                              disable_web_page_preview=True)

    rep.delete()


"""
    if cleartime := get_clearcmd(chat.id, "info"):
        context.bot.run_async(delete, delmsg, cleartime.time)
"""


async def about_me(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    user = await bot.get_chat(user_id) if user_id else message.from_user
    if info := sql.get_user_me_info(user.id):
        await update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        await update.effective_message.reply_text(
            f"{username} hasn't set an info message about themselves yet!", )
    else:
        await update.effective_message.reply_text(
            "There isnt one, use /setme to set one.")


async def about_me(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message
    user_id = extract_user(message, args)

    user = await bot.get_chat(user_id) if user_id else message.from_user
    if info := sql.get_user_me_info(user.id):
        await message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    elif update.effective_message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        await message.reply_text(
            f"{username} hasn't set an info message about themselves yet!", )
    else:
        await update.effective_message.reply_text(
            "There isnt one, use /setme to set one.")


async def set_about_me(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    user_id = message.from_user.id
    if user_id in [777000, 1087968824]:
        await update.effective_message.reply_text("Error! Forbidden")
        return
    bot = context.bot
    if update.effective_message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id in [bot.id, 777000, 1087968824] and (user_id
                                                             in DEV_USERS):
            user_id = repl_user_id
    text = message.text
    info = text.split(None, 1)
    if len(info) == 2:
        if len(info[1]) < MessageLimit.TEXT_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id in [777000, 1087968824]:
                await update.effective_message.reply_text(
                    "Authorized...Information updated!")
            elif user_id == bot.id:
                await update.effective_message.reply_text(
                    "I have updated my info with the one you provided!")
            else:
                await update.effective_message.reply_text(
                    "Information updated!")
        else:
            await message.reply_text(
                f"The info needs to be under {MessageLimit.TEXT_LENGTH // 4} characters! You have {len(info[1])}."
            )


async def about_bio(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message

    user_id = extract_user(message, args)
    user = await bot.get_chat(user_id) if user_id else message.from_user
    if info := sql.get_user_bio(user.id):
        await message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )

    elif update.effective_message.reply_to_message:
        username = user.first_name
        await message.reply_text(
            f"{username} hasn't had a message set about themselves yet!\nSet one using /setbio",
        )
    else:
        await message.reply_text(
            "You haven't had a bio set about yourself yet!", )


async def set_about_bio(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if update.effective_message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id

        if user_id == message.from_user.id:
            await message.reply_text(
                "Ha, you can't set your own bio! You're at the mercy of others here...",
            )
            return

        if user_id in [777000, 1087968824] and sender_id not in DEV_USERS:
            await update.effective_message.reply_text("You are not authorised")
            return

        if user_id == bot.id and sender_id not in DEV_USERS:
            await message.reply_text(
                "Erm... yeah, I only trust the Ackermans to set my bio.", )
            return

        text = message.text
        bio = text.split(
            None,
            1,
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MessageLimit.TEXT_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                await message.reply_text(
                    f"Updated {repl_message.from_user.first_name}'s bio!", )
            else:
                await message.reply_text(
                    f"Bio needs to be under {MessageLimit.TEXT_LENGTH // 4} characters! You tried to set {len(bio[1])}."
                )

    else:
        await update.effective_message.reply_text(
            "Reply to someone to set their bio!")


async def get_chat_info(chat, already=False):
    if not already:
        chat = await pgram.get_chat(chat)
    chat_id = chat.id
    username = chat.username
    title = chat.title
    type_ = chat.type
    is_scam = chat.is_scam
    description = chat.description
    members = chat.members_count
    is_restricted = chat.is_restricted
    link = f"[Link](t.me/{username})" if username else None
    dc_id = chat.dc_id
    photo_id = chat.photo.big_file_id if chat.photo else None
    body = {
        "ID": chat_id,
        "DC": dc_id,
        "Type": type_,
        "Name": [title],
        "Username": [f"@{username}" if username else None],
        "Mention": [link],
        "Members": members,
        "Scam": is_scam,
        "Restricted": is_restricted,
        "Description": [description],
    }

    caption = section("Chat info", body)
    return [caption, photo_id]


@pgram.on_message(filters.command("cinfo"))
async def chat_info_func(_, message: Message):
    try:
        if len(message.command) > 2:
            return await message.reply_text(
                "**Usage:**cinfo <chat id/username>")

        if len(message.command) == 1:
            chat = message.chat.id
        elif len(message.command) == 2:
            chat = message.text.split(None, 1)[1]

        m = await message.reply_text("Processing...")

        info_caption, photo_id = await get_chat_info(chat)
        if not photo_id:
            return await m.edit(info_caption, disable_web_page_preview=True)

        photo = await pgram.download_media(photo_id)
        await message.reply_photo(photo, caption=info_caption, quote=False)

        await m.delete()
        os.remove(photo)
    except Exception as e:
        await m.edit(e)


@telethn.on(events.NewMessage(pattern="^/gstat$"))
async def fk(m):
    lol = await m.client.send_message(m.chat.id, "Connecting To The Database")
    al = str((await ubot.get_messages(m.chat_id, limit=0)).total)
    ph = str((await
              ubot.get_messages(m.chat_id,
                                limit=0,
                                filter=InputMessagesFilterPhotos())).total)
    vi = str((await
              ubot.get_messages(m.chat_id,
                                limit=0,
                                filter=InputMessagesFilterVideo())).total)
    mu = str((await
              ubot.get_messages(m.chat_id,
                                limit=0,
                                filter=InputMessagesFilterMusic())).total)
    vo = str((await
              ubot.get_messages(m.chat_id,
                                limit=0,
                                filter=InputMessagesFilterVideo())).total)
    vv = str((await
              ubot.get_messages(m.chat_id,
                                limit=0,
                                filter=InputMessagesFilterRoundVideo())).total)
    do = str((await
              ubot.get_messages(m.chat_id,
                                limit=0,
                                filter=InputMessagesFilterDocument())).total)
    urls = str((await
                ubot.get_messages(m.chat_id,
                                  limit=0,
                                  filter=InputMessagesFilterUrl())).total)
    gifs = str((await
                ubot.get_messages(m.chat_id,
                                  limit=0,
                                  filter=InputMessagesFilterGif())).total)
    geos = str((await
                ubot.get_messages(m.chat_id,
                                  limit=0,
                                  filter=InputMessagesFilterGeo())).total)
    cont = str((await
                ubot.get_messages(m.chat_id,
                                  limit=0,
                                  filter=InputMessagesFilterContacts())).total)
    await asyncio.sleep(1)
    await lol.edit(
        ("✉️ Total Messages: {}\n" + "🖼 Total Photos: {}\n" +
         "📹 Total Video Messages: {}\n" + "🎵 Total music Messages : {}\n" +
         "🎶 Total Audio: {}\n" + "🎥 Total Videos: {}\n" +
         "📂 Total Files: {}\n" + "🔗 Total Links: {}\n" + "🎞 Total GIF: {}\n" +
         "🗺 Total Geo Messages: {}\n" + "👭 Total Contact files: {}").format(
             al, ph, vi, mu, vo, vv, do, urls, gifs, geos, cont))


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    result = ""
    if me:
        result += f"<b>About user:</b>\n{me}\n"
    if bio:
        result += f"<b>What others say:</b>\n{bio}\n"
    result = result.strip("\n")
    return result


__help__ = """
*ID:*
➛ /id*:* get the current group id. If used by replying to a message, gets that user's id.
➛ /gifid*:* reply to a gif to me to tell you its file ID.

*Self addded information:*
➛ /setme <text>*:* will set your info
➛ /me*:* will get your or another user's info.
Examples:
 `/setme I am a wolf.`
 `/me @username(defaults to yours if no user specified)`

*Information others add on you:*
➛ /bio*:* will get your or another user's bio. This cannot be set by yourself.
➛ /setbio <text>*:* while replying, will save another user's bio
Examples:
 `/bio @username(defaults to yours if not specified).`
 `/setbio This user is a wolf` (reply to the user)

*Overall Information about you:*
➛ /info*:* get information about a user.

*Remove Your Overall Information:*
➛ /gdpr: Deletes your information from the bot's database. Private chats only.

*◢ Intellivoid SpamProtection:*
➛ /spwinfo*:* SpamProtection Info

*json Detailed info:*
➛ /json*:* Get Detailed info about any message.

*Covid info:*
➛ /covid*:* Get Detailed info about Covid.

*ARQ Statistics:*
➛ /arq*:* ARQ API Stats.

*AFk:*
When marked as AFK, any mentions will be replied to with a message stating that you're not available!
➛ /afk <reason>*:* Mark yourself as AFK.
 - brb <reason>: Same as the afk command, but not a command.\n

*What is that health thingy?*
 Come and see [HP System explained](https://telegram.dog/Black_Knights_Union/33)

"""

CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("setbio", set_about_bio))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("bio", about_bio))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("id", get_id))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("gifid", gifid))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("info", info))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("setme", set_about_me))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("me", about_me))

__mod_name__ = "Info & AFK"
__command_list__ = ["setbio", "bio", "setme", "me", "info"]
