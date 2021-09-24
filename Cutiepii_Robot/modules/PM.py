# Made By Hunter
# Scammer Devil

from telethon import events, Button, custom
import re, os, random, asyncio
from Cutiepii_Robot import pgram as bot
from telethon import TelegramClient

# Start Text 
LSTART = f'''Hey there! My name is **Shoko**.
I'm here to help you to manage your groups.
I have lots of handy features such as:
‣ Warning system
‣ Artificial intelligence
‣ Flood control system
‣ Note keeping system
‣ Filters keeping system
‣ Approvals and much more.
So what are you waiting for?
Add me in your groups and give me full rights to make me function well.'''


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"suru"))) 
async def _(event):
     await event.edit(LSTART, buttons=start) 

ohk = [[custom.Button.inline("Back", data="start")]]

start = [[custom.Button.url("Add to your Group➕", "t.me/ShokoGbot?=start")]]
start += [[custom.Button.inline("Advanced⭐️", data="advances"), custom.Button.inline("Support🌐", data="SSP")]] 
start += [[custom.Button.inline("Help and commands❓", data="command")]]



@bot.on(events.NewMessage(pattern="^/start$"))
async def _(event):
      START = f'''Hey there! My name is **Shoko**.
I'm here to help you to manage your groups.
I have lots of handy features such as:
‣ Warning system
‣ Artificial intelligence
‣ Flood control system
‣ Note keeping system
‣ Filters keeping system
‣ Approvals and much more.
So what are you waiting for?
Add me in your groups and give me full rights to make me function well.'''
      await bot.send_message(event.chat.id,START, buttons=start)

HLP = '''Hello there! My name is **Shoko Nishimiya**.
I'm a modular group management bot with a few fun extras! Have a look at the following for an idea of some of the things I can help you with.
**Main** commands available:
 `/start`: Starts me, can be used to check i'm alive or no...
 `/help`: PM's you this message.
 `/help <module name>`: PM's you info about that module.
 `/settings`: in PM: will send you your settings for all supported modules.
   - in a group: will redirect you to pm, with all that chat's settings.
 
Click on the buttons below to get documentation about specific modules!'''


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"command"))) 
async def _(event):
     await event.edit(HLP, buttons=kk) 
  
@bot.on(events.NewMessage(pattern="/help"))
async def _(event):
   if not event.is_group:
    await bot.send_message(event.chat.id,HLP, buttons=kk)
   else:
    await event.reply("**Click me for help!**", buttons=[[Button.url("help","t.me/ShokoGbot?start=help")]])
    
@bot.on(events.NewMessage(pattern="^/start help"))
async def _(event):
     await event.reply(HLP, buttons=kk)

@bot.on(events.callbackquery.CallbackQuery(data="help"))
async def _(event):
     await event.reply(HLP, button=kk)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"contut"))) 
async def _(event):
    await event.edit('''**Welcome to the Seona configuration tutorial.**
The first thing to do is to add Seona to your group! For doing that, press the under button and select your group, then press "Done" to continue the tutorial..''', buttons=kk) 

done = [[custom.Button.inline("✅ Done", data="done")]]

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"done"))) 
async def _(event):
    await event.edit('''Ok, well done!
Now for let me work correctly, you need to make me Admin of your Group!
To do that, follow this easy steps:
▫️ Go to your group
▫️ Press the Group's name
▫️ Press Modify
▫️ Press on Administrator
▫️ Press Add Administrator
▫️ Press the Magnifying Glass
▫️ Search @Seona_Robot
▫️ Confirm''', buttons=kk) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"sed")))
async def _(event):
    await event.edit('''
Excellent!
Now the Bot is ready to use!
All commands can be used with /
Note: I recognise only the admins cached in my /admincache so as to avoid sending too many requests to the Telegram's servers. The admin cache will be updated every 10 minutes or upon executing /admincache command.''', buttons=kk) 

contut = [[custom.Button.inline("✅ Done", data="sed")]]
sed = [[custom.Button.inline("Main Menu", data="suru")]]

fuk = [[custom.Button.inline("Back", data="command")]]

kk = [[custom.Button.inline("AFK", data="afk"),custom.Button.inline("Admin",data="adminsm"),custom.Button.inline("Anime",data="anime")]]
kk += [[custom.Button.inline("Anti-spam", data="antispams"), custom.Button.inline("Backups", data="backup"), custom.Button.inline("Bans", data="Bans")]]
kk += [[custom.Button.inline("Bios and Abouts", data="pbio"), custom.Button.inline("Blacklists", data="black"), custom.Button.inline("Connections", data="connect")]]
kk += [[custom.Button.inline("Disabling", data="disable"), custom.Button.inline("Federations", data="fered"), custom.Button.inline("Filters", data="filters")]]
kk += [[custom.Button.inline("Greetings", data="greetings"), custom.Button.inline("Locks", data="Locks"), custom.Button.inline("Logger", data="loggersi")]]
kk += [[custom.Button.inline("Formating", data="fm"), custom.Button.inline("F-sub", data="ex"), custom.Button.inline("Notes", data="notesi")]]
kk += [[custom.Button.inline("Rules", data="rulesi"), custom.Button.inline("Purges", data="purgesi"), custom.Button.inline("Reporting", data="rpot")]]
kk += [[custom.Button.inline("Music", data="Music"), custom.Button.inline("Misc", data="ex")]]
kk += [[custom.Button.inline("Back", data="suru")]]




@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"bios"))) 
async def _(event):
    await event.edit('''Help others know yourself or what others think of yourself in a new way.
That's why here we have a way to describe yourself to the world around.
 • /setbio <text>: Set user's bio
 • /bio: Get user's bio
 • /resetbio: Reset your bio to default 
 • /setme <text>: Set your about
 • /resetabout: Reset your about to default 
 • /me: Get user's about''', buttons=kk) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"black"))) 
async def _(event):
    await event.edit('''Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!
NOTE: Blacklists do not affect group admins.
 • /blacklist: View the current blacklisted words.
Admin only:
 • /addblacklist <triggers>: Add a trigger to the blacklist. Each line is considered one trigger, so using different lines will allow you to add multiple triggers.
 • /unblacklist <triggers>: Remove triggers from the blacklist. Same newline logic applies here, so you can remove multiple triggers at once.
 • /rmblacklist <triggers>: Same as above.
 • /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>: Action to perform when someone sends blacklisted words.
 • /unblacklistall: Remove all blacklist triggers - chat creator only.''', buttons=Bax) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"connect"))) 
