import html
import io
import os
import glob
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status

# Background images list
LOGO_LINKS = [
    "https://telegra.ph/file/cecce411e88f00a5bfd99.jpg",
    "https://telegra.ph/file/e999fbca16d7fd9995d2a.jpg",
    "https://telegra.ph/file/973d830501725e170acf8.jpg",
    "https://telegra.ph/file/a6468482197bdd0b28c2f.jpg",
    "https://telegra.ph/file/bea4c385a300ea6361a2e.jpg",
    "https://telegra.ph/file/5dbda3a87be3d7c479e30.jpg",
    "https://telegra.ph/file/031ac36905d0c56b651e8.jpg",
    "https://telegra.ph/file/1f4c66fffc9da615593da.jpg",
    "https://telegra.ph/file/b1258759a8e78c9e3875f.jpg",
    "https://telegra.ph/file/e3019f8d56c36a7aea553.jpg",
    "https://telegra.ph/file/5503a333443322535011c.jpg",
    "https://telegra.ph/file/81b1dde32ad5f1866b4ad.jpg",
    "https://telegra.ph/file/cc3e2c7a1c1aa3e5c9b65.jpg",
    "https://telegra.ph/file/56af4060217c28d7a2876.jpg",
    "https://telegra.ph/file/667bf9f9906b153c98a97.jpg",
    "https://telegra.ph/file/c755afd9993a26c0e083e.jpg",
    "https://telegra.ph/file/559cd6cf75024c200930a.jpg",
    "https://telegra.ph/file/beb3b5cd1345e83572e04.jpg",
    "https://telegra.ph/file/a879aa2817227f329509e.jpg",
    "https://telegra.ph/file/fe190ea385f90cf5c8ded.jpg",
    "https://telegra.ph/file/9c9c66fc2f155f64538ba.jpg",
    "https://telegra.ph/file/8cd004ee7fa37f83e2536.jpg",
    "https://telegra.ph/file/6fe1670a547c4c213b20c.jpg",
    "https://telegra.ph/file/a1e1e15d1c7e109bcbf06.jpg",
    "https://telegra.ph/file/5103238687aee154ea1b7.jpg",
    "https://telegra.ph/file/cb923f740b7ff7083e41c.jpg",
    "https://telegra.ph/file/d807fe3840c964e99c490.jpg",
    "https://telegra.ph/file/90c858c3becdf9e2f1852.jpg",
    "https://telegra.ph/file/77f85981c8ea7e224d2b3.jpg",
    "https://telegra.ph/file/6eba4fab043f95d0f040d.jpg",
    "https://telegra.ph/file/4fe3b7ccdfbfe72ef16a1.jpg",
    "https://telegra.ph/file/7cc9ba4bf1235f77e024b.jpg",
    "https://telegra.ph/file/24468d310be55228feed2.jpg",
    "https://telegra.ph/file/29ec2c988009075c38a77.jpg",
    "https://telegra.ph/file/b6f9d956c2e8280b5751a.jpg",
    "https://telegra.ph/file/a0e276f1d9499c7323475.jpg",
    "https://telegra.ph/file/a25dbc5301c2a2d89f2ae.jpg",
    "https://telegra.ph/file/da4a7fb76c542bd655ae3.jpg",
    "https://telegra.ph/file/ac7dcbaf77a02dfb612b1.jpg",
    "https://telegra.ph/file/94d15438bc440b307399c.jpg",
    "https://telegra.ph/file/41b28f1f71dd151879a58.jpg",
    "https://telegra.ph/file/fb4859d7da4ec6bcba9a5.jpg",
    "https://telegra.ph/file/206254c31e36fcd3d5db8.jpg",
    "https://telegra.ph/file/e08db741f783a8ede7f1b.jpg",
    "https://telegra.ph/file/3c8a8f5a86e9cdcf454e0.jpg",
    "https://telegra.ph/file/d7171b332f796367b864b.jpg",
    "https://telegra.ph/file/90af83c74d4a7aa4886dc.jpg",
    "https://telegra.ph/file/fecd9ca5cc43ca219f767.jpg",
    "https://telegra.ph/file/c3c16d073ce2ff17ff1b9.jpg",
    "https://telegra.ph/file/2d436ea65189b4a0e2058.jpg",
    "https://telegra.ph/file/1c1854c11fdc1b9468be0.jpg",
    "https://telegra.ph/file/75f507a6c2796bf828186.jpg",
    "https://telegra.ph/file/ef36d66ce31e7805554fd.jpg",
    "https://telegra.ph/file/f0dbdcafaea14b3f8f1c6.jpg",
    "https://telegra.ph/file/b9cf16b5d81578aae3881.jpg",
    "https://telegra.ph/file/a143b18b772401a6a524e.jpg",
    "https://telegra.ph/file/36bf2e1171b44f777f58d.jpg",
    "https://telegra.ph/file/0f9d2d6047cab848ad44c.jpg",
    "https://telegra.ph/file/456a71fc90e1eb9b98109.jpg",
    "https://telegra.ph/file/e56f2572915703424738b.jpg",
    "https://telegra.ph/file/f5f90261f7506fa5b4766.jpg",
    "https://telegra.ph/file/d7e49a357a9bc1f59fde2.jpg",
    "https://telegra.ph/file/9f07ebeb13b0ca9d3f2a1.jpg",
    "https://telegra.ph/file/b1ae47176479c8d5b9713.jpg",
    "https://telegra.ph/file/82ce624aff169a47fa66e.jpg",
    "https://telegra.ph/file/cea0b13774b1d5118cf9d.jpg",
    "https://telegra.ph/file/09cf5e5ceb85f2978dde4.jpg",
    "https://telegra.ph/file/01e7470fe2f9e2ba7281a.jpg",
    "https://telegra.ph/file/17e09e6d5f38938b5666e.jpg",
    "https://telegra.ph/file/64b5814fecf04d37286f2.jpg",
    "https://telegra.ph/file/c6a2dd78c3ab15b49228e.jpg",
    "https://telegra.ph/file/fc0bb4f263aeb6737fe02.jpg",
    "https://telegra.ph/file/d772dbf56675b0632cd8f.jpg",
    "https://telegra.ph/file/d6a4f1a6a898abfe65e21.jpg",
    "https://telegra.ph/file/568ee935709d2e312eaa3.jpg",
    "https://telegra.ph/file/eccfb77d1380ddd3b0363.jpg",
    "https://telegra.ph/file/ba7c525015c259cc474eb.jpg",
    "https://telegra.ph/file/f4068858a842549e25c1f.jpg",
    "https://telegra.ph/file/f1bddef5b2496050c0931.jpg",
    "https://telegra.ph/file/bd6b7493d4b5beb0c116c.jpg",
    "https://telegra.ph/file/77f73079bee231fee9b6f.jpg",
    "https://telegra.ph/file/52a8dfa226ca417916d86.jpg",
    "https://telegra.ph/file/b1c3dcc72216e12cf989a.jpg",
    "https://telegra.ph/file/6f6be563ac4647bcedc43.jpg",
    "https://telegra.ph/file/2735d2c9dad2d2bd86160.jpg",
    "https://telegra.ph/file/30d594f70e2e8e0e80e23.jpg",
    "https://telegra.ph/file/24826ea7d58f44a36fd14.jpg",
    "https://telegra.ph/file/b8ccbd79cc7a5591f7a6e.jpg",
    "https://telegra.ph/file/59cfa7f35533f2563eb8e.jpg",
    "https://telegra.ph/file/dfd842b31706b23170f9d.jpg",
    "https://telegra.ph/file/e4d920897863dddb6f586.jpg",
    "https://telegra.ph/file/e63f991df36839849064b.jpg",
    "https://telegra.ph/file/af15efbaa212f18c17d08.jpg",
    "https://telegra.ph/file/b83c85c52b497cc25d9d7.jpg",
    "https://telegra.ph/file/ed5d19166cca90cf02f3e.jpg",
    "https://telegra.ph/file/2303c4a4a3d41f1531e3e.jpg",
    "https://telegra.ph/file/7d4152dd4c9e8150f0717.jpg",
    "https://telegra.ph/file/f4905f5bab3dfc7aed145.jpg",
    "https://telegra.ph/file/d80154c9508777093654e.jpg",
    "https://telegra.ph/file/b9c49c1d72f8057adc03d.jpg",
    "https://telegra.ph/file/a3af436f2e0e76eda47d9.jpg",
    "https://telegra.ph/file/91ab92895eba337e38f1c.jpg",
    "https://telegra.ph/file/eaf496c3bb1b637103985.jpg",
    "https://telegra.ph/file/7503016b471a092ec2003.jpg",
    "https://telegra.ph/file/2d2d8cf41e3146b6f31f4.jpg",
    "https://telegra.ph/file/418c0f9a5dbb63c493840.jpg",
    "https://telegra.ph/file/c380a60255706ade8662c.jpg",
    "https://telegra.ph/file/21b5bf4c8d2872b499fb0.jpg",
    "https://telegra.ph/file/6f51b9215f4d5dac79102.jpg",
    "https://telegra.ph/file/c3e8ab0ac88f303a4c2e3.jpg",
    "https://telegra.ph/file/2d9accf761a99f8972824.jpg",
    "https://telegra.ph/file/245f539f6701b4530eab9.jpg",
    "https://telegra.ph/file/e73a8be6ed6136865741a.jpg",
    "https://telegra.ph/file/39a9b6f487edf10e07222.jpg",
    "https://telegra.ph/file/2c3e389e4eaf0b952b817.jpg",
    "https://telegra.ph/file/5dc0bfe4c8c34dc980879.jpg",
    "https://telegra.ph/file/b6830b97207b9b743ec2d.jpg",
    "https://telegra.ph/file/2ed967a134f78894c845e.jpg",
    "https://telegra.ph/file/0859c9235f44d774ec11d.jpg",
    "https://telegra.ph/file/d90610f30e2d7adb25938.jpg",
    "https://telegra.ph/file/639fdd9f760861bfb20d4.jpg",
    "https://telegra.ph/file/a7d454b97edfa01a586c7.jpg",
    "https://telegra.ph/file/4cb6230c6485ee3ed5cf7.jpg",
    "https://telegra.ph/file/46c4fde58d80f04c7316c.jpg",
    "https://telegra.ph/file/71b3c347050c5b1320d0b.jpg",
    "https://telegra.ph/file/2fd14298a3d395d804062.jpg",
    "https://telegra.ph/file/e56d5462b78457bcf7082.jpg",
    "https://telegra.ph/file/b0988d2c3903bf208286d.jpg",
    "https://telegra.ph/file/85d64e47fddf0b0393617.jpg",
]

