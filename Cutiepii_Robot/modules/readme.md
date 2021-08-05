# Cutiepii Robot Example plugin format

## Advanced: Pyrogram
```python3
from Cutiepii_Robot.utils.pluginhelpers import admins_only
from Cutiepii_Robot import pgram

@pgram.on_message(filters.command("hi") & ~filters.edited & ~filters.bot)
@admins_only
async def hmm(client, message):
    j = "Namaste"
    await message.reply(j)
    
__mod_name__ = "Hi"
__help__ = """
<b>Hi</b>
- /hi: Namaste
"""
```

## Advanced: Telethon
```python3

from Cutiepii_Robot import tbot
from Cutiepii_Robot.events import register

@register(pattern="^/hi$")
async def hmm(event):
    j = "Namaste"
    await event.reply(j)
    
__mod_name__ = "Hi"
__help__ = """
<b>Hi</b>
- /hi: Namaste
"""
```

## Advanced: PTB
```PTB 13.7 Comming Soon
```
