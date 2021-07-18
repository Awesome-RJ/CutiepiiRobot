  
import io
from Cutiepii_Robot.events import register
from Cutiepii_Robot import telethn
from telethon import types
from telethon import events, Button
from telethon.tl import functions, types
from telethon.tl.types import *

MUSIC_HELP = """
**Hey 👋 Welcome back to Cutiepii
⚪️ Cutiepii can play music in your group's voice chat as well as channel voice chats
⚪️ Assistant name >> @Group_Music_Pro\n\nClick next for instructions**
"""

btn =[
    [Button.inline("Music Setting", data="MUSICSETTING"), 
    [Button.inline("Music Commands", data="user_help"),
    [Button.inline("Back", data="cutepii_back"),
    [Button.inline("Main Manu", data="back_back")]]]]]

@telethn.on(events.callbackquery.CallbackQuery(data="MUSIC_HELP"))
async def _(event):

    await event.edit(MUSIC_HELP, buttons=btn)

MUSICSETTING = """
**Setting up**
1) Make bot admin (Group and in channel if use cplay)
2) Start a voice chat
3) Try /play [song name] for the first time by an admin
*) If userbot joined enjoy music, If not add @Group_Music_Pro to your group and retry
**For Channel Music Play**
1) Make me admin of your channel 
2) Send /userbotjoinchannel in linked group
3) Now send commands in linked group
"""

@telethn.on(events.callbackquery.CallbackQuery(data="MUSICSETTING"))
async def _(event):

    await event.edit(MUSICSETTING, buttons=[
    [Button.inline("Back", data="MUSIC_HELP")]])

MUSICCOMMANDS = """
**Commands**
**=>> Song Playing 🎧**
- /play: Play the requestd song
- /play [yt url] : Play the given yt url
- /play [reply yo audio]: Play replied audio
- /dplay: Play song via deezer
- /splay: Play song via jio saavn
- /ytplay: Directly play song via Youtube Music
**=>> Playback ⏯**
- /player: Open Settings menu of player
- /skip: Skips the current track
- /pause: Pause track
- /resume: Resumes the paused track
- /end: Stops media playback
- /current: Shows the current Playing track
- /playlist: Shows playlist
*Player cmd and all other cmds except /play, /current  and /playlist  are only for admins of the group.
**=>> Channel Music Play 🛠**
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
4) Add @Group_Music_Pro to the channel as an admin.
5) Simply send commands in your group. (remember to use /ytplay instead /play)
**=>> More tools 🧑‍🔧**
- /musicplayer [on/off]: Enable/Disable Music player
- /admincache: Updates admin info of your group. Try if bot isn't recognize admin
- /userbotjoin: Invite @Group_Music_Pro Userbot to your chat
**=>> Song Download 🎸**
- /video [song mame]: Download video song from youtube
- /song [song name]: Download audio song from youtube
- /saavn [song name]: Download song from saavn
- /deezer [song name]: Download song from deezer
**=>> Search Tools 📄**
- /search [song name]: Search youtube for songs
- /lyrics [song name]: Get song lyrics
"""

@telethn.on(events.callbackquery.CallbackQuery(data="MUSICCOMMANDS"))
async def _(event):

    await event.edit(MUSICCOMMANDS, buttons=[
    [Button.inline("Back", data="MUSIC_HELP")]])
