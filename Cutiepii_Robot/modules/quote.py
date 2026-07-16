import os
import base64
import random
import aiohttp
from PIL import Image
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from telethon.tl import types
from telethon.utils import get_display_name, get_peer_id

from Cutiepii_Robot import LOGGER, dispatcher, telethn
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

# Mappings of Telethon entity types to Quotly API entity type strings
ENTITY_MAPPING_TELETHON = {
    types.MessageEntityPhone: "phone_number",
    types.MessageEntityMention: "mention",
    types.MessageEntityBold: "bold",
    types.MessageEntityCashtag: "cashtag",
    types.MessageEntityStrike: "strikethrough",
    types.MessageEntityHashtag: "hashtag",
    types.MessageEntityEmail: "email",
    types.MessageEntityMentionName: "text_mention",
    types.MessageEntityUnderline: "underline",
    types.MessageEntityUrl: "url",
    types.MessageEntityTextUrl: "text_link",
    types.MessageEntityBotCommand: "bot_command",
    types.MessageEntityCode: "code",
    types.MessageEntityPre: "pre",
}

BG_COLORS = ["#1b1429", "#FFFFFF", "#FF5733", "#33FF57", "#3357FF"]

async def upload_to_telegraph(file_path: str) -> str:
    png_path = file_path + ".png"
    try:
        with Image.open(file_path) as img:
            img.save(png_path, "PNG")
        
        async with aiohttp.ClientSession() as session:
            with open(png_path, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='file.png', content_type='image/png')
                async with session.post("https://telegra.ph/upload", data=data) as response:
                    if response.status == 200:
                        res = await response.json()
                        if isinstance(res, list) and len(res) > 0:
                            return "https://telegra.ph" + res[0]["src"]
    except Exception as e:
        LOGGER.error(f"Failed to upload to Telegraph: {e}")
    finally:
        if os.path.exists(png_path):
            os.remove(png_path)
    return ""

async def format_telethon_message(msg, reply=None, sender=None, type_="private") -> dict:
    reply_data = {}
    if reply:
        display_name = get_display_name(reply.sender) or "Deleted Account"
        username = getattr(reply.sender, "username", None)
        
        rank = ""
        if reply.chat_id and reply.sender_id:
            from telethon.tl.functions.channels import GetParticipantRequest
            from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator
            try:
                participant = await telethn(GetParticipantRequest(reply.chat_id, reply.sender_id))
                p = participant.participant
                if isinstance(p, (ChannelParticipantAdmin, ChannelParticipantCreator)) and p.rank:
                    rank = p.rank
            except Exception:
                pass
                
        extra = []
        if rank:
            extra.append(rank)
        if username:
            extra.append(f"@{username}")
            
        if extra:
            display_name = f"{display_name} ({', '.join(extra)})"

        reply_data = {
            "name": display_name,
            "text": reply.raw_text or "",
            "chatId": reply.chat_id,
        }

    is_fwd = msg.fwd_from
    name = None
    last_name = None
    sender_obj = None
    
    if sender:
        id_ = get_peer_id(sender)
        name = get_display_name(sender)
    elif not is_fwd:
        id_ = msg.sender_id
        try:
            sender_obj = await msg.get_sender()
            name = get_display_name(sender_obj)
        except Exception:
            pass
    else:
        id_, sender_obj = None, None
        name = is_fwd.from_name
        if is_fwd.from_id:
            id_ = get_peer_id(is_fwd.from_id)
            try:
                sender_obj = await telethn.get_entity(id_)
                name = get_display_name(sender_obj)
            except ValueError:
                pass

    if not id_:
        id_ = msg.chat_id

    if sender_obj and hasattr(sender_obj, "last_name"):
        last_name = sender_obj.last_name

    entities = []
    if msg.entities:
        for entity in msg.entities:
            if type(entity) in ENTITY_MAPPING_TELETHON:
                enti_ = entity.to_dict()
                if "_" in enti_:
                    del enti_["_"]
                enti_["type"] = ENTITY_MAPPING_TELETHON[type(entity)]
                entities.append(enti_)

    formatted = {
        "entities": entities,
        "chatId": id_,
        "avatar": True,
        "from": {
            "id": id_,
            "first_name": name or "Deleted Account",
            "last_name": last_name,
            "username": sender_obj.username if sender_obj and hasattr(sender_obj, 'username') else None,
            "language_code": "en",
            "title": name,
            "name": name or "Unknown",
            "type": type_,
        },
        "text": msg.raw_text or "",
        "replyMessage": reply_data,
    }

    # Handle media/photos
    if msg.media:
        try:
            file_path = await msg.download_media()
            if file_path and os.path.exists(file_path):
                uri = await upload_to_telegraph(file_path)
                if uri:
                    formatted["media"] = {"url": uri}
                os.remove(file_path)
        except Exception as e:
            LOGGER.error(f"Error quoting telethon media: {e}")

    return formatted

    return formatted


