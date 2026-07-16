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

import glob
import io
import os
import re
import urllib
import urllib.request
import bs4
import requests
from asyncio import sleep

from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from datetime import datetime
from requests import get, post
from bs4 import BeautifulSoup
from bing_image_downloader import downloader
from PIL import Image
from geopy.geocoders import Nominatim
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from telethon.tl import functions, types
from telethon import *
from telethon.tl.types import *
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telethon.tl.custom import Message
from gpytranslate import SyncTranslator


from Cutiepii_Robot import telethn, BOT_NAME, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import register

async def google_search(query):
    import urllib.parse
    import httpx
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
    
    try:
        async with httpx.AsyncClient(headers=headers, timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                results = []
                for r in soup.find_all("div", class_="result"):
                    classes = r.get("class", [])
                    if "result--ad" in classes:
                        continue
                    title_tag = r.find("a", class_="result__url")
                    snippet_tag = r.find("a", class_="result__snippet")
                    if title_tag and title_tag.get("href"):
                        title = title_tag.text.strip()
                        link = title_tag.get("href")
                        if "duckduckgo.com/y.js" in link:
                            continue
                        if "uddg=" in link:
                            link = urllib.parse.unquote(link.split("uddg=")[1].split("&")[0])
                        snippet = snippet_tag.text.strip() if snippet_tag else ""
                        results.append({
                            "title": title,
                            "link": link,
                            "description": snippet
                        })
                        if len(results) >= 5:
                            break
                return results
    except Exception as e:
        LOGGER.error(f"Error in google_search: {e}")
    return []


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):
        ui = await telethn.get_peer_id(user)
        ps = (
            await telethn(functions.messages.GetFullChatRequest(chat.chat_id))
        ).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None


@register(pattern="gps")
async def gps(event):
    if event.fwd_from:
        return
    if (
        event.is_group
        and not await is_register_admin(event.input_chat, event.message.sender_id)
    ):
        await event.reply(
            "<b>Action Denied</b>\nYou must be an administrator to perform this action in a group chat.",
            parse_mode="html"
        )
        return

    args = event.pattern_match.group(1)

    try:
        geolocator = Nominatim(user_agent="SkittBot")
        location = args
        geoloc = geolocator.geocode(location)
        longitude = geoloc.longitude
        latitude = geoloc.latitude
        gm = "https://www.google.com/maps/search/{},{}".format(latitude, longitude)
        await telethn.send_file(
            event.chat_id,
            file=types.InputMediaGeoPoint(
                types.InputGeoPoint(float(latitude), float(longitude))
            ),
        )
        await event.reply(
            "<b>Location Found</b>\nView on <a href='{}'>Google Maps</a>".format(gm),
            parse_mode="html",
            link_preview=False,
        )
    except Exception as e:
        LOGGER.debug(e)
        await event.reply("<b>No Results Found</b>\nCould not resolve the specified location.", parse_mode="html")


@register(pattern="^/google (.*)")
async def google(event):
    if event.fwd_from:
        return
    
    webevent = await event.reply("<b>Search</b>\nSearching the web...", parse_mode="html")
    match = event.pattern_match.group(1)
    
    gs = await google_search(match)
    if not gs:
        await webevent.edit("<b>No Results Found</b>\nCould not find any search results.", parse_mode="html")
        return
        
    import html
    msg = ""
    for res in gs:
        title = html.escape(res["title"])
        link = res["link"]
        desc = html.escape(res["description"])
        msg += f"❍ <a href='{link}'>{title}</a>\n<b>{desc}</b>\n\n"
        
    await webevent.edit(
        f"<b>Search Query:</b>\n<code>{html.escape(match)}</code>\n\n<b>Results:</b>\n{msg}",
        parse_mode="html",
        link_preview=False
    )


@register(pattern="img (.*)")
async def img_sampler(event):
    if event.fwd_from:
        return
    if (
        event.is_group
        and not await is_register_admin(event.input_chat, event.message.sender_id)
    ):
        await event.reply(
            "<b>Action Denied</b>\nYou must be an administrator to perform this action in a group chat.",
            parse_mode="html"
        )
        return

    query = event.pattern_match.group(1)
    downloader.download(
        query,
        limit=4,
        output_dir="store",
        adult_filter_off=False,
        force_replace=False,
        timeout=60,
    )
    import shutil
    store_dir = os.path.join("store", query)
    if not os.path.exists(store_dir) and os.path.exists("store"):
        dirs = [d for d in os.listdir("store") if os.path.isdir(os.path.join("store", d))]
        if dirs:
            store_dir = os.path.join("store", dirs[0])
            
    files_grabbed = []
    if os.path.exists(store_dir):
        for ext in ("*.png", "*.jpeg", "*.jpg"):
            files_grabbed.extend(glob.glob(os.path.join(store_dir, ext)))
            
    if files_grabbed:
        await telethn.send_file(event.chat_id, files_grabbed, reply_to=event.id)
        
    if os.path.exists("store"):
        shutil.rmtree("store")


