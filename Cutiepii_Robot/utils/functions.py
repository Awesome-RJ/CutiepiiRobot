import codecs
import pickle
from asyncio import gather, get_running_loop
from math import atan2, cos, radians, sin, sqrt
from random import randint

import aiofiles
import aiohttp

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from wget import download

from Cutiepii_Robot.utils import aiodownloader
from Cutiepii_Robot.utils.fetch import fetch
"""
Just import 'downloader' anywhere and do downloader.download() to
download file from a given url
"""
downloader = aiodownloader.Handler()


# Another downloader, but with wget
async def download_url(url: str):
    loop = get_running_loop()
    file = await loop.run_in_executor(None, download, url)
    return file


def generate_captcha():
    # Generate one letter
    def gen_letter():
        return chr(randint(65, 90))

    def rndColor():
        return (randint(64, 255), randint(64, 255), randint(64, 255))

    def rndColor2():
        return (randint(32, 127), randint(32, 127), randint(32, 127))

    # Generate a 4 letter word
    def gen_wrong_answer():
        return "".join(gen_letter() for _ in range(4))

    # Generate 8 wrong captcha answers
    wrong_answers = []
    for _ in range(8):
        wrong_answers.append(gen_wrong_answer())

    width = 80 * 4
    height = 100
    correct_answer = ""
    font = ImageFont.truetype("assets/arial.ttf", 55)
    file = f"assets/{randint(1000, 9999)}.jpg"
    image = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Draw random points on image
    for x in range(width):
        for y in range(height):
            draw.point((x, y), fill=rndColor())

    for t in range(4):
        letter = gen_letter()
        correct_answer += letter
        draw.text((60 * t + 50, 15), letter, font=font, fill=rndColor2())
    image = image.filter(ImageFilter.BLUR)
    image.save(file, "jpeg")
    return [file, correct_answer, wrong_answers]


async def file_size_from_url(url: str) -> int:
    async with aiohttp.ClientSession() as session, session.head(url) as resp:
        size = int(resp.headers["content-length"])
    return size


async def get_http_status_code(url: str) -> int:
    async with aiohttp.ClientSession() as session, session.head(url) as resp:
        return resp.status


async def transfer_sh(file):
    async with aiofiles.open(file, "rb") as f:
        params = {file: await f.read()}
    async with aiohttp.ClientSession() as session, session.post(
            "https://transfer.sh/", data=params) as resp:
        download_link = str(await resp.text()).strip()
    return download_link


def obj_to_str(object):
    if not object:
        return False
    return codecs.encode(pickle.dumps(object), "base64").decode()


def str_to_obj(string: str):
    return pickle.loads(codecs.decode(string.encode(), "base64"))


async def calc_distance_from_ip(ip1: str, ip2: str) -> float:
    Radius_Earth = 6371.0088
    data1, data2 = await gather(fetch(f"http://ipinfo.io/{ip1}"),
                                fetch(f"http://ipinfo.io/{ip2}"))
    lat1, lon1 = data1["loc"].split(",")
    lat2, lon2 = data2["loc"].split(",")
    lat1, lon1 = radians(float(lat1)), radians(float(lon1))
    lat2, lon2 = radians(float(lat2)), radians(float(lon2))
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return Radius_Earth * c