async def _(event):
    await event.edit('''Sometimes, you just want to add some notes and filters to a group chat, but you don't want everyone to see; This is where connections come in...
This allows you to connect to a chat's database, and add things to it without the commands appearing in chat! For obvious reasons, you need to be an admin to add things; but any member in the group can view your data.
 • /connect <chatid/username>: Connect to the specified chat, allowing you to view/edit contents.
 • /connection: List connected chats
 • /disconnect: Disconnect from the current chat
 • /helpconnect: List available commands that can be used remotely
Admin only:
 • /allowconnect <yes/no/on/off>: Allow a user to connect to a chat
 
 You can retrieve the chat id by using the /id command in your chat. Don't be surprised if the id is negative; all super groups have negative ids.''', buttons=Bax) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"buans"))) 
async def _(event):
    await event.edit('''Some people need to be publicly banned; spammers, annoyances, or just trolls.
This module allows you to do that easily, by exposing some common actions, so everyone will see!
User commands:
 • /kickme: kick out yourself.
Admins commands:
 • /ban: Ban a user.
 • /dban: Ban a user by reply, and delete their message. 
 • /sban: Silently ban a user, and delete your message.
 • /tban: Temporarily ban a user.
 • /unban: Unban a user.
 • /mute: Mute a user.
 • /dmute: Mute a user by reply, and delete their message. 
 • /smute: Silently mute a user, and delete your message.
 • /tmute: Temporarily mute a user.
 • /unmute: Unmute a user.
 • /kick: Kick a user.
 • /dkick: Kick a user by reply, and delete their message.  
 • /skick: Silently kick a user, and delete your message
 • /restrict: Restricts a user from sending media, gif, polls, etc.
 • /trestrict: Temporarily restricts a user.
 • /unrestrict: Unrestricts the user back to its default permissions.
 Example:
- Ban a user for two hours.
-> /tban @username 2h''', buttons=Bax) 



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"approve"))) 
async def _(event):
    await event.edit('''Sometimes, you might trust a user not to send unwanted content.
Maybe not enough to make them admin, but you might be ok with locks, blacklists, and antiflood not applying to them.
That's what approvals are for - approve of trustworthy users to allow them to send 
Admin commands:
 • /approval: Check a user's approval status in this chat.
 • /approve: Approve of a user. Locks, blacklists, and antiflood won't apply to them anymore.
 • /unapprove: Unapprove of a user. They will now be subject to locks, blacklists, and antiflood again.
 • /approved: List all approved users.
 • /unapproveall: Unapprove ALL users in a chat. This cannot be undone.''', buttons=Bax) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"backup"))) 
async def _(event):
    await event.edit('''Some people just want to see the world burn. Others, just want to have a way of grouping their chat data in one place so they can export their configuration to other chats!
Emilia import/export settings feature allows you to quickly set up a chat using a preexisting template. Instead of setting the same settings over and over again in different chats, you can use this feature to copy the general configuration across groups.
The generated file is in standard JSON format, so if there are any settings you dont want to import to your other chats, just open the file and edit it before importing.
Exporting settings can be done by any administrator, but for security reasons, importing can only be done by the group creator.
The following modules will have their data exported:
- admin
- antiflood
- blacklists
- disabled
- filters
- greetings
- locks
- notes
- pins
- reports
- rules
- warns
Chat owner commands:
- /export: Generate a file containing all your chat data.
- /import: Import the settings in the replied to data file.
Examples:
- To export chat data:
-> /export
- Or, to import a config file from emilia/rose, use:
-> /import <as a reply>
Note: To avoid abuse, this command is heavily rate limited; this is to make sure that people importing/exporting data don't slow down the bot.''', buttons=Bax) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"flood"))) 
async def _(event):
    await event.edit('''You know how sometimes, people join, send 100 messages, and ruin your chat? With antiflood, that happens no more!
Antiflood allows you to take action on users that send more than x messages in a row. Actions are: ban/kick/mute/tban/tmute
User commands:
 • /flood: Get the current flood control setting
Admin commands:
 • /setflood <number/off/no>:  Set the number of messages after which to take action on a user. Set to '0', 'off', or 'no' to disable.
 • /setfloodmode <action type>: Choose which action to take on a user who has been flooding. Options: ban/kick/mute/tban/tmute
Note:
- Value must be filled for tban and tmute!
-> It can be: 5m = 5 minutes, 6h = 6 hours, 3d = 3 days, 1w = 1 week
Examples:
- To set flood number:
-> /setflood 10
- Mute the user who tries to flood for 2 hours:
-> /setfloodmode tmute 2h''', buttons=Bax) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"admin"))) 
async def _(event):
    await event.edit('''Make it easy to promote and demote users with the admin module!
User commands:
 • /adminlist: List of admins in the chat.
Admins commands:
 • /promote <reply/username/mention/userid>: Promotes a user 
 • /demote <reply/username/mention/userid>: Demote a user
 • /admincache: Force update admin status in your group 
 • /send: Echo some message in the exact same state in a group  
 • /invitelink: gets invitelink of chat
 • /setgpic: As a reply to file or photo to set group profile pic
 • /delgpic: Same as above but to remove group profile pic
 • /setgsticker: As a reply to some sticker to set it as group sticker set
 
Sometimes, you promote or demote an admin manually, and Emilia doesn't realise it immediately. This is because to avoid spamming telegram servers, admin status is cached locally.
This means that you sometimes have to wait a few minutes for admin rights to update. If you want to update them immediately, you can use the /admincache command; that'll force Emilia to check who the admins are again.''', buttons=kk) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"afk"))) 
async def _(event):
    await event.edit('''Help others know you are away from telegram with the help of AFK module!
 • /afk <reason>: mark yourself as AFK(away from keyboard).
 • brb <reason>: same as the afk command - but not a command.
When marked as AFK, any mentions will be replied to with a message to say you're not available!''', buttons=Bax) 


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"muta")))
async def _(event):
    await event.edit('''** Mutes **
- /mute: mute a user
- /unmute: unmutes a user
- /tmute [entity] : temporarily mutes a user for the time interval.''',buttons=sedlyf)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"gheiadmin")))
async def _(event):
     await event.edit('''──「 Here's help for ** Admin ** module 」──
Please chose your option.''',buttons=cheator)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"promote"))) 
async def _(event):
    await event.edit('''** Promotes & Demotes**
- /promote (user) (?admin's title): Promotes the user to admin.
- /demote (user): Demotes the user from admin.
- /lowpromote: Promote a member with low rights
- /midpromote: Promote a member with mid rights
- /highpromote: Promote a member with max rights
- /lowdemote: Demote an admin to low permissions
- /middemote: Demote an admin to mid permissions''',buttons=sedlyf) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"ban_kk")))
async def _(event):
    await event.edit('''** Bans & Kicks **
- /ban: bans a user
- /tban [entity] : temporarily bans a user for the time interval.
- /unban: unbans a user
- /unbanall: Unban all banned members
- /banme: Bans you
- /kick: kicks a user
- /kickme: Kicks you''',buttons=warn)

