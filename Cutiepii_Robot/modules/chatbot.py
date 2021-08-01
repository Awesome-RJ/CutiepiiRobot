import re
import emoji
import aiohttp

# from google_trans_new import google_translator
from googletrans import Translator as google_translator
from pyrogram import filters

from Cutiepii_Robot.modules.mongo.chatbot_mongo import add_chat, get_session, remove_chat
from Cutiepii_Robot.utils.pluginhelp import admins_only, edit_or_reply
from Cutiepii_Robot import pgram as cutiepii, BOT_ID, BOT_USERNAME, arq 

translator = google_translator()
url = "https://acobot-brainshop-ai-v1.p.rapidapi.com/get"

async def lunaQuery(query: str, user_id: int):
    luna = await arq.luna(query, user_id)
    return luna.result


def extract_emojis(s):
    return "".join(c for c in s if c in emoji.UNICODE_EMOJI)


async def fetch(url):
    try:
        async with aiohttp.Timeout(10.0):
            async with aiohttp.ClientSession() as session, session.get(url) as resp:
                try:
                    data = await resp.json()
                except:
                    data = await resp.text()
            return data
    except:
        print("AI response Timeout")
        return


cutie_chats = []
en_chats = []


@cutiepii.on_message(
    filters.command(["chatbot", f"chatbot@{BOT_USERNAME}"]) & ~filters.edited & ~filters.bot & ~filters.private
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

    elif status == "EN" or status == "en" or status == "english":
        if not chat_id in en_chats:
            en_chats.append(chat_id)
            await message.reply_text("English AI chat Enabled!")
            return
        await message.reply_text("AI Chat Is Already Disabled.")
        message.continue_propagation()
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
async def hmm(_, message):
    if not get_session(int(message.chat.id)):
        return
    if not message.reply_to_message:
        return
    try:
        senderr = message.reply_to_message.from_user.id
    except:
        return
    if senderr != BOT_ID:
        return
    msg = message.text
    pro = await fetch(f"https://yukicloud.tk/Kuki/chatbot?message={msg}")
    pro = pro['reply']
    await cutiepii.send_chat_action(message.chat.id, "typing")
    await message.reply_text(pro)
__help__ = """
 Chatbot utilizes the Brainshop's API and allows Cutiepii to talk and provides a more interactive group chat experience.
 *Admins Only Commands*:
  ➢ `/chatbot [ON/OFF]`: Enables and disables Chatbot mode in the chat.
  ➢ `/chatbot EN` : Enables English only Chatbot mode in the chat.
 *Powered by Brainshop* (brainshop.ai)
"""

__mod_name__ = "ChatBot"