def parse_quote_args(args_list):
    is_png = False
    is_story = False
    is_anon = False
    force_reply = False
    
    clean_args = []
    for arg in args_list:
        arg_lower = arg.lower()
        if arg_lower in ("!png", "!file"):
            is_png = True
        elif arg_lower in ("!stories", "!story"):
            is_story = True
        elif arg_lower in ("!anon", "!hide"):
            is_anon = True
        elif arg_lower in ("!reply", "r"):
            force_reply = True
        else:
            clean_args.append(arg)
            
    bg_color = "#1b1429"
    emoji_brand = "apple"
    scale = 2
    count = 1
    leftover_text = []
    
    for arg in clean_args:
        if arg.isdigit():
            count = min(max(int(arg), 1), 20)
        elif arg.lower() == "random":
            bg_color = random.choice(BG_COLORS)
        elif arg.startswith("#"):
            bg_color = arg
        elif arg.lower() in ("apple", "google", "twitter", "blob", "joypixels"):
            emoji_brand = arg.lower()
        elif arg.lower().startswith("s") and len(arg) > 1:
            try:
                scale = float(arg[1:])
            except ValueError:
                leftover_text.append(arg)
        else:
            leftover_text.append(arg)
                
    return is_png, is_story, is_anon, force_reply, bg_color, emoji_brand, scale, count, " ".join(leftover_text)


@cutiepii_cmd(command=["q", "qr"])
async def quote_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if not message.reply_to_message:
        await message.reply_text("Reply to a message to quote it!")
        return

    progress = await message.reply_text("`Creating Quote...`", parse_mode=ParseMode.MARKDOWN)

    # Parse args
    is_png, is_story, is_anon, force_reply, bg_color, emoji_brand, scale, count, _ = parse_quote_args(context.args)
    if message.text.split()[0].lower().endswith("qr"):
        force_reply = True

    try:
        reply_to_id = message.reply_to_message.message_id
        
        reply_msgs = []
        if count > 1:
            for msg_id in range(reply_to_id, reply_to_id + count):
                try:
                    t_msg = await telethn.get_messages(message.chat_id, ids=msg_id)
                    if t_msg:
                        reply_msgs.append(t_msg)
                except Exception as e:
                    LOGGER.warning(f"Failed to fetch message {msg_id}: {e}")
        else:
            t_msg = await telethn.get_messages(message.chat_id, ids=reply_to_id)
            if t_msg:
                reply_msgs.append(t_msg)

        if not reply_msgs:
            await progress.edit_text("Could not fetch the message to quote.")
            return

        reply_ref = None
        if force_reply and len(reply_msgs) == 1:
            first_msg = reply_msgs[0]
            if first_msg.is_reply:
                try:
                    reply_ref = await first_msg.get_reply_message()
                except Exception:
                    pass

        messages_payload = []
        for r_msg in reply_msgs:
            formatted = await format_telethon_message(r_msg, reply=reply_ref)
            if is_anon:
                formatted["from"]["first_name"] = "Anonymous Hunter"
                formatted["from"]["last_name"] = ""
                formatted["from"]["username"] = None
                formatted["from"]["name"] = "Anonymous Hunter"
                formatted["from"]["title"] = "Anonymous Hunter"
                formatted["avatar"] = False
            messages_payload.append(formatted)

        payload = {
            "type": "quote",
            "format": "png" if is_png else "webp",
            "backgroundColor": bg_color,
            "emojiBrand": emoji_brand,
            "width": 720 if is_story else 512,
            "height": 1280 if is_story else 768,
            "scale": scale,
            "messages": messages_payload
        }

        api_urls = [
            "https://quote.yuri.ly/generate",
            "https://bot.lyo.su/quote/generate",
            "https://qoute-api-akashpattnaik.koyeb.app/generate"
        ]
        
        quote_file = None
        ext = "png" if is_png else "webp"
        async with aiohttp.ClientSession() as session:
            for api_url in api_urls:
                try:
                    async with session.post(api_url, json=payload, ssl=False) as response:
                        if response.status == 200:
                            res = await response.json()
                            if res.get("ok"):
                                image_data = base64.b64decode(res["result"]["image"])
                                quote_file = f"quote_{reply_to_id}.{ext}"
                                with open(quote_file, "wb") as f:
                                    f.write(image_data)
                                break
                except Exception as e:
                    LOGGER.warning(f"Failed to fetch from {api_url}: {e}")

        if quote_file and os.path.exists(quote_file):
            with open(quote_file, "rb") as f:
                if is_png:
                    await message.reply_document(document=f, filename=quote_file)
                else:
                    await message.reply_sticker(sticker=f)
            os.remove(quote_file)
            await progress.delete()
        else:
            await progress.edit_text("Failed to create quote.")

    except Exception as e:
        LOGGER.exception(f"Error in Quotly: {e}")
        await progress.edit_text(f"Error generating quote: {str(e)}")


