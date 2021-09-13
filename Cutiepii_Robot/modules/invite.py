from telethon.tl import functions
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    ChannelPublicGroupNaError)
from telethon.tl.functions.channels import GetFullChannelRequest

from Cutiepii_Robot.events import register
from Cutiepii_Robot import telethn

async def get_chatinfo(event):
    chat = event.pattern_match.group(1)
    chat_info = None
    if chat:
        try:
            chat = int(chat)
        except ValueError:
            pass
    if not chat:
        if event.reply_to_msg_id:
            replied_msg = await event.get_reply_message()
            if replied_msg.fwd_from and replied_msg.fwd_from.channel_id is not None:
                chat = replied_msg.fwd_from.channel_id
        else:
            chat = event.chat_id
    try:
        chat_info = await event.client(GetFullChatRequest(chat))
    except BaseException:
        try:
            chat_info = await event.client(GetFullChannelRequest(chat))
        except ChannelInvalidError:
            await event.reply("`Invalid channel/group`")
            return None
        except ChannelPrivateError:
            await event.reply("`This is a private channel/group or am I blocked there`")
            return None
        except ChannelPublicGroupNaError:
            await event.reply("`No channel or supergroup`")
            return None
        except (TypeError, ValueError):
            await event.reply("`Invalid channel/group`")
            return None
    return chat_info


@register(outgoing=True, pattern=r"^\.inviteall(?: |$)(.*)")
async def get_users(event):
    sender = await event.get_sender()
    me = await event.client.get_me()
    if not sender.id == me.id:
        telethn = await event.reply("`proses...`")
    else:
        telethn = await event.edit("`proses...`")
    telethntes = await get_chatinfo(event)
    chat = await event.get_chat()
    if event.is_private:
        return await telethn.edit("`Sorry, Please add a user here`")
    s = 0
    f = 0
    error = 'None'

    await telethn.edit("**Terminal Status**\n\n`Member Collection.......`")
    async for user in event.client.iter_participants(telethntes.full_chat.id):
        try:
            if error.startswith("Too"):
                return await telethn.edit(f"**Terminal Completed with error**\n(`May got limit error from telethon please try again later`)\n**Error** : \n`{error}`\n\n• Invited `{s}` Member \n• Failed to Add `{f}` Member")
            await event.client(functions.channels.InviteToChannelRequest(channel=chat, users=[user.id]))
            s = s + 1
            await telethn.edit(f"**Terminal Running...**\n\n• Invited `{s}` Member \n• Failed to Add `{f}` Member\n\n**× LastError:** `{error}`")
        except Exception as e:
            error = str(e)
            f = f + 1
    return await telethn.edit(f"**Terminal Finished** \n\n• Successfully Adding `{s}` Member \n• Failed to Add `{f}` Member")

__mod_name__ = "INVITE ALL"