opener = urllib.request.build_opener()
useragent = "Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/74.0.3729.157 Mobile Safari/537.36"
opener.addheaders = [("User-agent", useragent)]


async def ParseSauce(googleurl):
    """Parse/Scrape the HTML code for the info we want."""

    source = opener.open(googleurl).read()
    soup = BeautifulSoup(source, "html.parser")

    results = {"similar_images": "", "best_guess": ""}

    with contextlib.suppress(BaseException):
        for similar_image in soup.findAll("input", {"class": "gLFyf"}):
            url = "https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote_plus(
                similar_image.get("value")
            )
            results["similar_images"] = url

    for best_guess in soup.findAll("div", attrs={"class": "r5a77d"}):
        results["best_guess"] = best_guess.get_text()

    return results


async def scam(results, lim):

    single = opener.open(results["similar_images"]).read()
    decoded = single.decode("utf-8")

    imglinks = []
    counter = 0

    pattern = r"^,\[\"(.*[.png|.jpg|.jpeg])\",[0-9]+,[0-9]+\]$"
    oboi = re.findall(pattern, decoded, re.I | re.M)

    for imglink in oboi:
        counter += 1
        if counter < int(lim):
            imglinks.append(imglink)
        else:
            break

    return imglinks


@register(pattern="^/app (.*)")
async def apk(e):
    if e.fwd_from:
        return
    try:
        app_name = e.pattern_match.group(1).strip()
        search_url = f"https://play.google.com/store/search?q={urllib.parse.quote_plus(app_name)}&c=apps"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        page = requests.get(search_url, headers=headers, timeout=10)
        soup = bs4.BeautifulSoup(page.content, "html.parser")
        
        app_id = None
        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "/store/apps/details?id=" in href:
                app_id = href.split("?id=")[1].split("&")[0]
                break

        if not app_id:
            await e.reply("<b>No Results Found</b>\nCould not find any applications matching that name.", parse_mode="html")
            return

        detail_url = f"https://play.google.com/store/apps/details?id={app_id}"
        detail_page = requests.get(detail_url, headers=headers, timeout=10)
        detail_soup = bs4.BeautifulSoup(detail_page.content, "html.parser")

        # Title
        title_tag = detail_soup.find("h1")
        title = title_tag.text.strip() if title_tag else app_name.capitalize()

        # Developer
        dev = "N/A"
        dev_link = detail_url
        for a in detail_soup.find_all("a"):
            href = a.get("href", "")
            if "/store/apps/developer" in href or "/store/apps/dev" in href:
                dev = a.text.strip()
                dev_link = "https://play.google.com" + href
                break

        # Rating
        rating = "N/A"
        for div in detail_soup.find_all("div", {"aria-label": True}):
            label = div["aria-label"]
            if "stars out of five" in label or "Rated" in label:
                rating = label.replace("Rated ", "").replace(" stars out of five", "/5").replace(" stars", "")
                break

        # Icon / Image
        og_img = detail_soup.find("meta", property="og:image")
        app_icon = og_img["content"] if og_img else "https://play.google.com/favicon.ico"

        # Description
        og_desc = detail_soup.find("meta", property="og:description")
        desc = og_desc["content"].strip()[:200] + "..." if og_desc else "No description available."

        import html
        app_details = f"<b><a href='{app_icon}'>{html.escape(title)}</a></b>\n\n"
        app_details += f"<code>Developer  :</code> <a href='{dev_link}'>{html.escape(dev)}</a>\n"
        app_details += f"<code>Rating     :</code> {html.escape(rating)}\n"
        app_details += f"<code>Description:</code> {html.escape(desc)}\n\n"
        app_details += f"<code>Features   :</code> <a href='{detail_url}'>View in Play Store</a>"
        app_details += f"\n\n<b>{BOT_NAME} Information System</b>"

        await e.reply(app_details, link_preview=True, parse_mode="HTML")
    except Exception as err:
        await e.reply(f"<b>Error</b>\nAn unexpected error occurred: <code>{html.escape(str(err))}</code>", parse_mode="html")


def progress(current, total):
    """Calculate and return the download progress with given arguments."""
    LOGGER.debug(
        "Downloaded {} of {}\nCompleted {}".format(
            current, total, (current / total) * 100
        )
    )


