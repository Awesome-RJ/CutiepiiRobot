import os
import random

from PIL import Image, ImageDraw, ImageFont

from Cutiepii_Robot.events import register
from Cutiepii_Robot import OWNER_ID, telethn, SUPPORT_CHAT, BOT_USERNAME


logopics = [
 
 "./Cutiepii_Robot/utils/Logo/90681adbbef50d4fba1d6cc261d62cd9.jpg",
	
 "./Cutiepii_Robot/utils/Logo/73b69af0502031831c904fc536118ce1.jpg",
	
 "./Cutiepii_Robot/utils/Logo/6aaf0d7f5db3dce7595b27635645efc6.jpg",
	
 "./Cutiepii_Robot/utils/Logo/ebd7de41ff63c46ad9742b53f3a16d7b.jpg",
	
 "./Cutiepii_Robot/utils/Logo/blackbg.jpg",
 
]

logofonts = [
 
 "./Cutiepii_Robot/utils/Logo/RemachineScriptPersonalUseOnly-yZL3.ttf",
	
 "./Cutiepii_Robot/utils/Logo/beyond-wonderland.regular.ttf",
	
 "./Cutiepii_Robot/utils/Logo/Respective-VP6y.ttf",

 "./Cutiepii_Robot/utils/Logo/Maghrib.ttf",
	
 "./Cutiepii_Robot/utils/Logo/Chopsic.otf",
 
]


@register(pattern="^/logo ?(.*)")
async def lego(event):
 quew = event.pattern_match.group(1)
 if event.sender_id == OWNER_ID:
     pass
 else:

  if not quew:
     await event.reply('Provide Some Text To Draw!')
     return
  pass
 await event.reply('Creating your logo...wait!')
 try:
    text = event.pattern_match.group(1)
    img = Image.open(random.choice(logopics))
    draw = ImageDraw.Draw(img)
    image_widthz, image_heightz = img.size
    pointsize = 500
    fillcolor = "gold"
    shadowcolor = "blue"
    font = ImageFont.truetype(random.choice(logofonts) , 250)
    w, h = draw.textsize(text, font=font)
    h += int(h*0.21)
    image_width, image_height = img.size
    draw.text(((image_widthz-w)/2, (image_heightz-h)/2), text, font=font, fill=(255, 255, 255))
    x = (image_widthz-w)/2
    y= ((image_heightz-h)/2+6)
    draw.text((x, y), text, font=font, fill="yellow", stroke_width=25, stroke_fill="black")
    fname2 = "Cutiepii_Logo.png"
    img.save(fname2, "png")
    await telethn.send_file(event.chat_id, fname2, caption = f"**Made By @{BOT_USERNAME}**")
    if os.path.exists(fname2):
            os.remove(fname2)
 except Exception as e:
   await event.reply(f'**Error Report @{SUPPORT_CHAT}**, {e}')

   
file_help = os.path.basename(__file__)
file_help = file_help.replace(".py", "")
file_helpo = file_help.replace("_", " ")