# Helper function to add rounded corners
def add_corners(im, rad):
    circle = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
    alpha = Image.new('L', im.size, 255)
    w, h = im.size
    alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
    alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
    alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
    im.putalpha(alpha)
    return im

def combine_custom_logo(im, text1):
    im = add_corners(im, 17)
    font_path = "./Cutiepii_Robot/utils/Logo/default.ttf"
    if not os.path.exists(font_path):
        fnt_files = glob.glob("./Cutiepii_Robot/utils/Logo/*")
        if fnt_files:
            font_path = fnt_files[0]
        else:
            raise FileNotFoundError("No fonts found in ./Cutiepii_Robot/utils/Logo/")

    font_size = 120
    font = ImageFont.truetype(font_path, font_size)

    text_bbox = font.getbbox(text1)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    baru = Image.new(
        "RGB",
        (im.width + text_width + 210 + 20 + 130, 600),
        color=(0, 0, 0)
    )

    draw = ImageDraw.Draw(baru)
    draw.text((150, 250), text1, (255, 255, 255), font=font)
    baru.paste(im, (150 + text_width + 20, 230 + 10), im.convert("RGBA"))
    return baru

def generate_custom_logo(text1, text2):
    font_path = "./Cutiepii_Robot/utils/Logo/default.ttf"
    if not os.path.exists(font_path):
        fnt_files = glob.glob("./Cutiepii_Robot/utils/Logo/*")
        if fnt_files:
            font_path = fnt_files[0]
        else:
            raise FileNotFoundError("No fonts found in ./Cutiepii_Robot/utils/Logo/")

    font_size = 120
    font = ImageFont.truetype(font_path, font_size)

    text_bbox = font.getbbox(text2)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    oren = Image.new("RGBA", (text_width + 20, 140), color=(240, 152, 0))
    draw = ImageDraw.Draw(oren)

    text_x = 10
    text_y = (oren.height - text_height) // 2 - 10
    draw.text((text_x, text_y), text2, (0, 0, 0), font=font)

    return combine_custom_logo(oren, text1)