warn = [[custom.Button.inline("Admin Commands", data="ban_kk"), custom.Button.inline("User Commands", data="ucmds")]]
warn += [[custom.Button.inline("Warn Actions", data="actwar"),custom.Button.inline("Warn Limits", data="litwar")]]
warn += [[custom.Button.inline("Back", data="BCK")]]

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"muta")))
async def _(event):
    await event.edit('''** Mutes **
- /mute: mute a user
- /unmute: unmutes a user
- /tmute [entity] : temporarily mutes a user for the time interval.''',buttons=warn)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"gheiadmin")))
async def _(event):
     await event.edit('''Make it easy to admins for manage users and groups with the admin module!
**Available commands:**
** Admin List **
- /adminlist: Shows all admins of the chat.
- /admincache: Update the admin cache, to take into account new admins/admin permissions.''',buttons=warn)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"promote"))) 
async def _(event):
    await event.edit('''** Promotes & Demotes**
- /promote (user) (?admin's title): Promotes the user to admin.
- /demote (user): Demotes the user from admin.
- /lowpromote: Promote a member with low rights
- /midpromote: Promote a member with mid rights
- /highpromote: Promote a member with max rights
- /lowdemote: Demote an admin to low permissions
- /middemote: Demote an admin to mid permissions''',buttons=warn) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"ban_kk")))
async def _(event):
    await event.edit('''** Bans & Kicks **
- /ban: bans a user
- /tban [entity] : temporarily bans a user for the time interval.
- /unban: unbans a user
- /unbanall: Unban all banned members
- /banme: Bans you
- /kick: kicks a user
- /kickme: Kicks you''',buttons=warn)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"muta")))
async def _(event):
    await event.edit('''** Mutes **
- /mute: mute a user
- /unmute: unmutes a user
- /tmute [entity] : temporarily mutes a user for the time interval.''',buttons=warn)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"gheiadmin")))
async def _(event):
     await event.edit('''──「 Here's help for ** Admin ** module 」──
Please chose your option.''',buttons=warn)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"promote"))) 
async def _(event):
    await event.edit('''** Promotes & Demotes**
- /promote (user) (?admin's title): Promotes the user to admin.
- /demote (user): Demotes the user from admin.
- /lowpromote: Promote a member with low rights
- /midpromote: Promote a member with mid rights
- /highpromote: Promote a member with max rights
- /lowdemote: Demote an admin to low permissions
- /middemote: Demote an admin to mid permissions''',buttons=warn) 

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"ban_kk")))
async def _(event):
    await event.edit('''** Bans & Kicks **
- /ban: bans a user
- /tban [entity] : temporarily bans a user for the time interval.
- /unban: unbans a user
- /unbanall: Unban all banned members
- /banme: Bans you
- /kick: kicks a user
- /kickme: Kicks you''',buttons=warn)

warn = [[custom.Button.inline("Admin bCommands", data="approve"), custom.Button.inline("User Commands", data="ucmds")]]
warn += [[custom.Button.inline("Warn Actions", data="actwar"),custom.Button.inline("Warn Limits", data="litwar")]]
warn += [[custom.Button.inline("Back", data="command")]]







Bax = [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]



#Admin


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"adminsm")))
async def _(event):
     await event.edit('''──「 Here's help for ** Admin ** module 」──
Lazy to promote or demote someone for admins? Want to see basic information about chat?
All stuff about chatroom such as admin lists, pinning or grabbing an invite link can be
done easily using the bot.''',buttons=warn)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"usercommand")))
async def _(event):
     await event.edit('''『 ** Users Commands ** 』
➥ /admins or /adminlist: list of admins in the chat..''',buttons=Reverse)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"admincommand")))
async def _(event):
     await event.edit('''『Admins Commands』
 ➥ /pin: Silently pins the message replied to - add loud, notify or violent to give notificaton to users.
 ➥ /unpin: Unpins the currently pinned message.
 ➥ /invitelink: Gets private chat's invitelink.
 ➥ /promote: Promotes the user replied to.
 ➥ /demote: Demotes the user replied to.
 ➥ /settitle: Sets a custom title for an admin which is promoted by bot.
 ➥ /setgpic: As a reply to file or photo to set group profile pic!
 ➥ /delgpic: Same as above but to remove group profile pic.
 ➥ /setgtitle <newtitle>: Sets new chat title in your group.
 ➥ /setsticker: As a reply to some sticker to set it as group sticker set!
 ➥ /setdescription: <description> Sets new chat description in group.
Note: To set group sticker set chat must needs to have min 100 members.
An example of promoting someone to admins:
/promote @username; this promotes a user to admins.''',buttons=Reverse)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"taggers")))
async def _(event):
     await event.edit('''──「 Here's help for Tagger module 」──
Tagger is an essential feature to mention all subscribed members in the group. Any chat members can subscribe to tagger.
➥ /tagme: registers to the chat tag list.
➥ /untagme: unsubscribes from the chat tag list.
『Admin Commands』
➥ /tagall: mention all subscribed members.
➥ /untagall: clears all subscribed members. 
➥ `/addtag` <userhandle>: add a user to chat tag list. (via handle, or reply)
➥ /removetag  <userhandle>: remove a user to chat tag list. (via handle, or reply)''',buttons=Reverse)




warn = [[custom.Button.inline("Admin Commands", data="admincommand"), custom.Button.inline("User Commands", data="usercommand")]]
warn += [[custom.Button.inline("Approval", data="approve"),custom.Button.inline("Tagger",data="taggers"),custom.Button.inline("Warning",data="warnsi")]]
warn += [[custom.Button.inline("Anti-flood", data="flood")]]
warn += [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]


Reverse = [[custom.Button.inline("Back", data="adminsm"), custom.Button.inline("Home", data="suru")]]



