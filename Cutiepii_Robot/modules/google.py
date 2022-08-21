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

import glob
import os
import re
import urllib
import urllib.request
import bs4
import requests
import contextlib

from asyncio import sleep
from datetime import datetime
from requests import get, post
from bs4 import BeautifulSoup
from bing_image_downloader import downloader
from geopy.geocoders import Nominatim
from telethon.tl import functions, types
from telethon import *
from telethon.tl.types import *

from Cutiepii_Robot import telethn, LOGGER
from Cutiepii_Robot.events import register
"""
trans = SyncTranslator()

def get_string(key: str) -> Any:
    lang = language[0]
    try:
        return languages[lang][key]
    except (KeyError, IndexError):
        try:
            en_ = languages["en"][key]
            tr = trans.translate(en_, lang_tgt=lang).replace("\ N", "\n")
            if en_.count("{}") != tr.count("{}"):
                tr = en_
            if languages.get(lang):
                languages[lang][key] = tr
            else:
                languages.update({lang: {key: tr}})
            return tr
        except (KeyError, IndexError):
            return f"Warning: could not load any string with the key `{key}`"
        except Exception as er:
            LOGGER.exception(er)
            return languages["en"].get(key) or f"Failed to load language string "{key}"


async def google_search(query):
    query = query.replace(" ", "+")
    _base = "https://google.com"
    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "User-Agent": choice(some_random_headers),
    }
    soup = BeautifulSoup(
        await async_searcher(_base + "/search?q=" + query, headers=headers),
        "html.parser",
    )
    another_soup = soup.find_all("div", class_="ZINbbc xpd O9g5cc uUPGi")
    result = []
    results = [someone.find_all("div", class_="kCrYT") for someone in another_soup]
    for data in results:
        with contextlib.suppress(BaseException):
            if len(data) > 1:
                result.append(
                    {
                        "title": data[0].h3.text,
                        "link": _base + data[0].a["href"],
                        "description": data[1].text,
                    }
                )
    return result
"""


@register(pattern="^/gps (.*)")
async def _(event):
    if event.fwd_from:
        return
    if (event.is_group and not await is_register_admin(
            event.input_chat, event.message.sender_id)):
        await event.reply(
            "You are not Admin. So, You can't use this. Try in my inbox")
        return

    args = event.pattern_match.group(1)

    try:
        geolocator = Nominatim(user_agent="SkittBot")
        location = args
        geoloc = geolocator.geocode(location)
        longitude = geoloc.longitude
        latitude = geoloc.latitude
        gm = f"https://www.google.com/maps/search/{latitude},{longitude}"
        await telethn.send_file(
            event.chat_id,
            file=types.InputMediaGeoPoint(
                types.InputGeoPoint(float(latitude), float(longitude))),
        )
        await event.reply(f"Open with: [Google Maps]({gm})",
                          link_preview=False)
    except Exception as e:
        LOGGER.debug(e)
        await event.reply("I can't find that")


"""
@register(pattern="^/google (.*)")
async def google(event):
    inp = event.pattern_match.group(1)
    if not inp:
        return await eod(event, get_string("autopic_1"))
    x = await event.reply(get_string("com_2"))
    gs = await google_search(inp)
    if not gs:
        return await eod(x, get_string("autopic_2").format(inp))
    out = ""
    for res in gs:
        text = res["title"]
        url = res["link"]
        des = res["description"]
        out += f" 👉🏻  [{text}]({url})\n`{des}`\n\n"
    omk = f"**Google Search Query:**\n`{inp}`\n\n**Results:**\n{out}"
    await x.edit(omk, link_preview=False)


@register(pattern="^/google (.*)")
async def _(event):
    if event.fwd_from:
        return

    webevent = await event.reply("searching........")
    match = event.pattern_match.group(1)
    page = re.findall(r"page=\d+", match)
    try:
        page = page[0]
        page = page.replace("page=", "")
        match = match.replace("page=" + page[0], "")
    except IndexError:
        page = 1
    search_args = (str(match), int(page))
    gsearch = GoogleSearch()
    gresults = await gsearch.async_search(*search_args)
    msg = ""
    for i in range(len(gresults["links"])):
        try:
            title = gresults["titles"][i]
            link = gresults["links"][i]
            desc = gresults["descriptions"][i]
            msg += f"❍[{title}]({link})\n**{desc}**\n\n"
        except IndexError:
            break
    await webevent.edit(
        "**Search Query:**\n`" + match + "`\n\n**Results:**\n" + msg, link_preview=False
    )
"""