def generate_blackpink_logo(teks):
    font_path = "./Cutiepii_Robot/utils/Logo/blackpink.otf"
    if not os.path.exists(font_path):
        font_path = "./Cutiepii_Robot/utils/Logo/default.ttf"
    if not os.path.exists(font_path):
        fnt_files = glob.glob("./Cutiepii_Robot/utils/Logo/*")
        if fnt_files:
            font_path = fnt_files[0]
        else:
            raise FileNotFoundError("No fonts found in ./Cutiepii_Robot/utils/Logo/")

    font_size = 120
    font = ImageFont.truetype(font_path, font_size)

    text_bbox = font.getbbox(teks)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    img = Image.new("RGB", (text_width + 100, text_height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    x = (img.width - text_width) // 2
    y = -25
    draw.text((x, y), teks, fill=(255, 148, 224), font=font)

    padded_width = img.width + 400
    padded_height = img.height + 400
    img2 = Image.new("RGB", (padded_width, padded_height), color=(0, 0, 0))

    paste_x = (img2.width - img.width) // 2
    paste_y = (img2.height - img.height) // 2
    img2.paste(img, (paste_x, paste_y))

    return img2

@cutiepii_cmd(command="logo")
async def generate_logo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text(
            "Please provide some text to create a logo!\n\nExample: `/logo Yumeko`"
        )
        return

    text = " ".join(args)
    status_message = await message.reply_text("`Logo in progress. Please wait a sec...`", parse_mode=ParseMode.MARKDOWN)

    try:
        img = None
        try:
            api_res = requests.get('https://nekos.best/api/v2/neko', timeout=10)
            if api_res.status_code == 200:
                img_url = api_res.json()['results'][0]['url']
                img_content = requests.get(img_url, timeout=10).content
                img = Image.open(io.BytesIO(img_content))
        except Exception:
            pass

        if not img:
            random_logo = random.choice(LOGO_LINKS)
            response = requests.get(random_logo, timeout=15)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))

        if img.mode != "RGB":
            img = img.convert("RGB")

        # Crop to 1:1 aspect ratio
        width, height = img.size
        new_size = min(width, height)
        left = (width - new_size) // 2
        top = (height - new_size) // 2
        right = left + new_size
        bottom = top + new_size
        img = img.crop((left, top, right, bottom))

        draw = ImageDraw.Draw(img)
        image_widthz, image_heightz = img.size
        fnt_files = glob.glob("./Cutiepii_Robot/utils/Logo/*")
        if not fnt_files:
            await status_message.edit_text("No fonts available in the logo directory.")
            return

        randf = random.choice(fnt_files)
        font_size = max(30, int(image_widthz * 0.11))
        font = ImageFont.truetype(randf, font_size)

        left_x, top_y, right_x, bottom_y = draw.textbbox((0, 0), text, font=font)
        w = right_x - left_x
        h = bottom_y - top_y
        h += int(h * 0.21)

        x = (image_widthz - w) / 2
        y = ((image_heightz - h) / 2 + 6)

        draw.text(((image_widthz - w) / 2, (image_heightz - h) / 2), text, font=font, fill=(255, 255, 255))
        draw.text((x, y), text, font=font, fill="black", stroke_width=1, stroke_fill="white")

        fname = "generated_logo.png"
        img.save(fname, "PNG")

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fname, 'rb'),
            caption=f"<b>Logo Generated by @{context.bot.username}</b>",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=message.message_id
        )

        if os.path.exists(fname):
            os.remove(fname)
        await status_message.delete()

    except Exception as e:
        LOGGER.exception(f"Error generating logo: {e}")
        await status_message.edit_text(f"An error occurred: {str(e)}")