#feredations


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"fered")))
async def _(event):
     await event.edit('''──「 Here's help for **Federations** module 」──
Everything is fun, until a spammer starts entering your group, and you have to block it. Then you need to start banning more, and more, and it hurts.
But then you have many groups, and you don't want this spammer to be in one of your groups - how can you deal? Do you have to manually block it, in all your groups?
No longer! With Federation, you can make a ban in one chat overlap with all other chats.
You can even designate federation admins, so your trusted admin can ban all the spammers from chats you want to protect.''',buttons=Feds)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"fadmin")))
async def _(event):
     await event.edit('''『 Fed Admins 』
➥ /fban <user> <reason>: Fed bans a user
➥ /unfban <user> <reason>: Removes a user from a fed ban
➥ /fedinfo <fed-id>: Information about the specified Federation
➥ /joinfed <fed-id>: Join the current chat to the Federation. Only chat owners can do this. Every chat can only be in one Federation
➥ /leavefed <fed-id>: Leave the Federation given. Only chat owners can do this
➥ /setfrules <rules>: Arrange Federation rules
➥ /fednotif <on/off>: Federation settings not in PM when there are users who are fbaned/unfbanned
➥ /frules: See Federation regulations
➥ /fedadmins: Show Federation admin
➥ /fbanlist: Displays all users who are victimized at the Federation at this time
➥ /fedchats: Get all the chats that are connected in the Federation.''',buttons=Freverse)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"fuser")))
async def _(event):
     await event.edit('''『 Fed Users 』
➥ /fbanstat: Shows if you/or the user you are replying to or their username is fbanned somewhere or not
➥ /chatfed: See the Federation in the current chat.''',buttons=Freverse)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"fowner")))
async def _(event):
     await event.edit('''『 **Fed Owner** 』
➥ `/newfed <fed-name>` :  Creates a Federation, One allowed per user
➥ `/ftransfer <reply-fed-admin>` : transfer fed to one of our fed admin
➥ `/renamefed <fed-id> <new-fed-name>` : Renames the fed id to a new name
➥ `/delfed <fed-id>`:  Delete a Federation, and any information related to it. Will not cancel blocked users 
➥ /fpromote <user-id> :Assigns the user as a federation admin. Enables all commands for the user under Fed Admins
➥ `/fdemote <user>` : Drops the User from the admin Federation to a normal User
➥ `/subfed <fed-id>` : Subscribes to a given fed ID, bans from that subscribed fed will also happen in your fed
➥ `/unsubfed <fed-id>` : Unsubscribes to a given fed ID
➥ `/fedexport <fed-id>`  : export fed banlist from current fed
➥ `/fedimport <fed-id>` :  import fed banlist from current fed
➥ `/setfedlog <fed-id>` : Sets the group as a fed log report base for the federation
➥ `/unsetfedlog <fed-id>`:  Removed the group as a fed log report base for the federation
➥ `/fbroadcast <message>` : Broadcasts a messages to all groups that have joined your fed
➥ `/fedsubs` : Shows the feds your group is subscribed too.''',buttons=Freverse)


Feds = [[custom.Button.inline("Fed Owner", data="fowner"), custom.Button.inline("Fed Admin", data="fadmin")]]
Feds += [[custom.Button.inline("Fed Users", data="fuser")]]
Feds += [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]

Freverse = [[custom.Button.inline("Back", data="fered"), custom.Button.inline("Home", data="suru")]]

#Warning

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"warnsi")))
async def _(event):
     await event.edit('''──「 Here's help for **Warnings** module 」──
 If you're looking for a way to automatically warn users when they say certain things, use the /addwarn command.
 An example of setting multiword warns filter:
➥ /addwarn "very angry" This is an angry user
 This will automatically warn a user that triggers "very angry", with reason of 'This is an angry user'.
 An example of how to set a new multiword warning:
/warn @user Because warning is fun
➥ /warns <userhandle>: Gets a user's number, and reason, of warnings.
➥ /warnlist: Lists all current warning filters
**『Admins Commands』**
➥ /warn <userhandle>: Warns a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
➥ /resetwarn <userhandle>: Resets the warnings for a user. Can also be used as a reply.
➥ /rmwarn <userhandle>: Removes latest warn for a user. It also can be used as reply.
➥ /unwarn <userhandle>: Same as /rmwarn
➥ /addwarn <keyword> <reply message>: Sets a warning filter on a certain keyword. If you want your keyword to be a sentence, encompass it with quotes, as such: /addwarn "very angry" This is an angry user. 
➥ /nowarn <keyword>: Stops a warning filter
➥ /warnlimit <num>: Sets the warning limit
➥ /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick.''',buttons=Bax)


#Rules

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"rulesi")))
async def _(event):
     await event.edit('''──「 Here's help for **Rules** module 」──
Every chat works with different rules; this module will help make those rules clearer!
➥ `/rules`: get the rules for this chat.
**『Admins Commands』**
➥ `/setrules <your rules here>`: Sets rules for the chat.
➥ `/clearrules`: Clears saved rules for the chat.''',buttons=Bax)



#Logger


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"loggersi")))
async def _(event):
     await event.edit('''──「 Here's help for **Logger** module 」──
Recent actions are nice, but they don't help you log every action taken by the bot. This is why you need log channels!
Log channels can help you keep track of exactly what the other admins are doing. Bans, Mutes, warns, notes - everything can be moderated.
**『Admins Commands』**
➥ /logchannel: Get log channel info
➥ /setlog: Set the log channel.
➥ /unsetlog: Unset the log channel.
Setting the log channel is done by:
- Add the bot to your channel, as an admin. This is done via the "add administrators" tab.
- Send /setlog to your channel.
- Forward the /setlog command to the group you wish to be logged.
- Congratulations! All is set!.''',buttons=Bax)



#Notes

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"notesi")))
async def _(event):
     await event.edit('''──「 Here's help for **Notes** module 」──
Save data for future users with notes!
Notes are great to save random tidbits of information; a phone number, a nice gif, a funny picture - anything!
➥ `/get <notename>`: Get the note with this notename
 - #<notename>: Same as /get
➥ `/notes or /saved`: Lists all saved notes in the chat
If you would like to retrieve the contents of a note without any formatting, use /get <notename> noformat. This can be useful when updating a current note.
**『Admins Commands』**
➥ `/save <notename> <notedata>`: Saves notedata as a note with name notename
A button can be added to a note by using standard markdown link syntax - the link should just be prepended with a buttonurl: section, as such: `[somelink](buttonurl:example.com)`. Check `/markdownhelp` for more info.
➥ `/save <notename>`: Saves the replied message as a note with name notename
➥ `/clear <notename>`: Clears note with this name
**『Owner Commands』**
➥ `/clearall`: Clear all notes saved in chat at once.
 An example of how to save a note would be via:
/save Data This is some data!
Now, anyone using "/get notedata", or "#notedata" will be replied to with "This is some data!".
If you want to save an image, gif, or sticker, or any other data, do the following:
➥ `/save` notename while replying to a sticker or whatever data you'd like. Now, the note at "#notename" contains a sticker which will be sent as a reply.
Tip: to retrieve a note without the formatting, use /get <notename> noformat
This will retrieve the note and send it without formatting it; getting you the raw markdown, allowing you to make easy edits.''',buttons=Bax)