@register(pattern="^/img (.*)")
async def img_sampler(event):
    if event.fwd_from:
        return

    query = event.pattern_match.group(1)
    jit = f"{query}"
    downloader.download(
        jit,
        limit=4,
        output_dir="store",
        adult_filter_off=False,
        force_replace=False,
        timeout=60,
    )
    os.chdir(f"./store/'{query}'")
    types = ("*.png", "*.jpeg", "*.jpg")  # the tuple of file types
    files_grabbed = []
    for files in types:
        files_grabbed.extend(glob.glob(files))
    await telethn.send_file(event.chat_id, files_grabbed, reply_to=event.id)
    os.chdir("/app")
    os.system("rm -rf store")


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
                similar_image.get("value"))
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

    try:
        app_name = e.pattern_match.group(1)
        remove_space = app_name.split(" ")
        final_name = "+".join(remove_space)
        page = requests.get(
            f"https://play.google.com/store/search?q={final_name}&c=apps")
        soup = bs4.BeautifulSoup(page.content, "lxml", from_encoding="utf-8")
        results = soup.findAll("div", "ZmHEEd")
        app_name = (results[0].findNext("div", "Vpfmgd").findNext(
            "div", "WsMG1c nnK0zc").text)
        app_dev = results[0].findNext("div",
                                      "Vpfmgd").findNext("div", "KoLSrc").text
        app_dev_link = ("https://play.google.com" + results[0].findNext(
            "div", "Vpfmgd").findNext("a", "mnKHRc")["href"])
        app_rating = (results[0].findNext("div", "Vpfmgd").findNext(
            "div", "pf5lIe").find("div")["aria-label"])
        app_link = ("https://play.google.com" + results[0].findNext(
            "div", "Vpfmgd").findNext("div", "vU6FJ p63iDd").a["href"])
        app_icon = (results[0].findNext("div", "Vpfmgd").findNext(
            "div", "uzcko").img["data-src"])
        app_details = f"<a href={app_icon}" + "'>📲&#8203;</a>"
        app_details += f" <b>{app_name}</b>"
        app_details += ("\n\n<code>Developer :</code> <a href=" +
                        app_dev_link + "'>" + app_dev + "</a>")
        app_details += "\n<code>Rating :</code> " + app_rating.replace(
            "Rated ", "⭐ ").replace(" out of ", "/").replace(
                " stars", "", 1).replace(" stars", "⭐ ").replace("five", "5")
        app_details += ("\n<code>Features :</code> <a href=" + app_link +
                        "'>View in Play Store</a>")
        app_details += "\n\n===> *Cutiepii Robot 愛* <==="
        await e.reply(app_details, parse_mode="HTML")
    except IndexError:
        await e.reply(
            "No result found in search. Please enter **Valid app name**")
    except Exception as err:
        await e.reply(f"Exception Occured:- {str(err)}")


def progress(current, total):
    """Calculate and return the download progress with given arguments."""
    LOGGER.debug(
        f"Downloaded {current} of {total}\nCompleted {current / total * 100}")


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (await
             telethn(functions.channels.GetParticipantRequest(chat, user)
                     )).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (await telethn(functions.messages.GetFullChatRequest(chat.chat_id)
                            )).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None


@register(pattern=r"^/getqr$")
async def parseqr(qr_e):
    """For /getqr command, get QR Code content from the replied photo."""
    if qr_e.fwd_from:
        return
    start = datetime.now()
    downloaded_file_name = await qr_e.telethn.download_media(
        await qr_e.get_reply_message(), progress_callback=progress)
    url = "https://api.qrserver.com/v1/read-qr-code/?outputformat=json"
    with open(downloaded_file_name, "rb") as file:
        files = {"file": file}
        resp = post(url, files=files).json()
        qr_contents = resp[0]["symbol"][0]["data"]
    os.remove(downloaded_file_name)
    end = datetime.now()
    duration = (end - start).seconds
    await qr_e.reply(
        f"Obtained QRCode contents in {duration} seconds, Inside the QR Code was:\n{qr_contents}"
    )


@register(pattern=r"^/makeqr(?: |$)([\s\S]*)")
async def make_qr(qrcode):
    """For /makeqr command, make a QR Code containing the given content."""
    if qrcode.fwd_from:
        return
    start = datetime.now()
    input_str = qrcode.pattern_match.group(1)
    message = "USAGE: `/makeqr <text>`"
    reply_msg_id = None
    if input_str:
        message = input_str
    elif qrcode.reply_to_msg_id:
        previous_message = await qrcode.get_reply_message()
        reply_msg_id = previous_message.id
        if previous_message.media:
            downloaded_file_name = await qrcode.telethn.download_media(
                previous_message, progress_callback=progress)
            m_list = None
            with open(downloaded_file_name, "rb") as file:
                m_list = file.readlines()
            message = "".join(
                media.decode("UTF-8") + "\r\n" for media in m_list)
            os.remove(downloaded_file_name)
        else:
            message = previous_message.message

    url = "https://api.qrserver.com/v1/create-qr-code/?data={}&\
size=200x200&charset-source=UTF-8&charset-target=UTF-8\
&ecc=L&color=0-0-0&bgcolor=255-255-255\
&margin=1&qzone=0&format=jpg"

    resp = get(url.format(message), stream=True)
    required_file_name = "temp_qr.png"
    with open(required_file_name, "w+b") as file:
        for chunk in resp.iter_content(chunk_size=128):
            file.write(chunk)
    await qrcode.telethn.send_file(
        qrcode.chat_id,
        required_file_name,
        reply_to=reply_msg_id,
        progress_callback=progress,
    )
    os.remove(required_file_name)
    duration = (datetime.now() - start).seconds
    await qrcode.reply(f"Created QRCode in {duration} seconds")
    await sleep(5)


__help__ = """
➛ /google <text>*:* Perform a google search
➛ /img <text>*:* Search Google for images and returns them\nFor greater no. of results specify lim, For eg: `/img hello lim=10`
➛ /app <appname>*:* Searches for an app in Play Store and returns its details.
➛ /reverse*:* reply to a sticker, or an image to search it!
  Do you know that you can search an image with a link too? /reverse picturelink <amount>.
➛ /gitinfo <github username>*:* Get info of any github profile
➛ /ytdl <youtube video link*:* download any youtube video in every possible resolution.
➛ /webss <website url>*:* get screen shot of any website you want.
➛ /makeqr <text*:*  make any text to a qr code format
➛ /getqr <reply to a qrcode>*:*  decode and get what is inside the qr code.
"""

__mod_name__ = "Google"
