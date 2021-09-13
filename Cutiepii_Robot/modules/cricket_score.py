import urllib.request

from bs4 import BeautifulSoup
from telethon import events
from telethon.tl import functions, types
from Cutiepii_Robot import telethn


async def is_register_admin(chat, user):

    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (
            await telethn(functions.messages.GetFullChatRequest(chat.chat_id))
        ).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None


@telethn.on(events.NewMessage(pattern="/cs$"))
async def _(event):
    if event.fwd_from:
        return
    if event.is_group and not await is_register_admin(
        event.input_chat, event.message.sender_id
    ):
        return
    score_page = "http://static.cricinfo.com/rss/livescores.xml"
    page = urllib.request.urlopen(score_page)
    soup = BeautifulSoup(page, "html.parser")
    result = soup.find_all("description")
    Sed = "".join(match.get_text() + "\n\n" for match in result)
    await event.reply(
        f"<b><u>Match information gathered successful</b></u>\n\n\n<code>{Sed}</code>",
        parse_mode="HTML",
    )