#purges


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"purgesi")))
async def _(event):
     await event.edit('''──「 Here's help for **Purges** module 」──
Deleting messages made easy with this command. Bot purges messages all together or individually.
**『Admins Commands』**
➥ /del: Deletes the message you replied to
➥ /purge: Deletes all messages between this and the replied to message.''',buttons=Freverse)



#Reporting


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"rpot")))
async def _(event):
     await event.edit('''──「 Here's help for **Reporting** module 」──
We're all busy people who don't have time to monitor our groups 24/7. But how do you react if someone in your group is spamming?
Presenting reports; if someone in your group thinks someone needs reporting, they now have an easy way to call all admins.
**『Admins Commands』**
➥ '/reports <on/off>': Change report setting, or view current status.
   • If done in pm, toggles your status.
   • If in chat, toggles that chat's status.
To report a user, simply reply to user's message with @admin or /report. This message tags all the chat admins; same as if they had been @'ed.
You MUST reply to a message to report a user; you can't just use @admin to tag admins for no reason!
Note that the report commands do not work when admins use them; or when used to report an admin. Bot assumes that admins don't need to report, or be reported!.''',buttons=Bax)

#anti-spam


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"antispams")))
async def _(event):
     await event.edit('''──「 Here's help for **Anti-Spam** module 」──
Anti-Spam, used by bot devs to ban spammers across all groups. This helps protect
you and your groups by removing spam flooders as quickly as possible.
**『Admin Commands』**
➥ `/antispam <on/off/yes/no>`: Will toggle our antispam tech or return your current settings.
NOTE: Users can appeal gbans or report spammers at @ShokoSupports
This also integrates @Spamwatch API to remove Spammers as much as possible from your chatroom!
**『What is SpamWatch?』**
SpamWatch maintains a large constantly updated ban-list of spambots, trolls, bitcoin spammers and unsavoury characters.
Constantly help banning spammers off from your group automatically So, you wont have to worry about spammers storming your group.
NOTE: Users can appeal spamwatch bans at @SpamwatchSupport.''',buttons=Bax)


#Formatting

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"filsi")))
async def _(event):
     await event.edit('''──「 **Fillings** 」──
You can also customise the contents of your message with contextual data. For example, you could mention a user by name in the welcome message, or mention them in a filter!
You can use these to mention a user in notes too!
**Supported fillings:**
➥ `{first}`: The user's first name.
➥ `{last}`: The user's last name.
➥ `{fullname}`: The user's full name.
➥ `{username}`: The user's username. If they don't have one, mentions the user instead.
➥ `{mention}`: Mentions the user with their firstname.
➥ `{id}`: The user's ID.
➥ `{chatname}`: The chat's name.
➥ `{rules}`: Adds rules button to message.''',buttons=forreverse)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"romsi")))
async def _(event):
     await event.edit('''──「 **Random Content** 」──
Another thing that can be fun, is to randomise the contents of a message. Make things a little more personal by changing filter messages, or changing notes!
**How to use random contents:**
➥ %%%: This separator can be used to add "random" replies to the bot.
**For example:*"
hello
%%%
how are you
This will randomly choose between sending the first message, "hello", or the second message, "how are you". Use this to make Shoko feel a bit more customised! (only works in notes/filters/welcome)
**Example welcome message:**
➥ Every time a new user joins, they'll be presented with one of the three messages shown here.
➥ `/setwelcome`
Hai `{first}`, how are you.
%%%
OwO, `{first}` is join to chatroom.
%%%
Welcome to the group, `{first}`.''',buttons=forreverse)




@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"mfd")))
async def _(event):
     await event.edit('''──「 **Markdown Formatting** 」──
You can format your message using *bold*, _italics_, -underline-, and much more. Go ahead and experiment!
**Supported markdown:**
➥ code words: Backticks are used for monospace fonts. Shows as: code words.
➥ _italic words_: Underscores are used for italic fonts. Shows as: italic words.
➥ *bold words*: Asterisks are used for bold fonts. Shows as: bold words.
➥ ~strikethrough~: Tildes are used for strikethrough. Shows as: strikethrough.
➥ `[hyperlink](example.com)`: This is the formatting used for hyperlinks. Shows as: hyperlink.
➥ `[My Button](buttonurl://example.com)`: This is the formatting used for creating buttons. This example will create a button named "My button" which opens example.com when clicked.
If you would like to send buttons on the same row, use the :same formatting.
**Example:**
`[button 1](buttonurl://example.com)`
`[button 2](buttonurl://example.com:same)`
`[button 3](buttonurl://example.com)`
This will show button 1 and 2 on the same line, with 3 underneath.''',buttons=forreverse)




@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"fm")))
async def _(event):
     await event.edit('''──「 Here's help for **Formatting** module 」──
Shoko supports a large number of formatting options to make your messages more expressive. Take a look!.''',buttons=Fmd)

Fmd = [[custom.Button.inline("Markdown Formatting", data="mfd"), custom.Button.inline("Fillings", data="filsi")]]
Fmd += [[custom.Button.inline("Random Content", data="romsi")]]
Fmd += [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]

forreverse = [[custom.Button.inline("Back", data="fm"), custom.Button.inline("Home", data="suru")]]


