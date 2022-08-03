from Cutiepii_Robot import mongodb, telethn
from Cutiepii_Robot.events import register
from telethon import *
import dateparser

db = mongodb["Cutiepii_Robot_alarm"]
alarms = db.alarm
approved_users = db.approve


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (await
             telethn(functions.channels.GetParticipantRequest(chat, user)
                     )).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (await telethn(functions.messages.GetFullChatRequest(chat.chat_id)
                            )).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None


def get_reason(id, time, user):
    return alarms.find_one({"chat": id, "time": time, "user": user})


@register(pattern="^/setalarm (.*)")
async def _(event):
    if event.fwd_from:
        return
    if not event.is_private:
        await event.reply("Alarms can only be set in my pm .")
        return
    approved_userss = approved_users.find({})
    for ch in approved_userss:
        iid = ch["id"]
        userss = ch["user"]
    if event.is_group:
        if await is_register_admin(event.input_chat, event.message.sender_id):
            pass
        elif event.chat_id != iid or event.sender_id != userss:
            return
    quew = event.pattern_match.group(1)
    if "|" in quew:
        iid, zonee, reasonn = quew.split("|")
    time = iid.strip()
    reason = reasonn.strip()
    zone = zonee.strip()
    if len(time) != 22:
        await event.reply("Please enter valid date and time.")
        return
    ttime = dateparser.parse(f"{time}",
                             settings={
                                 "TIMEZONE": f"{zone}",
                                 "DATE_ORDER": "DMY"
                             })
    if ttime is None:
        await event.reply("Please enter valid date and time.")
        return
    time = ttime  # exchange
    present = dateparser.parse("now",
                               settings={
                                   "TIMEZONE": f"{zone}",
                                   "DATE_ORDER": "YMD"
                               })

    #print(time)
    #print(present)
    if not time > present:
        await event.reply("Please enter valid date and time.")
        return
    if not reason:
        reason = "No reason given"
    chats = alarms.find({})
    for c in chats:
        if event.chat_id == c["chat"] and time == c[
                "time"] and f"[user](tg://user?id={event.sender_id})" == c[
                    "user"]:
            to_check = get_reason(
                id=event.chat_id,
                time=time,
                user=f"[user](tg://user?id={event.sender_id})")
            alarms.update_one(
                {
                    "_id": to_check["_id"],
                    "chat": to_check["chat"],
                    "user": to_check["user"],
                    "time": to_check["time"],
                    "zone": to_check["zone"],
                    "reason": to_check["reason"]
                }, {"$set": {
                    "reason": reason,
                    "zone": zone
                }})
            await event.reply(
                "This alarm is already set.\nI am updating the reason(and zone) of the alarm with the new reason(and zone)."
            )
            return
    alarms.insert_one({
        "chat": event.chat_id,
        "user": f"[user](tg://user?id={event.sender_id})",
        "time": time,
        "zone": zone,
        "reason": reason
    })
    await event.reply("Alarm set successfully !")


@telethn.on(events.NewMessage(pattern=None))
async def tikclock():
    chats = alarms.find({})
    for c in chats:
        #print(c)
        chat = c["chat"]
        user = c["user"]
        time = c["time"]
        zone = c["zone"]
        reason = c["reason"]
        present = dateparser.parse("now",
                                   settings={
                                       "TIMEZONE": f"{zone}",
                                       "DATE_ORDER": "YMD"
                                   })

        ttime = dateparser.parse(f"{time}", settings={"TIMEZONE": f"{zone}"})
        #print(ttime)
        #print(present)
        #print (zone)
        #print(present>=ttime)
        if present > ttime:
            await telethn.send_message(
                chat,
                f"**DING DONG**\n\n__This is an alarm set by__ {user} __for reason -__ `{reason}`"
            )
            alarms.delete_one({
                "chat": chat,
                "user": user,
                "time": time,
                "zone": zone,
                "reason": reason
            })
            break
        continue


__help__ = """
 - /setalarm <(date) (time)|zone|reason>: sets a alarm/reminder 
**Syntax:** `/setalarm 01/01/2000 10:00:00 AM | America/New_York | breakfast`
**NOTE:** Please turn on notifications for @Cutiepii_Robot otherwise you will not get notification for the alarm !
"""

__mod_name__ = "Alarm"
