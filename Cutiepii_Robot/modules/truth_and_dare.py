import requests
from Cutiepii_Robot.events import register


@register(pattern="^/truth ?(.*)")
async def _(td):
    try:
        resp = requests.get("https://tede-api.herokuapp.com/api/truth-en").json()
        results = f"{resp['message']}"
        return await td.reply(results)
    except Exception:
        await td.reply("`Something went wrong LOL...`")


@register(pattern="^/dare ?(.*)")
async def _(dr):
    try:
        resp = requests.get("https://tede-api.herokuapp.com/api/dare-en").json()
        results = f"{resp['message']}"
        return await dr.reply(results)
    except Exception:
        await dr.reply("`Something went wrong LOL...`")