#Extras


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"ex")))
async def _(event):
     await event.edit('''──「 Here's help for **Extras** module 」──
Chose your option.''',buttons=Exb)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"memes")))
async def _(event):
     await event.edit('''──「 Here's help for **Memes** module 」──
Some dank memes for fun or whatever!
➥ /shrug | /cri: Get shrug or ToT.
➥ /decide: Randomly answer yes no etc.
➥ /abuse: Abuses the retard!
➥ /table: Flips a table...
➥ /runs: Reply a random string from an array of replies.
➥ /slap: Slap a user, or get slapped if not a reply.
➥ /pasta: Famous copypasta meme, try and see.
➥ /clap: Claps on someones message!➥ /owo: UwU-fy whole text XD.
➥ /roll: Rolls a dice.
➥ /recite: Logical quotes to change your life.
➥ /stretch:  streeeeeeetch iiiiiiit.
➥ /warm: Hug a user warmly, or get hugged if not a reply.
Regex based memes:
➥ decide can be also used with regex like: Shoko? <question>: randomly answer "Yes, No" etc.
Some other regex filters are:
me too | goodmorning,gm,good morning | goodnight.
Shoko will reply random strings accordingly when these words are used!
All regex filters can be disabled incase u don't want... like: /disable metoo.''',buttons=rxras)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"pbio")))
async def _(event):
     await event.edit('''──「 **Bois/Abouts** 」──
Writing something about yourself is cool, whether to make people know about yourself or promoting your profile.
All bios are displayed on /info command.
➥ /setbio <text>: While replying, will save another op it user's bio
➥ /bio: Will get your or another user's bio. This cannot be set by yourself.
➥ /setme <text>: Will set your info
➥ /me: Will get your or another user's info
An example of setting a bio for yourself:
/setme I work for Telegram; Bio is set to yourself.
An example of writing someone else' bio:
Reply to user's message: /setbio He is such cool person.
Notice: Do not use /setbio against yourself!''',buttons=rxras)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"miscs")))
async def _(event):
     await event.edit('''──「 Here's help for *"Miscs** module 」──
An "odds and ends" module for small, simple commands which don't really fit anywhere
➥ /id: Get the current group id. If used by replying to a message, gets that user's id.
➥ /info: Get information about a user.
➥ /wiki : Search wikipedia articles.
➥ /rmeme: Sends random meme scraped from reddit.
➥ /ud <query> : Search stuffs in urban dictionary.
➥ /wall <query> : Get random wallpapers directly from bot! 
➥ /reverse : Reverse searches image or stickers on google.
➥ /gdpr: Deletes your information from the bot's database. Private chats only.
➥ /markdownhelp: Quick summary of how markdown works in telegram - can only be called in private chats.
 **Translator**
➥ /tr or /tl: - To translate to your language, by default language is set to english, use /tr <lang code> for some other language!
➥ /tr hi-en: translates hindi to english
➥ /splcheck: - As a reply to get grammar corrected text of gibberish message.
➥ /tts: - To some message to convert it into audio format!
 **Weather**
➥ /weather <city>: Gets weather information of particular place!
  * To prevent spams weather command and the output will be deleted after 30 seconds.''',buttons=rxras)

Exb = [[custom.Button.inline("Miscs", data="miscs"), custom.Button.inline("Bio/About", data="pbio")]]
Exb += [[custom.Button.inline("Memes", data="memes"),custom.Button.inline("android",data="androidsi"),custom.Button.inline("Strickers",data="strickers")]]
Exb += [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]

rxras = [[custom.Button.inline("Back", data="ex"), custom.Button.inline("Home", data="suru")]]



#Filter

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"filters")))
async def _(event):
     await event.edit('''──「 Here's help for **Filters** module 」──
➥ `/filters`: List all active filters saved in the chat.
**『Admins Commands』**
➥ `/filter <keyword> <reply message>`: Add a filter to this chat. The bot will now reply that message whenever 'keyword'is mentioned. If you reply to a sticker with a keyword, the bot will reply with that sticker. NOTE: all filter keywords are in lowercase. If you want your keyword to be a sentence, use quotes. eg: /filter "hey there" How you doin?
➥ `/stop <filter keyword>`: Stop that filter.
**『Owner Commands』**
➥ /stopall: Stop all chat filters at once.
Note: Filters also support markdown formatters like: {first}, {last} etc.. and buttons.
Check `/markdownhelp` to know more!''',buttons=Bax)

#Disable

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"disables")))
async def _(event):
     await event.edit('''──「 Here's help for **Disable** module 」──
Not everyone wants every feature that the bot offers. Some commands are best left unused; to avoid spam and abuse.
This allows you to disable some commonly used commands, so noone can use them. It'll also allow you to autodelete them, stopping people from bluetexting.
➥ `/cmds`: Check the current status of disabled commands
**『Admins Commands』**
➥ `/enable <cmd name>`: Enable that command
➥ `/disable <cmd name>`: Disable that command
➥ `/listcmds`: List all possible disablable commands.''',buttons=Bax)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"greetings")))
async def _(event):
     await event.edit('''──「 Here's help for **Greetings** module 」──
Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages to be individually generated, like the default welcome message is, you can use these variables:
 • `{first}`: this represents the user's first name
 • `{last}`: this represents the user's last name. Defaults to first name if user has no last name.
 • `{fullname}`: this represents the user's full name. Defaults to first name if user has no last name.
 • `{username}`: this represents the user's username. Defaults to a mention of the user's first name if has no username.
 • `{mention}`: this simply mentions a user - tagging them with their first name.
 • `{id}`: this represents the user's id
 • `{count}`: this represents the user's member number.
 • `{chatname}`: this represents the current chat name.
Each variable MUST be surrounded by `{}` to be replaced.
Welcome messages also support markdown, so you can make any elements bold/italic/code/links. Buttons are also supported, so you can make your welcomes look awesome with some nice intro buttons.
To create a button linking to your rules, use this: [Rules](buttonurl://t.me/ShokoGbot?start=group_id). Simply replace group_id with your group's id, which can be obtained via /id, and you're good to go. Note that group ids are usually preceded by a - sign; this is required, so please don't remove it.
If you're feeling fun, you can even set images/gifs/videos/voice messages as the welcome message by replying to the desired media, and calling /setwelcome.
**『Admins Commands』**
➥ `/welcome <on/off>`: enable/disable Welcome messages.
➥ `/welcome`: Shows current welcome settings.
➥ `/welcome` noformat: Shows current welcome settings, without the formatting - useful to recycle your welcome messages!
➥ `/goodbye` -> Same usage and args as /welcome.
➥ `/setwelcome <sometext>`: Sets a custom welcome message. If used replying to media, uses that media.
➥ `/setgoodbye <sometext>`: Sets a custom goodbye message. If used replying to media, uses that media.
➥ `/resetwelcome`: Resets to the default welcome message.
➥ `/resetgoodbye`: Resets to the default goodbye message.
➥ `/cleanwelcome <on/off>`: On new member, try to delete the previous welcome message to avoid spamming the chat.
➥ `/cleanservice <on/off>`: Clean 'user is joined' service messages automatically.
➥ `/welcomemute <off/soft/strong>`: All users that join, get muted; a button gets added to the welcome message for them to unmute themselves. This proves they aren't a bot! soft - restricts users ability to post media for 24 hours. strong - mutes on join until they prove they're not bots.
➥ `/welcomehelp`: View more formatting information for custom welcome/goodbye messages.
Buttons in welcome messages are made easy, everyone hates URLs visible. With button links you can make your chats look more tidy and simplified.
**An example of using buttons**:
You can create a button using `[button text](buttonurl://example.com)`.
If you wish to add more than 1 buttons simply do the following:
`[Button 1](buttonurl://example.com)`
`[Button 2](buttonurl://github.com:same)`
`[Button 3](buttonurl://google.com)`
The :same end of the link merges 2 buttons on same line as 1 button, resulting in 3rd button to be separated from same line.
Tip: Buttons must be placed at the end of welcome messages.''',buttons=gpo)

