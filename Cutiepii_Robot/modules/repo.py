from pyrogram import filters

from Cutiepii_Robot import pgram, BOT_USERNAME
from Cutiepii_Robot.utils.errors import capture_err
from Cutiepii_Robot.utils.http import get


@pgram.on_message(filters.command("repo") & ~filters.edited)
@capture_err
async def repo(_, message):
    users = await get(
        "https://api.github.com/repos/Awesome-RJ/CutiepiiRobot/contributors"
    )
    list_of_users = "".join(
        f"**{count}.** [{user['login']}]({user['html_url']})\n"
        for count, user in enumerate(users, start=1)
    )

    text = f"""[Updates](https://t.me/Black_Knights_Union) | [Support](https://t.me/{BOT_USERNAME})
```----------------
| Contributors |
----------------```
{list_of_users}"""
    await pgram.send_message(
        message.chat.id, text=text, disable_web_page_preview=True
    )
