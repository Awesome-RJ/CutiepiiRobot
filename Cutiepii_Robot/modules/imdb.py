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

import re
import bs4
import requests

from telethon import types
from telethon.tl import functions

from Cutiepii_Robot.events import register
from Cutiepii_Robot import telethn

langi = "en"


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerUser):
        return True


@register(pattern="^/imdb (.*)")
async def imdb(e):
    if e.is_group and not await is_register_admin(
        e.input_chat, e.message.sender_id
    ):
        return

    try:
        movie_name = e.pattern_match.group(1)
        remove_space = movie_name.split(" ")
        final_name = "+".join(remove_space)
        page = requests.get(
            f"https://www.imdb.com/find?ref_=nv_sr_fn&q={final_name}&s=all"
        )

        str(page.status_code)
        soup = bs4.BeautifulSoup(page.content, "lxml")
        odds = soup.findAll("tr", "odd")
        mov_title = odds[0].findNext("td").findNext("td").text
        mov_link = (
            "http://www.imdb.com/" + odds[0].findNext("td").findNext("td").a["href"]
        )
        page1 = requests.get(mov_link)
        soup = bs4.BeautifulSoup(page1.content, "lxml")
        if soup.find("div", "poster"):
            poster = soup.find("div", "poster").img["src"]
        else:
            poster = ""
        if soup.find("div", "title_wrapper"):
            pg = soup.find("div", "title_wrapper").findNext("div").text
            mov_details = re.sub(r"\s+", " ", pg)
        else:
            mov_details = ""
        credits = soup.findAll("div", "credit_summary_item")
        director = credits[0].a.text
        if len(credits) == 1:
            writer = "Not available"
            stars = "Not available"
        elif len(credits) > 2:
            writer = credits[1].a.text
            actors = [x.text for x in credits[2].findAll("a")]
            actors.pop()
            stars = f"{actors[0]},{actors[1]},{actors[2]}"
        else:
            writer = "Not available"
            actors = [x.text for x in credits[1].findAll("a")]
            actors.pop()
            stars = f"{actors[0]},{actors[1]},{actors[2]}"
        if soup.find("div", "inline canwrap"):
            story_line = soup.find("div", "inline canwrap").findAll("p")[0].text
        else:
            story_line = "Not available"
        if info := soup.findAll("div", "txt-block"):
            mov_country = []
            mov_language = []
            for node in info:
                a = node.findAll("a")
                for i in a:
                    if "country_of_origin" in i["href"]:
                        mov_country.append(i.text)
                    elif "primary_language" in i["href"]:
                        mov_language.append(i.text)
        if soup.findAll("div", "ratingValue"):
            for r in soup.findAll("div", "ratingValue"):
                mov_rating = r.strong["title"]
        else:
            mov_rating = "Not available"
        await e.reply(
            (
                (
                    (
                        (
                            (
                                (
                                    (
                                        (
                                            (
                                                (
                                                    (
                                                        (
                                                            (
                                                                (
                                                                    (
                                                                        (
                                                                            (
                                                                                (
                                                                                    (
                                                                                        (
                                                                                            f"<a href={poster}"
                                                                                            + ">&#8203;</a>"
                                                                                            "<b>Title : </b><code>"
                                                                                        )
                                                                                        + mov_title
                                                                                    )
                                                                                    + "</code>\n<code>"
                                                                                )
                                                                                + mov_details
                                                                            )
                                                                            + "</code>\n<b>Rating : </b><code>"
                                                                        )
                                                                        + mov_rating
                                                                    )
                                                                    + "</code>\n<b>Country : </b><code>"
                                                                )
                                                                + mov_country[
                                                                    0
                                                                ]
                                                            )
                                                            + "</code>\n<b>Language : </b><code>"
                                                        )
                                                        + mov_language[0]
                                                    )
                                                    + "</code>\n<b>Director : </b><code>"
                                                )
                                                + director
                                            )
                                            + "</code>\n<b>Writer : </b><code>"
                                        )
                                        + writer
                                    )
                                    + "</code>\n<b>Stars : </b><code>"
                                )
                                + stars
                            )
                            + "</code>\n<b>IMDB Url : </b>"
                        )
                        + mov_link
                    )
                    + "\n<b>Story Line : </b>"
                )
                + story_line
            ),
            link_preview=True,
            parse_mode="HTML",
        )

    except IndexError:
        await e.reply("Please enter a valid movie name !")