gpo = [[custom.Button.inline("Formating", data="fm")]]
gpo += [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"strickers")))
async def _(event):
     await event.edit('''──「 Here's help for **Stickers** module 」──
Stickers made easy with stickers module!
➥ `/addsticker`: Reply to a sticker to add it to your pack.
➥ `/delsticker`: Reply to your anime exist sticker to your pack to delete it.
➥ `/stickerid`: Reply to a sticker to me to tell you its file ID.
➥ `/getsticker`: Reply to a sticker to me to upload its raw PNG file.
➥ `/addfsticker | afs <custom name>`: Reply to a sticker to add it into your favorite pack list.
➥ `/myfsticker | mfs`: Get list of your favorite packs.
➥ `/removefsticker | rfs <custom name>`: Reply to a sticker to remove it into your favorite pack list.
**Example:** `/addfsticker` my cat pack.''',buttons=rxras)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"anime")))
async def _(event):
     await event.edit('''──「 Here's help for **Anime** module 」──
Get information about anime, manga or characters from AniList.
Available commands
➥ `/anime <anime>|: returns information about the anime.
➥ `/character <character>`: returns information about the character.
➥ `/manga <manga>`: returns information about the manga.
➥ `/user <user>`: returns information about a MyAnimeList user.
➥ `/upcoming`: returns a list of new anime in the upcoming seasons.
➥ `/airing <anime>`: returns anime airing info.
➥ `/watchlist`: to get your saved watchlist.
➥ `/mangalist`: to get your saved manga read list.
➥ `/characterlist | fcl`: to get your favorite characters list.
➥ `/removewatchlist | rwl <anime>: to remove a anime from your list.
➥ `/rfcharacter | rfcl <character>`: to remove a character from your list.  
➥ `/rmanga | rml <manga>`: to remove a manga from your list.''',buttons=Bax)

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"androidsi")))
async def _(event):
     await event.edit('''──「 Here's help for **Android** module 」──
Get Latest magisk relese, Twrp for your device or info about some device using its codename, Directly from Bot!
Android related commands:
➥ '/magisk' - Gets the latest magisk release for Stable/Beta/Canary.
➥ '/device <codename>' - Gets android device basic info from its codename.
➥ '/twrp <codename>' -  Gets latest twrp for the android device using the codename.''',buttons=rxras)



#help


buttonsi = [[custom.Button.url("Updates","t.me/ShokoUpdates"), custom.Button.url("Support","t.me/Shokosupports")]]
buttonsi += [[custom.Button.url("Network","t.me/shokonetwork")]]
buttonsi += [[custom.Button.inline("Back", data="suru")]]

#Rewrite start message

@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"advances")))
async def _(event):
     await event.edit('''**Shoko is a bot for managing your group with additional features,**
__and is fork of marie.__
__Shoko's licensed under the GNU General Public License v3.0,
here is the repository.__
__If any question about Shoko, let us know at @Shokosupports.__''',buttons=Adv)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"TC")))
async def _(event):
     await event.edit('''**Terms and Conditions:**
To use this bot, you need to read Terms and Conditions
- Watch your group, if someone spamming your group, you can use report feature from your Telegram Client.
- Make sure antiflood is enabled, so nobody can ruin your group.
- Do not spam commands, buttons, or anything in bot PM, else you will be Gbanned.
- If you need to ask anything about this bot, Go @Shokosupports.
- If you asking nonsense in @Shokosupports, you will get banned.
- Sharing any files/videos others than about bot in @Shokosupports is prohibited.
- Sharing NSFW in @Shokosupports will reward you banned/gbanned and reported to Telegram as well.
For any kind of help, related to this bot, Join @ShokoSupports.
__Terms and Conditions will be changed anytime__
Follow @ShokoUpdates for Updates.
Follow @SHOKONETWORK to get info about bots.__''',buttons=Advs)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"BH")))
async def _(event):
     await event.edit('''**Basic help:**
__To add Shoko to your chats, simply click here  and select your chat.
You can also click on @ShokoGBot, and go to the three dots on the top right of your screen, and select 'add to group'__.''',buttons=dvs)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"ASPS")))
async def _(event):
     await event.edit('''**Anti-spam settings:**
- /antispam <on/off/yes/no>: Change antispam security settings in the group, or return your current settings(when no arguments).
This helps protect you and your groups by removing spam flooders as quickly as possible.
- /setflood <int/'no'/'off'>: enables or disables flood control
- /setfloodmode <ban/kick/mute/tban/tmute> <value>: Action to perform when user have exceeded flood limit. ban/kick/mute/tmute/tban
Antiflood allows you to take action on users that send more than x messages in a row. Exceeding the set flood will result in restricting that user.
- /addblacklist <triggers>: Add a trigger to the blacklist. Each line is considered one trigger, so using different lines will allow you to add multiple triggers.
- /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>: Action to perform when someone sends blacklisted words.
Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!
- /reports <on/off>: Change report setting, or view current status.
 • If done in pm, toggles your status.
 • If in chat, toggles that chat's status.
If someone in your group thinks someone needs reporting, they now have an easy way to call all admins.
- /lock <type>: Lock items of a certain type (not available in private)
- /locktypes: Lists all possible locktypes
The locks module allows you to lock away some common items in the telegram world; the bot will automatically delete them!
- /addwarn <keyword> <reply message>: Sets a warning filter on a certain keyword. If you want your keyword to be a sentence, encompass it with quotes, as such: /addwarn "very angry" This is an angry user. 
- /warn <userhandle>: Warns a user. After 3 warns, the user will be banned from the group. Can also be used as a reply.
- /strongwarn <on/yes/off/no>: If set to on, exceeding the warn limit will result in a ban. Else, will just kick.
If you're looking for a way to automatically warn users when they say certain things, use the /addwarn command.
- /welcomemute <off/soft/strong>: All users that join, get muted
 A button gets added to the welcome message for them to unmute themselves. This proves they aren't a bot! soft - restricts users ability to post media for 24 hours. strong - mutes on join until they prove they're not bots.''',buttons=Advs)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"APS")))
