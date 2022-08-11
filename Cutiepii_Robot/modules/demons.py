import asyncio

from telethon import events, Button
from telethon.tl.functions.channels import EditBannedRequest
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError
from telethon.tl.types import ChatBannedRights

from Cutiepii_Robot import telethn
from Cutiepii_Robot.modules.helper_funcs.telethn.chatstatus import user_is_admin, can_ban_users

# =================== CONSTANT ===================
BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)


# Demons
async def demons(event):
    demons: int = 0
    X = await event.respond("Searching For Demons...")
    async for user in event.client.iter_participants(event.chat_id):
        if user.deleted:
            demons += 1
            await asyncio.sleep(1)

    if demons > 0:
        markup = [
            [Button.inline("Yes", data="demons yes")],
            [Button.inline("No", data="demons no")],
        ]
        text = f"Found **{0}** Demon{1} In This Chat!\n\nWould You Like To Hunt {2} ?".format(
            demons, 's' if demons > 1 else '',
            'Them All' if demons > 1 else 'That Demon')
        await X.edit(text, buttons=markup)
    else:
        await X.edit("There Are No Demons!\nThis Chat Is Safe For Now!")


@telethn.on(events.CallbackQuery(data=r"demons (yes|no)"))
async def dimonhandler(event):
    if event.data == "demons yes":
        # Here laying the sanity check
        but = await event.get_chat()
        admim = but.admin_rights

        # Check Permissions
        if not await user_is_admin(event.sender_id,
                                   event) and event.sender_id not in [
                                       1087968824
                                   ]:
            await event.answer(
                "You don't have the necessary rights to do this!",
                show_alert=True)
            return
        if not admim and not await can_ban_users(event):
            await event.reply("I haven't got the necessary rights to do this.")
            return

        await event.edit("Hunting Demons...")
        normy_demons: int = 0
        pro_demons: int = 0

        async for user in event.client.iter_participants(event.chat_id):
            if user.deleted:
                try:
                    await event.client(
                        EditBannedRequest(event.chat_id, user.id,
                                          BANNED_RIGHTS))
                    await asyncio.sleep(1)
                except UserAdminInvalidError:
                    normy_demons -= 1
                    pro_demons += 1
                except ChatAdminRequiredError:
                    await event.edit(
                        "I haven't got the necessary rights to do this.")
                    return

                normy_demons += 1

        demon = ""
        if normy_demons > 0:
            demon += f"**{0}** - Demon{1} Hunted!".format(
                normy_demons, 's' if normy_demons > 1 else '')
        if pro_demons > 0:
            demon += f"\n**{0}** - Upper Level Demon{1} {2} Escaped!".format(
                pro_demons, 's' if pro_demons > 1 else '',
                'Are' if pro_demons > 1 else 'Is')

        await event.edit(demon)
        await event.answer("Demon Hunted!")
    elif event.data == "demons no":
        await event.edit("Demom Hunting Task Cancelled!")
        await event.answer("Cancelled!")


DEMONS = demons, events.NewMessage(pattern=r"^[!/]demons$")
telethn.add_event_handler(*DEMONS)

__mod_name__ = "Demons"
__command_list__ = ["demons"]
