import re
import emoji
import aiohttp
import requests

from pyrogram import filters

from Cutiepii_Robot.modules.mongo.chatbot_mongo import add_chat, get_session, remove_chat
from Cutiepii_Robot.utils.pluginhelp import admins_only, edit_or_reply
from Cutiepii_Robot import pgram as cutiepii, BOT_ID, BOT_USERNAME


cutie_chats = []
en_chats = []


@cutiepii.on_message(
    filters.command(["chatbot", f"chatbot@{BOT_USERNAME}"]) & ~filters.edited & ~filters.bot & filters.private
)
@admins_only
async def hmm(_, message):
    global cutie_chats
    if len(message.command) != 2:
        await message.reply_text(
            "I only recognize `/chatbot on` and /chatbot `off only`"
        )
        message.continue_propagation()
    status = message.text.split(None, 1)[1]
    chat_id = message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await edit_or_reply(message, "`Processing...`")
        lol = add_chat(int(message.chat.id))
        if not lol:
            await lel.edit("cutie AI Already Activated In This Chat")
            return
        await lel.edit(
            f"cutie AI Successfully Added For Users In The Chat {message.chat.id}"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await edit_or_reply(message, "`Processing...`")
        Escobar = remove_chat(int(message.chat.id))
        if not Escobar:
            await lel.edit("cutie AI Was Not Activated In This Chat")
            return
        await lel.edit(
            f"cutie AI Successfully Deactivated For Users In The Chat {message.chat.id}"
        )
    else:
        await message.reply_text(
            "I only recognize `/chatbot on` and /chatbot `off only`"
        )


@cutiepii.on_message(
    filters.text
    & filters.reply
    & ~filters.bot
    & ~filters.edited
    & ~filters.via_bot
    & ~filters.forwarded,
    group=2,
)
async def kuki(_, message):
    if not get_session(int(message.chat.id)):
        return
    if not message.reply_to_message:
        return
    try:
        moe = message.reply_to_message.from_user.id
    except:
        return
    if moe != BOT_ID:
        return
    msg = message.text
    Kuki = requests.get(f"https://kuki-yukicloud.up.railway.app/Kuki/chatbot?message={msg}").json()
    moezilla = f"{Kuki['reply']}"
    if "Cutiepii" in msg or "cutiepii" in msg or "CUTIEPII" in msg:
    await cutiepii.send_chat_action(message.chat.id, "typing")
    await message.reply_text(moezilla) 

__help__ = """
 Chatbot utilizes the Kuki's API and allows Cutiepii to talk and provides a more interactive group chat experience.
 *Admins Only Commands*:
  ➢ `/chatbot [ON/OFF]`: Enables and disables Chatbot mode in the chat.
  ➢ `/chatbot EN` : Enables English only Chatbot mode in the chat.
 *Powered by KukiChatBot* (@kukichatbot)
"""

__mod_name__ = "ChatBot"