@cutiepii_cmd(command="fq")
async def fake_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not context.args:
        await message.reply_text("Usage: `/fq [text]` or `/fq [color] [emojiBrand] [sScale] [text]` (reply to target user required or fakes yourself).")
        return
        
    is_png, is_story, is_anon, force_reply, bg_color, emoji_brand, scale, count, text = parse_quote_args(context.args)
    if not text:
        await message.reply_text("Please provide message text for the fake quote!")
        return

    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = message.from_user

    sender_id = target_user.id
    first_name = target_user.first_name
    last_name = target_user.last_name or ""
    username = target_user.username

    if is_anon:
        first_name = "Anonymous Hunter"
        last_name = ""
        username = None

    formatted = {
        "entities": [],
        "chatId": sender_id,
        "avatar": not is_anon,
        "from": {
            "id": sender_id,
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "language_code": "en",
            "title": first_name,
            "name": first_name,
            "type": "private",
        },
        "text": text,
        "replyMessage": {},
    }

    progress = await message.reply_text("`Generating Fake Quote...`", parse_mode=ParseMode.MARKDOWN)

    try:
        payload = {
            "type": "quote",
            "format": "png" if is_png else "webp",
            "backgroundColor": bg_color,
            "emojiBrand": emoji_brand,
            "width": 720 if is_story else 512,
            "height": 1280 if is_story else 768,
            "scale": scale,
            "messages": [formatted]
        }

        api_urls = [
            "https://quote.yuri.ly/generate",
            "https://bot.lyo.su/quote/generate",
            "https://qoute-api-akashpattnaik.koyeb.app/generate"
        ]
        
        quote_file = None
        ext = "png" if is_png else "webp"
        async with aiohttp.ClientSession() as session:
            for api_url in api_urls:
                try:
                    async with session.post(api_url, json=payload, ssl=False) as response:
                        if response.status == 200:
                            res = await response.json()
                            if res.get("ok"):
                                image_data = base64.b64decode(res["result"]["image"])
                                quote_file = f"fake_quote_{sender_id}.{ext}"
                                with open(quote_file, "wb") as f:
                                    f.write(image_data)
                                break
                except Exception as e:
                    LOGGER.warning(f"Failed to fetch from {api_url}: {e}")

        if quote_file and os.path.exists(quote_file):
            with open(quote_file, "rb") as f:
                if is_png:
                    await message.reply_document(document=f, filename=quote_file)
                else:
                    await message.reply_sticker(sticker=f)
            os.remove(quote_file)
            await progress.delete()
        else:
            await progress.edit_text("Failed to create fake quote.")

    except Exception as e:
        LOGGER.exception(f"Error in Fake Quotly: {e}")
        await progress.edit_text(f"Error generating fake quote: {str(e)}")


__mod_name__ = "Quotly"

__help__ = True