async def _(event):
     await event.edit(''' **Admin permissions:**
To avoid slowing down, Shoko caches admin rights for each user. This cache lasts about 10 minutes; this may change in the future. This means that if you promote a user manually (without using the /promote command), Shoko will only find out ~10 minutes later.
If you are getting a message saying:
You must be this chat administrator to perform this action!
This has nothing to do with Shoko's rights; this is all about YOUR permissions as an admin. Shoko respects admin permissions; if you do not have the Ban Users permission as a telegram admin, you won't be able to ban users with Shoko. Similarly, to change Shoko settings, you need to have the Change group info permission.
The message very clearly says that you need these rights - not Shoko.''',buttons=Advs)


Adv = [[custom.Button.inline("How to use ❓", data="BH"), custom.Button.inline("Terms and Conditions", data="TC")]]
Adv += [[custom.Button.inline("Back", data="suru")]]

Advs = [[custom.Button.inline("Back", data="advances")]]

dvs = [[custom.Button.inline("Admin permissions", data="APS"), custom.Button.inline("Anti-spam settings", data="ASPS")]]
dvs += [[custom.Button.inline("Back", data="advances")]]



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"SSP")))
async def _(event):
     await event.edit('''This is all Shoko Support groups..''',buttons=buttonsi)

#vocie chat 


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"Music")))
async def _(event):
     await event.edit('''──「 Here's help for **Music** module 」──
Chose your option.''',buttons=VC)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"PSG")))
async def _(event):
     await event.edit('''=>> **Song Playing 🎧**
- /play: Play the requestd song
- /play [yt url] : Play the given yt url
- /play [reply yo audio]: Play replied audio
- /dplay: Play song via deezer
- /splay: Play song via jio saavn
- /ytplay: Directly play song via Youtube Music
**=>> Playback** ⏯
- /player: Open Settings menu of player
- /skip: Skips the current track
- /pause: Pause track
- /resume: Resumes the paused track
- /end: Stops media playback
- /current: Shows the current Playing track
- /playlist: Shows playlist
*Player cmd and all other cmds except /play, /current  and /playlist  are only for admins of the group.''',buttons=VCC)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"Songs")))
async def _(event):
     await event.edit('''──「 Here's help for **Songs** module 」──
• /song <songname artist(optional)>: download the song in it's best quality available.(API BASED)
• /video <songname artist(optional)>: download the video song in it's best quality available.
• /lyrics <songname artist(optional)>: sends the complete lyrics of the song provided as input.''',buttons=VCR)



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"CMP")))
async def _(event):
     await event.edit('''=>> Channel Music Play 🛠
⚪️ For linked group admins only:
- /cplay [song name] - play song you requested
- /cdplay [song name] - play song you requested via deezer
- /csplay [song name] - play song you requested via jio saavn
- /cplaylist - Show now playing list
- /cccurrent - Show now playing
- /cplayer - open music player settings panel
- /cpause - pause song play
- /cresume - resume song play
- /cskip - play next song
- /cend - stop music play
- /userbotjoinchannel - invite assistant to your chat
channel is also can be used instead of c ( /cplay = /channelplay )
⚪️ If you donlt like to play in linked group:
1) Get your channel ID.
2) Create a group with tittle: Channel Music: your_channel_id
3) Add bot as Channel admin with full perms
4) Add @Shokoxhelper to the channel as an admin.
5) Simply send commands in your group.
Setting up
1) Make bot admin (Group and in channel if use cplay)
2) Start a voice chat
3) Try /play [song name] for the first time by an admin
*) If userbot joined enjoy music, If not add @Shokoxhelper to your group and retry
For Channel Music Play
1) Make me admin of your channel 
2) Send /userbotjoinchannel in linked group
3) Now send commands in linked group
Commands''',buttons=VCR)

VC = [[custom.Button.inline("Music player", data="PSG"), custom.Button.inline("Songs", data="Songs")]]
VC += [[custom.Button.inline("Back", data="command"), custom.Button.inline("Home", data="suru")]]

VCC = [[custom.Button.inline("Channel Music Player", data="CMP")]]
VCC += [[custom.Button.inline("Back", data="PSG"), custom.Button.inline("Home", data="suru")]]


VCR = [[custom.Button.inline("Back", data="Music"), custom.Button.inline("Home", data="suru")]]

#Bans & Locks


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"Locks"))) 
async def _(event):
    await event.edit('''──「 Here's help for *"Locks** module 」──
Do stickers annoy you? or want to avoid people sharing links? or pictures? You're in the right place!
The locks module allows you to lock away some common items in the telegram world; the bot will automatically delete them!
➥ `/locktypes`: Lists all possible locktypes
 
**『Admins Commands』**
➥ `/lock <type>`: Lock items of a certain type (not available in private)
➥ `/unlock <type>`: Unlock items of a certain type (not available in private)
➥ `/locks`: The current list of locks in this chat.
 
Locks can be used to restrict a group's users.
eg:
Locking urls will auto-delete all messages with urls, locking stickers will restrict all non-admin users from sending stickers, etc.
Locking bots will stop non-admins from adding bots to the chat.
**Note*":
 __• Unlocking permission info will allow members (non-admins) to change the group information, such as the description or the group name
 • Unlocking permission pin will allow members (non-admins) to pinned a message in a group__''', buttons=Bax) 



@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"Bans"))) 
async def _(event):
    await event.edit('''──「 Here's help for **Bans** module 」──
Some people need to be publicly banned; spammers, annoyances, or just trolls.
This module allows you to do that easily, by exposing some common actions, so everyone will see!
➥ `/kickme`: Kicks the user who issued the command
➥ `/banme`: Bans the user who issued the command
**『Admins Commands』**
➥ `/ban <userhandle>`: Bans a user. (via handle, or reply)
➥ `/tban <userhandle>` x(m/h/d): Bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
➥ `/unban <userhandle>`: Unbans a user. (via handle, or reply)
➥ `/kick <userhandle>`: Kicks a user, (via handle, or reply)
➥ `/mute <userhandle>`: Silences a user. Can also be used as a reply, muting the replied to user.
➥ `/tmute <userhandle>` x(m/h/d): Mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
➥ `/unmute <userhandle>`: Unmutes a user. Can also be used as a reply, muting the replied to user. 
An example of temporarily banning someone:
`/tban @username 2h`; this bans a user for 2 hours.''', buttons=Bax) 














