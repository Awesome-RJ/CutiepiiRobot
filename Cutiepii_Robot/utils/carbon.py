from io import BytesIO
from Cutiepii_Robot import aiohttpsession

async def make_carbon(code):
    url = "https://carbonara.vercel.app/api/cook"
    async with aiohttpsession.post(url, json={"code": code}) as resp:
        image = BytesIO(await resp.read())
    image.name = "Cutiepii_Carbon.png"
    return image
