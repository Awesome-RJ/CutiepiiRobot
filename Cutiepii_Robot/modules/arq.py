from pyrogram import filters

from Cutiepii_Robot import pgram, arq, BOT_USERNAME


@pgram.on_message(filters.command("arq"))
async def arq_stats(_, message):
    data = await arq.stats()
    if not data.ok:
        return await message.reply_text(data.result)
    data = data.result
    uptime = data.uptime
    requests = data.requests
    cpu = data.cpu
    server_mem = data.memory.server
    api_mem = data.memory.api
    disk = data.disk
    platform = data.platform
    python_version = data.python
    users = data.users
    statistics = f"""
**>-< System >-<**
**Uptime:** `{uptime}`
**Requests Since Uptime:** `{requests}`
**CPU:** `{cpu}`
**Memory:**
    **Total Used:** `{server_mem}`
    **API:** `{api_mem}`
**Disk:** `{disk}`
**Platform:** `{platform}`
**Python:** `{python_version}`

**ARQ Statistics:**
**Users:** `{users}`

**@{BOT_USERNAME} Some Modules Running On ARQ**
"""
    await message.reply_text(
        statistics, disable_web_page_preview=True
    )