@cutiepii_cmd(command="clogo")
async def make_clogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Provide a name to make a custom logo...")
        return

    match = " ".join(args)
    first, last = "", ""
    if len(match.split()) >= 2:
        first, last = match.split(maxsplit=1)
    else:
        last = match

    status_message = await message.reply_text("`Processing custom logo...`", parse_mode=ParseMode.MARKDOWN)

    try:
        logo = generate_custom_logo(first, last)
        fname = "generated_clogo.png"
        logo.save(fname, format="PNG")

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fname, 'rb'),
            reply_to_message_id=message.message_id
        )

        if os.path.exists(fname):
            os.remove(fname)
        await status_message.delete()
    except Exception as e:
        LOGGER.exception(f"Error in clogo: {e}")
        await status_message.edit_text(f"An error occurred: {str(e)}")

@cutiepii_cmd(command="blogo")
async def make_blogo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Provide a name to make a Blackpink logo...")
        return

    match = " ".join(args)
    status_message = await message.reply_text("`Processing Blackpink logo...`", parse_mode=ParseMode.MARKDOWN)

    try:
        logo = generate_blackpink_logo(match)
        fname = "generated_blogo.png"
        logo.save(fname, format="PNG")

        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=open(fname, 'rb'),
            reply_to_message_id=message.message_id
        )

        if os.path.exists(fname):
            os.remove(fname)
        await status_message.delete()
    except Exception as e:
        LOGGER.exception(f"Error in blogo: {e}")
        await status_message.edit_text(f"An error occurred: {str(e)}")

__mod_name__ = "Logo"

__help__ = True
