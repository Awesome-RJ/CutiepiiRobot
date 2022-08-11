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

import random
import re

import requests
from bs4 import BeautifulSoup as bs

from Cutiepii_Robot.events import register

try:
    import aiofiles
    import aiohttp
except ImportError:
    import urllib

    aiohttp = None


async def download_file(link, name):
    """for files, without progress callback with aiohttp"""
    if not aiohttp:
        urllib.request.urlretrieve(link, name)
        return name
    async with aiohttp.ClientSession() as ses:
        async with ses.get(link) as re_ses:
            file = await aiofiles.open(name, "wb")
            await file.write(await re_ses.read())
            await file.close()
    return name


@register(pattern="^/devian?(.*)")
async def downakd(e):
    match = e.pattern_match.group(1)
    if not match:
        return await e.reply("`Give Query to Search...`")
    Random = False
    if ";" in match:
        num = int(match.split(";")[1])
        if num == 1:
            Random = True
        match = match.split(";")[0]
    else:
        num = 5
    xd = await e.reply("`Processing...`")
    match = match.replace(" ", "+")
    link = f"https://www.deviantart.com/search?q={match}"
    ct = requests.get(link).content
    st = bs(ct, "html.parser", from_encoding="utf-8")
    res = st.find_all("img",
                      loading="lazy",
                      src=re.compile("https://images-wixmp"))[:num]
    if Random:
        res = [random.choice(res)]
    out = []
    num = 0
    for on in res:
        img = await download_file(on["src"], f"./downloads/{match}-{num}.jpg")
        num += 1
        out.append(img)
    if not out:
        return await xd.edit("`No Results Found!`")
    await e.client.send_file(e.chat_id,
                             out,
                             caption=f"Uploaded {len(res)} Images\n",
                             album=True)
    await xd.delete()
