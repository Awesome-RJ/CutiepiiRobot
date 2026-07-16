import requests
from Cutiepii_Robot import LOGGER

class HMrequest:
    def nekosGet(name):
        blacklist = ['https://cdn.nekos.life/blowjob/blowjob31.jpg', 'https://cdn.nekos.life/blowjob/blowjob32.jpg', 'https://cdn.nekos.life/lewdkemo/lewd_neko_v2_132.jpg', 'https://cdn.nekos.life/Random_hentai_gif/Random_hentai_gifNB_1039.gif']
        json = requests.get(f"https://nekos.life/api/v2/img/{name}").json()
        if json["url"] in blacklist:
            return HMrequest.nekosGet(name)
        return json

    def nekoloveGet(name):
        return requests.get(f"https://nekos.life/api/v2/img/{name}").json()

    def nekobotGet(name):
        blacklist = ['https://i0.nekobot.xyz/0/2/9/1b50d3f619f1bafdf114a530a2570.jpg', 'https://cdn.nekobot.xyz/9/3/9/448bb2ff69b3457a82f32ecd31c06.jpg', 'https://i0.nekobot.xyz/4/9/3/3b6ccf0c081db887fbe38038af996.jpg', 'https://i0.nekobot.xyz/8/6/9/ee21a6ac7d06aabf0b71691e6dfb5.jpg', 'https://cdn.nekobot.xyz/b/4/d/c1fdf4234fbfba326fb282de9ef8c.jpg', 'https://cdn.nekobot.xyz/b/4/d/c1fdf4234fbfba326fb282de9ef8c.jpg']
        req = requests.get(f"https://nekobot.xyz/api/image?type={name}")
        if not req.status_code == 200:
            return LOGGER.debug('This endpoint don\'t work, or you got a Rate Limit')
        if req.json()["message"] in blacklist:
            return HMrequest.nekobotGet(name)
        return {"url": req.json()["message"]}

    def freakerGet(name):
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0"
        }
        return requests.get(f"https://api.computerfreaker.cf/v2/{name}", headers=headers).json()

        