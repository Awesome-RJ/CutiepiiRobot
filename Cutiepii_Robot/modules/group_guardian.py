
import nude
import html
import asyncio
import better_profanity

from Cutiepii_Robot.modules.sql import cleaner_sql as sql
from Cutiepii_Robot.events import register

from telethon.tl import functions
from telethon import types, events
from better_profanity import profanity
from textblob import TextBlob

from Cutiepii_Robot import BOT_ID, MONGO_DB_URL, mongodb as db, telethn as tbot

CMD_HELP = {}

approved_users = db.approve
spammers = db.spammer
cleanservices = db.cleanservice
globalchat = db.globchat

CMD_STARTERS = '/'
profanity.load_censor_words_from_file('./profanity_wordlist.txt')

async def can_change_info(message):
    result = await tbot(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        )
    )
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (isinstance(
        p, types.ChannelParticipantAdmin) and p.admin_rights.change_info)


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (
                await tbot(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await tbot.get_peer_id(user)
        ps = (
            await tbot(functions.messages.GetFullChatRequest(chat.chat_id))
        ).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None

@register(pattern="^/profanity(?: |$)(.*)")
async def profanity(event):
    if event.fwd_from:
        return
    if event.is_private:
        return
    if MONGO_DB_URL is None:
        return
    if not await can_change_info(message=event):
        return
    input = event.pattern_match.group(1)
    chats = spammers.find({})
    if not input:
        for c in chats:
            if event.chat_id == c["id"]:
                await event.reply(
                    "Please provide some input yes or no.\n\nCurrent setting is : **on**"
                )
                return
        await event.reply(
            "Please provide some input yes or no.\n\nCurrent setting is : **off**"
        )
        return
    if input == "on":
        if event.is_group:
            chats = spammers.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    await event.reply(
                        "Profanity filter is already activated for this chat.")
                    return
            spammers.insert_one({"id": event.chat_id})
            await event.reply("Profanity filter turned on for this chat.")
    if input == "off":
        if event.is_group:  
            chats = spammers.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    spammers.delete_one({"id": event.chat_id})
                    await event.reply(
                        "Profanity filter turned off for this chat.")
                    return
        await event.reply(
                    "Profanity filter isn't turned on for this chat.")
    if not input == "on" and not input == "off":
        await event.reply("I only understand by on or off")
        return

@register(pattern="^/globalmode(?: |$)(.*)")
async def profanity(event):
    if event.fwd_from:
        return
    if event.is_private:
        return
    if MONGO_DB_URL is None:
        return
    if not await can_change_info(message=event):
        return
    input = event.pattern_match.group(1)
    chats = globalchat.find({})
    if not input:
        for c in chats:
            if event.chat_id == c["id"]:
                await event.reply(
                    "Please provide some input yes or no.\n\nCurrent setting is : **on**"
                )
                return
        await event.reply(
            "Please provide some input yes or no.\n\nCurrent setting is : **off**"
        )
        return
    if input == "on":
        if event.is_group:
            chats = globalchat.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    await event.reply(
                        "Global mode is already activated for this chat.")
                    return
            globalchat.insert_one({"id": event.chat_id})
            await event.reply("Global mode turned on for this chat.")
    if input == "off":
        if event.is_group:  
            chats = globalchat.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    globalchat.delete_one({"id": event.chat_id})
                    await event.reply(
                        "Global mode turned off for this chat.")
                    return
        await event.reply(
                    "Global mode isn't turned on for this chat.")
    if not input == "on" and not input == "off":
        await event.reply("I only understand by on or off")
        return


@register(pattern="^/cleanservice(?: |$)(.*)")
async def cleanservice(event):
    if event.fwd_from:
        return
    if event.is_private:
        return
    if MONGO_DB_URL is None:
        return
    if not await can_change_info(message=event):
        return
    input = event.pattern_match.group(1)
    chats = cleanservices.find({})
    if not input:
        for c in chats:
            if event.chat_id == c["id"]:
                await event.reply(
                    "Please provide some input yes or no.\n\nCurrent setting is : **on**"
                )
                return
        await event.reply(
            "Please provide some input yes or no.\n\nCurrent setting is : **off**"
        )
        return
    if input in "on":
        if event.is_group:
            chats = cleanservices.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    await event.reply(
                        "Clean service message already enabled for this chat.")
                    return
            cleanservices.insert_one({"id": event.chat_id})
            await event.reply("I will clean all service messages from now.")
    if input in "off":
        if event.is_group:
            chats = cleanservices.find({})
            for c in chats:
                if event.chat_id == c["id"]:
                    cleanservices.delete_one({"id": event.chat_id})
                    await event.reply(
                        "I will not clean service messages anymore.")
                    return
        await event.reply(
                    "Service message cleaning isn't turned on for this chat.")       
    
    if not input == "on" and not input == "off":
        await event.reply("I only understand by on or off")
        return

@tbot.on(events.NewMessage(pattern=None))
async def del_profanity(event):
    if event.is_private:
        return
    if MONGO_DB_URL is None:
        return
    msg = str(event.text)
    sender = await event.get_sender()
    # let = sender.username
    if event.is_group:
        if (await is_register_admin(event.input_chat, event.message.sender_id)):
            return
        pass
    chats = spammers.find({})
    for c in chats:
        if event.text:
            if event.chat_id == c['id']:
                if better_profanity.profanity.contains_profanity(msg):
                    await event.delete()
                    if sender.username is None:
                        st = sender.first_name
                        hh = sender.id
                        final = f"[{st}](tg://user?id={hh}) **{msg}** is detected as a slang word and your message has been deleted"
                    else:
                        final = f'sir **{msg}** is detected as a slang word and your message has been deleted'
                    dev = await event.respond(final)
                    await asyncio.sleep(10)
                    await dev.delete()
        if event.photo:
            if event.chat_id == c['id']:
                await event.client.download_media(event.photo, "nudes.jpg")
                if nude.is_nude('./nudes.jpg'):
                    await event.delete()
                    st = sender.first_name
                    hh = sender.id
                    final = f"[{st}](tg://user?id={hh}) you should only speak in english here !"
                    dev = await event.respond(final)
                    await asyncio.sleep(10)
                    await dev.delete()
                    os.remove("nudes.jpg")

@tbot.on(events.NewMessage(pattern=None))
async def del_profanity(event):
    if event.is_private:
        return
    if MONGO_DB_URL is None:
        return
    msg = str(event.text)
    sender = await event.get_sender()
    # let = sender.username
    if event.is_group:
        if (await is_register_admin(event.input_chat, event.message.sender_id)):
            return
        pass
    chats = globalchat.find({})
    for c in chats:
        if event.text:
            if event.chat_id == c['id']:
                a = TextBlob(msg)
                b = a.detect_language()
                if not b == "en":
                    await event.delete()                   
                    st = sender.first_name
                    hh = sender.id
                    final = f"[{st}](tg://user?id={hh}) you should only speak in english here !"
                    dev = await event.respond(final)
                    await asyncio.sleep(10)
                    await dev.delete()


@tbot.on(events.ChatAction())
async def del_cleanservice(event):
    chats = cleanservices.find({})
    for c in chats:
      if event.chat_id == c['id']:       
       try:       
        await event.delete()
       except Exception as e:
        print(e)

file_help = os.path.basename(__file__)
file_help = file_help.replace(".py", "")
file_helpo = file_help.replace("_", " ")

__help__ = """
 - /profanity on/off: filters all explict/abusive words sent by non admins also filters explicit/porn images
 - /cleanservice on/off: cleans all service messages from telegram
 - /globalmode: let users only speak in english in your group (automatically deletes messages in other languages)
"""

CMD_HELP.update({
    file_helpo: [
        file_helpo,
        __help__
    ]
})