@register(pattern=r"^/getqr$")
async def parseqr(qr_e):
    """For /getqr command, get QR Code content from the replied photo."""
    if qr_e.fwd_from:
        return
    
    reply = await qr_e.get_reply_message()
    if not reply or not reply.media:
        await qr_e.reply("<b>Invalid Command Usage</b>\nPlease reply to a photo or image containing a QR code.", parse_mode="html")
        return

    if not any(hasattr(reply.media, attr) for attr in ["photo", "document"]):
        await qr_e.reply("<b>Invalid Media Type</b>\nThe replied message does not contain a valid image file.", parse_mode="html")
        return

    start = datetime.now()
    status_msg = await qr_e.reply("<b>QR Parser</b>\nDownloading image and parsing QR code...", parse_mode="html")
    
    try:
        downloaded_file_name = await qr_e.telethn.download_media(reply)
        if not downloaded_file_name:
            await status_msg.edit("<b>Error</b>\nFailed to download the media image.", parse_mode="html")
            return

        url = "https://api.qrserver.com/v1/read-qr-code/?outputformat=json"
        with open(downloaded_file_name, "rb") as file:
            files = {"file": file}
            resp = post(url, files=files, timeout=15).json()
            
        if os.path.exists(downloaded_file_name):
            os.remove(downloaded_file_name)
            
        if resp and isinstance(resp, list) and "symbol" in resp[0]:
            symbol = resp[0]["symbol"][0]
            qr_contents = symbol.get("data")
            error = symbol.get("error")
            
            if error:
                await status_msg.edit(f"<b>QR Parser Error</b>\nCould not read the QR code: <code>{html.escape(str(error))}</code>", parse_mode="html")
            elif qr_contents:
                duration = (datetime.now() - start).seconds
                await status_msg.edit(
                    f"<b>QR Parser Completed</b>\nProcessed in {duration} seconds.\n\n<b>Contents:</b>\n<code>{html.escape(qr_contents)}</code>",
                    parse_mode="html"
                )
            else:
                await status_msg.edit("<b>No Data Found</b>\nNo QR code details were found in the parsed image.", parse_mode="html")
        else:
            await status_msg.edit("<b>QR Parser Error</b>\nFailed to read the QR code from the image.", parse_mode="html")
            
    except Exception as e:
        await status_msg.edit(f"<b>Error</b>\nAn error occurred while parsing: <code>{html.escape(str(e))}</code>", parse_mode="html")


@register(pattern=r"^/makeqr(?: |$)([\s\S]*)")
async def make_qr(qrcode):
    """For /makeqr command, make a QR Code containing the given content."""
    if qrcode.fwd_from:
        return
    
    input_str = qrcode.pattern_match.group(1).strip()
    message = ""
    reply_msg_id = qrcode.id
    
    if input_str:
        message = input_str
    elif qrcode.is_reply:
        previous_message = await qrcode.get_reply_message()
        reply_msg_id = previous_message.id
        if previous_message.document and previous_message.document.mime_type.startswith("text/"):
            downloaded_file_name = await qrcode.telethn.download_media(previous_message)
            try:
                with open(downloaded_file_name, "r", encoding="utf-8", errors="ignore") as file:
                    message = file.read().strip()
            except Exception:
                message = previous_message.message or ""
            finally:
                if os.path.exists(downloaded_file_name):
                    os.remove(downloaded_file_name)
        else:
            message = previous_message.message or ""
            
    if not message:
        await qrcode.reply("<b>Invalid Command Usage</b>\nUsage: <code>/makeqr [text]</code> or reply to a text message.", parse_mode="html")
        return

    if len(message) > 2000:
        message = message[:2000] + "\n[truncated]"

    status_msg = await qrcode.reply("<b>QR Generator</b>\nGenerating QR code...", parse_mode="html")
    
    import urllib.parse
    encoded_message = urllib.parse.quote(message)
    url = f"https://api.qrserver.com/v1/create-qr-code/?data={encoded_message}&size=300x300&margin=10"

    try:
        resp = get(url, stream=True, timeout=15)
        if resp.status_code != 200:
            await status_msg.edit("<b>API Connection Error</b>\nFailed to generate the QR code via the API.", parse_mode="html")
            return

        required_file_name = "temp_qr.png"
        with open(required_file_name, "wb") as file:
            for chunk in resp.iter_content(chunk_size=1024):
                file.write(chunk)

        await qrcode.telethn.send_file(
            qrcode.chat_id,
            required_file_name,
            reply_to=reply_msg_id
        )
        await status_msg.delete()
        if os.path.exists(required_file_name):
            os.remove(required_file_name)
            
    except Exception as e:
        await status_msg.edit(f"<b>Error</b>\nAn error occurred during generation: <code>{html.escape(str(e))}</code>", parse_mode="html")

__help__ = True

__mod_name__ = "Google"


