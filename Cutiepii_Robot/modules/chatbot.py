import emoji
import re
import aiohttp
from google_trans_new import google_translator
from pyrogram import filters

from Cutiepii_Robot import BOT_ID
from Cutiepii_Robot.modules.mongo.chatbot_mongo import add_chat, get_session, remove_chat
from Cutiepii_Robot import arq
from Cutiepii_Robot.functions.pluginhelpers import admins_only, edit_or_reply
from Cutiepii_Robot import pgram as cutiepii

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
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    try:
                        data = await resp.json()
                    except:
                        data = await resp.text()
            return data
    except:
        print("AI response Timeout")
        return

cutiepii_chats = []
en_chats = []


@cutiepii.on_message(
    filters.command("chatbot") & ~filters.edited & ~filters.bot & ~filters.private
)
@admins_only
async def chatbot_status(_, message):
    global cutiepii_chats
    if len(message.command) != 2:
        await message.reply_text(
            "I only recognize `/chatbot on` and `/chatbot off` only"
        )
        message.continue_propagation()
    status = message.text.split(None, 1)[1]
    chat_id = message.chat.id
    if status == "ON" or status == "on" or status == "On":
        lel = await edit_or_reply(message, "`Processing...`")
        lol = add_chat(int(message.chat.id))
        if not lol:
            await lel.edit("AI is Already enabled In This Chat")
            return
        await lel.edit(
            f"AI Successfully Enabled For this Chat"
        )

    elif status == "OFF" or status == "off" or status == "Off":
        lel = await edit_or_reply(message, "`Processing...`")
        Escobar = remove_chat(int(message.chat.id))
        if not Escobar:
            await lel.edit("AI Was Not Enabled In This Chat")
            return
        await lel.edit(
            f" Successfully Disabled AI For This Chat"
        )

    elif status == "EN" or status == "en" or status == "english":
        if not chat_id in en_chats:
            en_chats.append(chat_id)
            await message.reply_text("English Only AI Enabled!")
            return
        await message.reply_text("English Only AI Is Already Enabled in this chat.")
        message.continue_propagation()
    else:
        await message.reply_text(
            "I only recognize `/chatbot on` and `/chatbot off` only"
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
async def chatbot_function(client, message):
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
    chat_id = message.chat.id
    if msg.startswith("/") or msg.startswith("@"):
        message.continue_propagation()
    if chat_id in en_chats:
        test = msg
        test = test.replace("Aco", "Cutiepii")
        test = test.replace("aco", "cutiepii")
        response = await lunaQuery(
            test, message.from_user.id if message.from_user else 0
        )
        response = response.replace("aco", "cutiepii")
        response = response.replace("Aco", "Cutiepii")
        response = response.replace("Luna", "Cutiepii")
        response = response.replace("Luna", "cutiepii")
        response = response.replace("female", "male")

        pro = response
        try:
            await cutiepii.send_chat_action(message.chat.id, "typing")
            await message.reply_text(pro)
        except CFError:
            return

    else:
        u = msg.split()
        emj = extract_emojis(msg)
        msg = msg.replace(emj, "")
        if (
            [(k) for k in u if k.startswith("@")]
            and [(k) for k in u if k.startswith("#")]
            and [(k) for k in u if k.startswith("/")]
            and re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []
        ):

            h = " ".join(filter(lambda x: x[0] != "@", u))
            km = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", h)
            tm = km.split()
            jm = " ".join(filter(lambda x: x[0] != "#", tm))
            hm = jm.split()
            rm = " ".join(filter(lambda x: x[0] != "/", hm))
        elif [(k) for k in u if k.startswith("@")]:

            rm = " ".join(filter(lambda x: x[0] != "@", u))
        elif [(k) for k in u if k.startswith("#")]:
            rm = " ".join(filter(lambda x: x[0] != "#", u))
        elif [(k) for k in u if k.startswith("/")]:
            rm = " ".join(filter(lambda x: x[0] != "/", u))
        elif re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []:
            rm = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", msg)
        else:
            rm = msg
            # print (rm)
        try:
            lan = translator.detect(rm)
        except:
            return
        test = rm
        if not "en" in lan and not lan == "":
            try:
                test = translator.translate(test, lang_tgt="en")
            except:
                return
        # test = emoji.demojize(test.strip())

        test = test.replace("Cutiepii", "aco")
        test = test.replace("cutiepii", "aco")
        
        response = await lunaQuery(
            test, message.from_user.id if message.from_user else 0
        )
        response = response.replace("aco", "Cutiepii")
        response = response.replace("Aco", "cutiepii")
        response = response.replace("Luna", "Cutiepii")
        response = response.replace("Luna", "cutiepii")
        response = response.replace("female", "male")

        pro = response
        if not "en" in lan and not lan == "":
            try:
                pro = translator.translate(pro, lang_tgt=lan[0])
            except:
                return
        try:
            await cutiepii.send_chat_action(message.chat.id, "typing")
            await message.reply_text(pro)
        except CFError:
            return


@cutiepii.on_message(
    filters.text & filters.private & ~filters.edited & filters.reply & ~filters.bot
)
async def sasuke(client, message):
    msg = message.text
    if msg.startswith("/") or msg.startswith("@"):
        message.continue_propagation()
    u = msg.split()
    emj = extract_emojis(msg)
    msg = msg.replace(emj, "")
    if (
        [(k) for k in u if k.startswith("@")]
        and [(k) for k in u if k.startswith("#")]
        and [(k) for k in u if k.startswith("/")]
        and re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []
    ):

        h = " ".join(filter(lambda x: x[0] != "@", u))
        km = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", h)
        tm = km.split()
        jm = " ".join(filter(lambda x: x[0] != "#", tm))
        hm = jm.split()
        rm = " ".join(filter(lambda x: x[0] != "/", hm))
    elif [(k) for k in u if k.startswith("@")]:

        rm = " ".join(filter(lambda x: x[0] != "@", u))
    elif [(k) for k in u if k.startswith("#")]:
        rm = " ".join(filter(lambda x: x[0] != "#", u))
    elif [(k) for k in u if k.startswith("/")]:
        rm = " ".join(filter(lambda x: x[0] != "/", u))
    elif re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []:
        rm = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", msg)
    else:
        rm = msg
        # print (rm)
    try:
        lan = translator.detect(rm)
    except:
        return
    test = rm
    if not "en" in lan and not lan == "":
        try:
            test = translator.translate(test, lang_tgt="en")
        except:
            return

    # test = emoji.demojize(test.strip())

    # Kang with the credits bitches @InukaASiTH
    test = test.replace("aco", "Cutiepii")
    test = test.replace("aco", "cutiepii")    
    
    response = await lunaQuery(test, message.from_user.id if message.from_user else 0)
    response = response.replace("Aco", "Cutiepii")
    response = response.replace("aco", "cutiepii")
    response = response.replace("Luna", "Cutiepii")
    response = response.replace("Luna", "cutiepii")
    response = response.replace("female", "male")

    pro = response
    if not "en" in lan and not lan == "":
        pro = translator.translate(pro, lang_tgt=lan[0])
    try:
        await cutiepii.send_chat_action(message.chat.id, "typing")
        await message.reply_text(pro)
    except CFError:
        return


@cutiepii.on_message(
    filters.regex("Cutiepii")
    & ~filters.bot
    & ~filters.via_bot
    & ~filters.forwarded
    & ~filters.reply
    & ~filters.channel
    & ~filters.edited
)
async def sasuke(client, message):
    msg = message.text
    if msg.startswith("/") or msg.startswith("@"):
        message.continue_propagation()
    u = msg.split()
    emj = extract_emojis(msg)
    msg = msg.replace(emj, "")
    if (
        [(k) for k in u if k.startswith("@")]
        and [(k) for k in u if k.startswith("#")]
        and [(k) for k in u if k.startswith("/")]
        and re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []
    ):

        h = " ".join(filter(lambda x: x[0] != "@", u))
        km = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", h)
        tm = km.split()
        jm = " ".join(filter(lambda x: x[0] != "#", tm))
        hm = jm.split()
        rm = " ".join(filter(lambda x: x[0] != "/", hm))
    elif [(k) for k in u if k.startswith("@")]:

        rm = " ".join(filter(lambda x: x[0] != "@", u))
    elif [(k) for k in u if k.startswith("#")]:
        rm = " ".join(filter(lambda x: x[0] != "#", u))
    elif [(k) for k in u if k.startswith("/")]:
        rm = " ".join(filter(lambda x: x[0] != "/", u))
    elif re.findall(r"\[([^]]+)]\(\s*([^)]+)\s*\)", msg) != []:
        rm = re.sub(r"\[([^]]+)]\(\s*([^)]+)\s*\)", r"", msg)
    else:
        rm = msg
        # print (rm)
    try:
        lan = translator.detect(rm)
    except:
        return
    test = rm
    if not "en" in lan and not lan == "":
        try:
            test = translator.translate(test, lang_tgt="en")
        except:
            return

    # test = emoji.demojize(test.strip())

    test = test.replace("Aco", "Cutiepii")
    test = test.replace("aco", "cutiepii")
    response = await lunaQuery(test, message.from_user.id if message.from_user else 0)
    response = response.replace("Aco", "Cutiepii")
    response = response.replace("aco", "cutiepii")
    response = response.replace("Luna", "Cutiepii")
    response = response.replace("Luna", "cutiepii")
    response = response.replace("female", "male")

    pro = response
    if not "en" in lan and not lan == "":
        try:
            pro = translator.translate(pro, lang_tgt=lan[0])
        except Exception:
            return
    try:
        await cutiepii.send_chat_action(message.chat.id, "typing")
        await message.reply_text(pro)
    except CFError:
        return


__help__ = """
 Chatbot utilizes the Branshop's API and allows Cutiepii to talk and provides a more interactive group chat experience.
 *Admins Only Commands*:
 • `/chatbot [ON/OFF]`: Enables and disables Chatbot mode in the chat.
 • `/chatbot EN` : Enables English only Chatbot mode in the chat.
 *Powered by Brainshop* (brainshop.ai)
"""

__mod_name__ = "ChatBot"
