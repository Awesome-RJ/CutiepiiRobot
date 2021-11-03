"""
MIT License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021 Awesome-RJ
Copyright (c) 2021, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

RUN_STRINGS = (
    "Now you see me, now you don't.", "ε=ε=ε=ε=┌(;￣▽￣)┘",
    "Get back here!",
    "REEEEEEEEEEEEEEEEEE!!!!!!!",
    "Look out for the wall!",
    "Don't leave me alone with them!!",
    "You've got company!",
    "Chotto matte!",
    "Yare yare daze",
    "*Naruto run activated*",
    "*Nezuko run activated*",
    "Hey take responsibilty for what you just did!",
    "May the odds be ever in your favour.",
    "Run everyone, they just dropped a bomb 💣💣",
    "And they disappeared forever, never to be seen again.",
    "Legend has it, they're still running.",
    "Hasta la vista, baby.",
    "Ah, what a waste. I liked that one.",
    "As The Doctor would say... RUN!",
)

GIFS = [
    "CgACAgQAAx0CSVUvGgAC7KpfWxMrgGyQs-GUUJgt-TSO8cOIDgACaAgAAlZD0VHT3Zynpr5nGxsE",
    "CgACAgUAAx0CU_rCTAABAjdgX1s4NVaeCls6YaH3p43vgdCRwQIAAqsAA4P_MFUYQhyoR-kgpRsE",
    "CgACAgUAAx0CU_rCTAABAjdSX1s3fq5iEJ64YeQLKI8cD7CSuSEAAlUBAAJu09hW5iqWB0hTPD4bBA",
]

SLAP_CUTIEPII_TEMPLATES = (
    "Slap me one more time and I'll mute you.",
    "Stop slapping me. REEEEEEEEEEEEEE.",
    [
        "I am muting you for a minute.",  # normal reply
        "Stop slapping me just because I can't mute you. REEEEEEEEEE.",  # reply to admin
        "tmute",  # command
        "Shut up!",
        "Silence!",
    ],
)

SLAP_TEMPLATES = (
    "{user2} was killed by magic.",
    "{user2} starved without pats.",
    "{user2} was knocked into the void by {user1}.",
    "{user2} fainted.",
    "{user2} is out of usable Pokemon! {user2} whited out!.",
    "{user2} is out of usable Pokemon! {user2} blacked out!.",
    "{user2} got rekt.",
    "{user2}'s melon was split by {user1}.",
    "{user2} was sliced and diced by {user1}.",
    "{user2} played hot-potato with a grenade.",
    "{user2} was knifed by {user1}.",
    "{user2} ate a grenade.",
    "{user2} is what's for dinner!",
    "{user2} was terminated by {user1}.",
    "{user1} spammed {user2}'s email.",
    "{user1} RSA-encrypted {user2} and deleted the private key.",
    "{user1} put {user2} in the friendzone.",
    "{user1} slaps {user2} with a DMCA takedown request!",
    "{user2} got a house call from Doctor {user1}.",
    "{user1} beheaded {user2}.",
    "{user2} got stoned...by an angry mob.",
    "{user1} sued the pants off {user2}.",
    "{user2} was one-hit KO'd by {user1}.",
    "{user1} sent {user2} down the memory hole.",
    "{user2} was a mistake. - '{user1}' ",
    "{user2} was made redundant.",
    "{user1} {hits} {user2} with a bat!.",
    "{user1} {hits} {user2} with a Taijutsu Kick!.",
    "{user1} {hits} {user2} with X-Gloves!.",
    "{user1} {hits} {user2} with a Jet Punch!.",
    "{user1} {hits} {user2} with a Jet Pistol!.",
    "{user1} {hits} {user2} with a United States of Smash!.",
    "{user1} {hits} {user2} with a Detroit Smash!.",
    "{user1} {hits} {user2} with a Texas Smash!.",
    "{user1} {hits} {user2} with a California Smash!.",
    "{user1} {hits} {user2} with a New Hampshire Smash!.",
    "{user1} {hits} {user2} with a Missouri Smash!.",
    "{user1} {hits} {user2} with a Carolina Smash!.",
    "{user1} {hits} {user2} with a King Kong Gun!.",
    "{user1} {hits} {user2} with a baseball bat - metal one.!.",
    "*Serious punches {user2}*.",
    "*Normal punches {user2}*.",
    "*Consecutive Normal punches {user2}*.",
    "*Two Handed Consecutive Normal Punches {user2}*.",
    "*Ignores {user2} to let them die of embarassment*.",
    "*points at {user2}* What's with this sassy... lost child?.",
    "*Hits {user2} with a Fire Tornado*.",
    "{user1} pokes {user2} in the eye !",
    "{user1} pokes {user2} on the sides!",
    "{user1} pokes {user2}!",
    "{user1} pokes {user2} with a needle!",
    "{user1} pokes {user2} with a pen!",
    "{user1} pokes {user2} with a stun gun!",
    "{user2} is secretly a Furry!",
    "Hey Everybody! {user1} is asking me to be mean!",
    "( ･_･)ﾉ⌒●~* (･.･;) <-{user2}",
    "Take this {user2}\n(ﾉﾟДﾟ)ﾉ ))))●~* ",
    "Here {user2} hold this\n(｀・ω・)つ ●~＊",
    "( ・_・)ノΞ●~*  {user2}\nDieeeee!!.",
    "( ・∀・)ｒ鹵~<≪巛;ﾟДﾟ)ﾉ\n*Bug sprays {user2}*.",
    "( ﾟДﾟ)ﾉ占~<巛巛巛.\n-{user2} You pest!",
    r"( う-´)づ︻╦̵̵̿╤── \(˚☐˚”)/ {user2}.",
    "{user1} {hits} {user2} with a {item}.",
    "{user1} {hits} {user2} in the face with a {item}.",
    "{user1} {hits} {user2} around a bit with a {item}.",
    "{user1} {throws} a {item} at {user2}.",
    "{user1} grabs a {item} and {throws} it at {user2}'s face.",
    "{user1} launches a {item} in {user2}'s general direction.",
    "{user1} starts slapping {user2} silly with a {item}.",
    "{user1} pins {user2} down and repeatedly {hits} them with a {item}.",
    "{user1} grabs up a {item} and {hits} {user2} with it.",
    "{user1} ties {user2} to a chair and {throws} a {item} at them.",
    "{user1} gave a friendly push to help {user2} learn to swim in lava.",
    "{user1} bullied {user2}.",
    "Nyaan ate {user2}'s leg. *nomnomnom*",
    "{user1} {throws} a master ball at {user2}, resistance is futile.",
    "{user1} hits {user2} with an action beam...bbbbbb (ง・ω・)ง ====*",
    "{user1} ara ara's {user2}.",
    "{user1} ora ora's {user2}.",
    "{user1} muda muda's {user2}.",
    "{user2} was turned into a Jojo reference!",
    "{user1} hits {user2} with {item}.",
    "Round 2!..Ready? .. FIGHT!!",
    "WhoPixel will oof {user2} to infinity and beyond.",
    "{user2} ate a bat and discovered a new disease.",
    "{user1} folded {user2} into a paper plane",
    "{user1} served {user2} some bat soup.",
    "{user2} was sent to their home, the planet of the apes.",
    "{user1} kicked {user2} out of a moving train.",
    "{user2} just killed John Wick’s dog.",
    "{user1} performed an Avada Kedavra spell on {user2}.",
    "{user1} subjected {user2} to a fiery furnace.",
    "Sakura Haruno just got more useful than {user2}",
    "{user1} unplugged {user2}'s life support.",
    "{user1} subscribed {user2}' to 5 years of bad internet.",
    "You know what’s worse than Dad jokes? {user2}!",
    "{user1} took all of {user2}'s cookies.",
    "{user2} wa mou.......Shindeiru! - {user1}.",
    "{user2} lost their race piece!",  # No game no life reference
    "Shut up {user2}, you are just {user2}.",  # No game no life reference
    "{user1} hits {user2} with Aka si anse!",  # No game no life reference
    "@NeoTheKitty scratches {user2}",  # Pixels pet cat - @NeoTheKitty
    "Majin buu ate {user2}",  # Dbz
    "Goblin slayer slays {user2}",  # Goblin Slayer
)

PAT_TEMPLATES = (
    "{user1} pats {user2} on the head.",
    "*gently rubs {user2}'s head*.",
    "*{user1} mofumofus {user2}'s head*",
    "*{user1} messes up {user2}'s head*",
    "*{user1} intensly rubs {user2}'s head*",
    "*{user2}'s waifu pats their head*",
    "*{user2}'s got free headpats*",
    "No pats for {user2}!",
    "Oh no! We are all out of pats.",
    "This is a designated no pat zone!",
    "No pats for {user2}!",
    "{user1} spoils {user2} with headpats!",
    "{user2} received one free headpat!",
    "{user1} headpats {user2} whilst giving a lap pillow",
    "{user1} aggressively pats {user2}",
    "{user1} gently strokes {user2}'s head",
    "Pat, pat, pat, pat",
    "{user2} could not escape {user1}'s headpats",
    "{user2}.exe has stopped working",
    "{user1} rubs {user2} on the neck",
    "Must... extort... HEADPATS",
    "{user1} headpats {user2}'s head with a pat",
    "{user1} pats {user2} unexpectedly",
    "{user1} pats {user2} with consent, maybe?",
    "Pat pat, {user2} honto kawaii ne!",
    "{user1} headpats {user2} at 420apm",
    "{user1} bellyrubs {user2}",
    "{user1} pats {user2} friendlily",
    "{user2} uses HEADPATS? O KAWAII KOTO",
    "*headpats.gif intensifies for {user2}*",
    "(*´ω´(*｀ω｀)",
    "(ｏ・_・)ノ”(ᴗ_ ᴗ。)",
    "(*￣▽￣)ノ”(- -*)",
    "(っ´ω`)ﾉ(╥ω╥)",
    "( ´Д｀)ﾉ(´･ω･`) ﾅﾃﾞﾅﾃﾞ",
)

PAT_GIFS = (
    "CgACAgQAAxkBAALRX19Xs7tBdOH1gQwS_rglVRkTbgVYAAKEAgACmQn9UWlyGa_xy9_aGwQ",
    "CgACAgEAAxkBAALRYF9Xs8EnhsDfDpld3ILoqTbzDmwxAAJFAAOJxjlHECanwn69E5QbBA",
)

PAT_STICKERS = (
    "CAACAgQAAxkBAALRWV9Xs4HH0XaXfhZe-jWaZoXfs-IsAAJYAwACdDgSEHYOt4KvL02oGwQ",
    "CAACAgQAAxkBAALRXF9Xs6XmIeDbnoL1wiDky0TdX-CvAAKKAQAC1TMzC9A3CtiT2rqVGwQ",
)

PING_STRING = (
    "PONG!!",
    "I am here!",
)

ITEMS = (
    "cast iron skillet",
    "angry meow",
    "cricket bat",
    "wooden cane",
    "shovel",
    "toaster",
    "book",
    "laptop",
    "rubber chicken",
    "spiked bat",
    "heavy rock",
    "chunk of dirt",
    "ton of bricks",
    "rasengan",
    "spirit bomb",
    "100-Type Guanyin Bodhisattva",
    "rasenshuriken",
    "Murasame",
    "ban",
    "chunchunmaru",
    "Kubikiribōchō",
    "rasengan",
    "spherical flying kat",
)

THROW = (
    "throws",
    "flings",
    "chucks",
    "hurls",
)

HIT = (
    "hits",
    "whacks",
    "slaps",
    "smacks",
    "bashes",
    "pats",
)

EYES = [
    ["⌐■", "■"],
    [" ͠°", " °"],
    ["⇀", "↼"],
    ["´• ", " •`"],
    ["´", "`"],
    ["`", "´"],
    ["ó", "ò"],
    ["ò", "ó"],
    ["⸌", "⸍"],
    [">", "<"],
    ["Ƹ̵̡", "Ʒ"],
    ["ᗒ", "ᗕ"],
    ["⟃", "⟄"],
    ["⪧", "⪦"],
    ["⪦", "⪧"],
    ["⪩", "⪨"],
    ["⪨", "⪩"],
    ["⪰", "⪯"],
    ["⫑", "⫒"],
    ["⨴", "⨵"],
    ["⩿", "⪀"],
    ["⩾", "⩽"],
    ["⩺", "⩹"],
    ["⩹", "⩺"],
    ["◥▶", "◀◤"],
    ["◍", "◎"],
    ["/͠-", "┐͡-\\"],
    ["⌣", "⌣”"],
    [" ͡⎚", " ͡⎚"],
    ["≋"],
    ["૦ઁ"],
    ["  ͯ"],
    ["  ͌"],
    ["ළ"],
    ["◉"],
    ["☉"],
    ["・"],
    ["▰"],
    ["ᵔ"],
    [" ﾟ"],
    ["□"],
    ["☼"],
    ["*"],
    ["`"],
    ["⚆"],
    ["⊜"],
    [">"],
    ["❍"],
    ["￣"],
    ["─"],
    ["✿"],
    ["•"],
    ["T"],
    ["^"],
    ["ⱺ"],
    ["@"],
    ["ȍ"],
    ["  "],
    ["  "],
    ["x"],
    ["-"],
    ["$"],
    ["Ȍ"],
    ["ʘ"],
    ["Ꝋ"],
    [""],
    ["⸟"],
    ["๏"],
    ["ⴲ"],
    ["◕"],
    ["◔"],
    ["✧"],
    ["■"],
    ["♥"],
    [" ͡°"],
    ["¬"],
    [" º "],
    ["⨶"],
    ["⨱"],
    ["⏓"],
    ["⏒"],
    ["⍜"],
    ["⍤"],
    ["ᚖ"],
    ["ᴗ"],
    ["ಠ"],
    ["σ"],
    ["☯"],
]

MOUTHS = [
    ["v"],
    ["ᴥ"],
    ["ᗝ"],
    ["Ѡ"],
    ["ᗜ"],
    ["Ꮂ"],
    ["ᨓ"],
    ["ᨎ"],
    ["ヮ"],
    ["╭͜ʖ╮"],
    [" ͟ل͜"],
    [" ͜ʖ"],
    [" ͟ʖ"],
    [" ʖ̯"],
    ["ω"],
    [" ³"],
    [" ε "],
    ["﹏"],
    ["□"],
    ["ل͜"],
    ["‿"],
    ["╭╮"],
    ["‿‿"],
    ["▾"],
    ["‸"],
    ["Д"],
    ["∀"],
    ["!"],
    ["人"],
    ["."],
    ["ロ"],
    ["_"],
    ["෴"],
    ["ѽ"],
    ["ഌ"],
    ["⏠"],
    ["⏏"],
    ["⍊"],
    ["⍘"],
    ["ツ"],
    ["益"],
    ["╭∩╮"],
    ["Ĺ̯"],
    ["◡"],
    [" ͜つ"],
]

EARS = [
    ["q", "p"],
    ["ʢ", "ʡ"],
    ["⸮", "?"],
    ["ʕ", "ʔ"],
    ["ᖗ", "ᖘ"],
    ["ᕦ", "ᕥ"],
    ["ᕦ(", ")ᕥ"],
    ["ᕙ(", ")ᕗ"],
    ["ᘳ", "ᘰ"],
    ["ᕮ", "ᕭ"],
    ["ᕳ", "ᕲ"],
    ["(", ")"],
    ["[", "]"],
    ["¯\\_", "_/¯"],
    ["୧", "୨"],
    ["୨", "୧"],
    ["⤜(", ")⤏"],
    ["☞", "☞"],
    ["ᑫ", "ᑷ"],
    ["ᑴ", "ᑷ"],
    ["ヽ(", ")ﾉ"],
    ["\\(", ")/"],
    ["乁(", ")ㄏ"],
    ["└[", "]┘"],
    ["(づ", ")づ"],
    ["(ง", ")ง"],
    ["⎝", "⎠"],
    ["ლ(", "ლ)"],
    ["ᕕ(", ")ᕗ"],
    ["(∩", ")⊃━☆ﾟ.*"],
]

TOSS = ("Heads", "Tails")

EIGHTBALL = [
    "🟢 As I see it, yes.",
    "🟡 Ask again later.",
    "🟡 Better not tell you now.",
    "🟡 Cannot predict now.",
    "🟡 Concentrate and ask again.",
    "🟡 Don’t count on it.",
    "🟢 It is certain.",
    "🟢 It is decidedly so.",
    "🟢 Most likely.",
    "🔴 My reply is no.",
    "🔴 My sources say no.",
    "🔴 Outlook not so good.",
    "🟢 Outlook good.",
    "🟡 Reply hazy, try again.",
    "🟢 Signs point to yes.",
    "🔴 Very doubtful.",
    "🟢 Without a doubt.",
    "🟢 Yes.",
    "🟢 Yes – definitely.",
    "🟢 You may rely on it.",
]

DECIDE = ("Yes.", "No.", "Maybe.")

TABLE = (
    "(╯°□°）╯彡 ┻━┻",
    "I ran out of tables, will order more.",
    "Go do some work instead of flippin tables.",
)

GBUN = (
    "Beware! This Bot-Admeme Can Gbun You Right Off The Map.",
    "I Guess You've Forgot Spelling Of GBAN Maybe...?",
    "Don't Misuse Your Powers...",
    "Nah, He Looks Innocent...",
)


GBAM = "<b>Beginning Of Global Bam For {user2}</b>  \n \nChat Id : <code>{chatid}</code> \nReason : <i>{reason}</i> \nGBammed By {user1}"


GBAM_REASON = (
    "sasta noob",
    "sasta waifu stealer",
    "sasta white-het hekur",
    "sasta white-het codur",
    "sasta white-het vala chintu",
    "sasta hexa hekur",
    "sasta hexa playur",
    "sasta tiktokur💃🏾",
    "sasta membor of team 7",
    "sasta selmon boi",
    "sasta fri-fire player",
    "sasta chhota bhim",
    "sasta chhapri",
    "sasta jony sin",
    "sasta chhapri nibba",
    "sasta nibba",
    "sasti ria chokroborti",
    "sasti nibbi",
    "sasta camper",
    "sasta pubji mobeil player",
    "Aine me khudko dekh ke hilane wala",
    "Bts ka choda",
    "Kabhi Kabhi lagta he apun hi bhagwan he",
    "Aise hi sexy lag raha tha",
    "Eminem ka choda",
)

GDNIGHT = [
    "`Good night keep your dreams alive`",
    "`Night, night, to a dear friend! May you sleep well!`",
    "`May the night fill with stars for you. May counting every one, give you contentment!`",
    "`Wishing you comfort, happiness, and a good night’s sleep!`",
    "`Now relax. The day is over. You did your best. And tomorrow you’ll do better. Good Night!`",
    "`Good night to a friend who is the best! Get your forty winks!`",
    "`May your pillow be soft, and your rest be long! Good night, friend!`",
    "`Let there be no troubles, dear friend! Have a Good Night!`",
    "`Rest soundly tonight, friend!`",
    "`Have the best night’s sleep, friend! Sleep well!`",
    "`Have a very, good night, friend! You are wonderful!`",
    "`Relaxation is in order for you! Good night, friend!`",
    "`Good night. May you have sweet dreams tonight.`",
    "`Sleep well, dear friend and have sweet dreams.`",
    "`As we wait for a brand new day, good night and have beautiful dreams.`",
    "`Dear friend, I wish you a night of peace and bliss. Good night.`",
    "`Darkness cannot last forever. Keep the hope alive. Good night.`",
    "`By hook or crook you shall have sweet dreams tonight. Have a good night, buddy!`",
    "`Good night, my friend. I pray that the good Lord watches over you as you sleep. Sweet dreams.`",
    "`Good night, friend! May you be filled with tranquility!`",
    "`Wishing you a calm night, friend! I hope it is good!`",
    "`Wishing you a night where you can recharge for tomorrow!`",
    "`Slumber tonight, good friend, and feel well rested, tomorrow!`",
    "`Wishing my good friend relief from a hard day’s work! Good Night!`",
    "`Good night, friend! May you have silence for sleep!`",
    "`Sleep tonight, friend and be well! Know that you have done your very best today, and that you will do your very best, tomorrow!`",
    "`Friend, you do not hesitate to get things done! Take tonight to relax and do more, tomorrow!`",
    "`Friend, I want to remind you that your strong mind has brought you peace, before. May it do that again, tonight! May you hold acknowledgment of this with you!`",
    "`Wishing you a calm, night, friend! Hoping everything winds down to your liking and that the following day meets your standards!`",
    "`May the darkness of the night cloak you in a sleep that is sound and good! Dear friend, may this feeling carry you through the next day!`",
    "`Friend, may the quietude you experience tonight move you to have many more nights like it! May you find your peace and hold on to it!`",
    "`May there be no activity for you tonight, friend! May the rest that you have coming to you arrive swiftly! May the activity that you do tomorrow match your pace and be all of your own making!`",
    "`When the day is done, friend, may you know that you have done well! When you sleep tonight, friend, may you view all the you hope for, tomorrow!`",
    "`When everything is brought to a standstill, friend, I hope that your thoughts are good, as you drift to sleep! May those thoughts remain with you, during all of your days!`",
    "`Every day, you encourage me to do new things, friend! May tonight’s rest bring a new day that overflows with courage and exciting events!`",
]

GDMORNING = (
    "`Life is full of uncertainties. But there will always be a sunrise after every sunset. Good morning!`",
    "`It doesn’t matter how bad was your yesterday. Today, you are going to make it a good one. Wishing you a good morning!`",
    "`If you want to gain health and beauty, you should wake up early. Good morning!`",
    "`May this morning offer you new hope for life! May you be happy and enjoy every moment of it. Good morning!`",
    "`May the sun shower you with blessings and prosperity in the days ahead. Good morning!`",
    "`Every sunrise marks the rise of life over death, hope over despair and happiness over suffering. Wishing you a very enjoyable morning today!`",
    "`Wake up and make yourself a part of this beautiful morning. A beautiful world is waiting outside your door. Have an enjoyable time!`",
    "`Welcome this beautiful morning with a smile on your face. I hope you’ll have a great day today. Wishing you a very good morning!`",
    "`You have been blessed with yet another day. What a wonderful way of welcoming the blessing with such a beautiful morning! Good morning to you!`",
    "`Waking up in such a beautiful morning is a guaranty for a day that’s beyond amazing. I hope you’ll make the best of it. Good morning!`",
    "`Nothing is more refreshing than a beautiful morning that calms your mind and gives you reasons to smile. Good morning! Wishing you a great day.`",
    "`Another day has just started. Welcome the blessings of this beautiful morning. Rise and shine like you always do. Wishing you a wonderful morning!`",
    "`Wake up like the sun every morning and light up the world your awesomeness. You have so many great things to achieve today. Good morning!`",
    "`A new day has come with so many new opportunities for you. Grab them all and make the best out of your day. Here’s me wishing you a good morning!`",
    "`The darkness of night has ended. A new sun is up there to guide you towards a life so bright and blissful. Good morning dear!`",
    "`Wake up, have your cup of morning tea and let the morning wind freshen you up like a happiness pill. Wishing you a good morning and a good day ahead!`",
    "`Sunrises are the best; enjoy a cup of coffee or tea with yourself because this day is yours, good morning! Have a wonderful day ahead.`",
    "`A bad day will always have a good morning, hope all your worries are gone and everything you wish could find a place. Good morning!`",
    "`A great end may not be decided but a good creative beginning can be planned and achieved. Good morning, have a productive day!`",
    "`Having a sweet morning, a cup of coffee, a day with your loved ones is what sets your “Good Morning” have a nice day!`",
    "`Anything can go wrong in the day but the morning has to be beautiful, so I am making sure your morning starts beautiful. Good morning!`",
    "`Open your eyes with a smile, pray and thank god that you are waking up to a new beginning. Good morning!`",
    "`Morning is not only sunrise but A Beautiful Miracle of God that defeats the darkness and spread light. Good Morning.`",
    "`Life never gives you a second chance. So, enjoy every bit of it. Why not start with this beautiful morning. Good Morning!`",
    "`If you want to gain health and beauty, you should wake up early. Good Morning!`",
    "`Birds are singing sweet melodies and a gentle breeze is blowing through the trees, what a perfect morning to wake you up. Good morning!`",
    "`This morning is so relaxing and beautiful that I really don’t want you to miss it in any way. So, wake up dear friend. A hearty good morning to you!`",
    "`Mornings come with a blank canvas. Paint it as you like and call it a day. Wake up now and start creating your perfect day. Good morning!`",
    "`Every morning brings you new hopes and new opportunities. Don’t miss any one of them while you’re sleeping. Good morning!`",
    "`Start your day with solid determination and great attitude. You’re going to have a good day today. Good morning my friend!`",
    "`Friendship is what makes life worth living. I want to thank you for being such a special friend of mine. Good morning to you!`",
    "`A friend like you is pretty hard to come by in life. I must consider myself lucky enough to have you. Good morning. Wish you an amazing day ahead!`",
    "`The more you count yourself as blessed, the more blessed you will be. Thank God for this beautiful morning and let friendship and love prevail this morning.`",
    "`Wake up and sip a cup of loving friendship. Eat your heart out from a plate of hope. To top it up, a fork full of kindness and love. Enough for a happy good morning!`",
    "`It is easy to imagine the world coming to an end. But it is difficult to imagine spending a day without my friends. Good morning.`",
    )

CUDDLE_GIF = [
    "CgACAgQAAxkBAAIPy2C0fJmMJlku6c-ugz7UVD-dlAdIAAIyAgACJDqUUrjsIE0L5PsMHwQ",
    "CgACAgQAAxkBAAIPzGC0fJkuEsnH8OOFPDfJxjZbIwVvAAJoAgAC0pmEUuBZhUc-uBwyHwQ",
    "CgACAgQAAxkBAAIPzWC0fJnN5qbgad4MYlFV8j5_LWEUAAKwAgAC2SydUioqFAlXLp3GHwQ",
    "CgACAgQAAxkBAAIPzmC0fJmIxriRiBRu5ngSiLwqNnuHAAJqAgACsxaVUjxrduB7RCMLHwQ",
    "CgACAgQAAxkBAAIPz2C0fJkZnPH6TiBRCaXvdPXsGvISAAJ-AgACyIqdUknP0GtdaLthHwQ",
    "CgACAgQAAxkBAAIP0GC0fJlVW7XfbgZW6OYg9olSqLiuAAJVAgACqb-cUqoC4zxOZjWgHwQ",
    "CgACAgQAAxkBAAIP3WC0fVlBMfmBRpjoKGPAYEPtlJENAAJvAgACrDeMUuBzMNVEYkHBHwQ",
    "CgACAgQAAxkBAAIP3mC0fVly-olZyqiuM-MVaWt05RlbAAIxAgACzhuVUnpk9DYufWoQHwQ",
    "CgACAgQAAxkBAAIP32C0fVnwrZMkJ4pXZkq8ZrrB--5wAAIwAgACP8MkUzn3moIsBgeQHwQ",
    "CgACAgQAAxkBAAIP4GC0fVnWTF-uwJGWD4aBqVQQMrriAAIlAgACwAv1UrsAAc1-no_c-B8E",
    "CgACAgQAAxkBAAPBYMwZQMIksQKfpNeFh90T83kAAcD4AALjAgAC30MtURDzuVy0pD8CHwQ"
]

CUDDLE_TEMPLATES = (
    "{user1} cuddles {user2} tightly.",
    "{user2} got free cuddles from {user1}.",
    "{user1} cuddles {user2} with love whole night.",
    "It's cuddle time for {user1} and {user2}.",
    "{user1} cuddled {user2}. Such a romantic moment",
    "No Cuddles For {user2}!",
)

FLIRT_TEXT = (
    "I hope you know CPR, because you just took my breath away!",
    "So, aside from taking my breath away, what do you do for a living?",
    "I ought to complain to Spotify for you not being named this week’s hottest single.",
    "Your eyes are like the ocean; I could swim in them all day.",
    "When I look in your eyes, I see a very kind soul",
    "If you were a vegetable, you’d be a ‘cute-cumber.’",
    "Do you happen to have a Band-Aid? ‘Cause I scraped my knees falling for you.",
    "I didn’t know what I wanted in a woman until I saw you.",
    "I was wondering if you could tell me: If you’re here, who’s running Heaven?",
    "No wonder the sky is gray tonight , cause all the color is in your eyes.",
    "You’ve got everything I’ve been searching for, and believe me—I’ve been looking a long time.",
    "Do you have a map? I just got lost in your eyes."
)

ROMANCE_GIFS = [
    "CgACAgQAAxkBAAIQIWC0g6ovGy7YT-Y66XfpFVEKwTXKAAJ8AgACTu6sUN0m69FQv9tHHwQ",
    "CgACAgQAAxkBAAIQImC0g62lTsbdQtBB5fY4tX5s9vP8AAJyAgACHdY1UTlYUpF2JAABcx8E",
    "CgACAgQAAxkBAAIQI2C0g7nn-TRjwilr59dtctGb_cLlAAJ6AgACNkelUhxvFpZgDUbFHwQ",
    "CgACAgQAAxkBAAIQJGC0g8L4cYfXRxE42YOTOcTCn8d9AAIoAgACqhGMUnPCWXH2RqPwHwQ",
    "CgACAgQAAxkBAAIQJWC0g9GEFeRewmfL7Ei4ZaCdQ9p4AAIEAgAC_3xlUB5O5hIl3CbxHwQ",
    "CgACAgQAAxkBAAIQJmC0g92L9jTq89JBieJCumwYCFPwAAIiAgAC1z2UUlOhsI6CxkHXHwQ"
] 

ROMANCE_STICKERS = [
    "CAACAgQAAxkBAAIQM2C0hTjoZ6imrf90bzPD6RmGkl2ZAAJaLgAClGBOA7Ky9sn-fqeXHwQ",
    "CAACAgQAAxkBAAIQNGC0hT2OqiTvCvXzONyRU8PfXejQAAJ1LgAClGBOA5yx5Lp5F-ILHwQ",
    "CAACAgQAAxkBAAIQNWC0hT9jlDuleEyc_FOs9IBVmISYAAJ2LgAClGBOA5rDqeCOsXHNHwQ",
    "CAACAgQAAxkBAAIQNmC0hUprZQ43ncln60H8tN2Df5Z2AAKILgAClGBOA28NiCHVy1AKHwQ",
    "CAACAgQAAxkBAAIQN2C0hUu7-A7rehNrLRHCAxZVMTTnAAKHLgAClGBOA3wWNsqsCiN6HwQ"
]

ROMANCE_TEMPLATES = (
    "I knew I’d never be able to remember what {user2} wore that day. But I also knew I’d never forget the way she looked.",
    "So it’s not gonna be easy. It’s gonna be really hard. We’re gonna have to work at this every day, but I want to do that because I want you. I want all of you, forever, you and me, every day.",
    "I wish I knew how to quit you.",
    "Make me a radio and turn me up when you feel low.",
    "I can't see anything that I don't like about you."
)

UWU_GIFS = [
    "CgACAgQAAxkBAAIQQmC0hzeH3jUWqOpCnK383r-TPBwSAAJmAgACuciMUgfkgemP5m1zHwQ",
    "CgACAgQAAxkBAAIQQ2C0h1RVQT1rES7mP86Ci2OWCx2YAAIiAgAC-eyUUhbqa8UgTgiKHwQ",
    "CgACAgQAAxkBAAIQRGC0h3r70AsY6BHeCFx_YIdXPxe1AAJzAgAChzINUP7DYeBMExAbHwQ",
    "CgACAgQAAxkBAAIQRWC0h4YyiN0QtB04fwQ9BrO5Dn8-AAJeAgACA0ZNUKg2nl7j2KgkHwQ",
    "CgACAgQAAxkBAAIQRmC0h5Gu-nYhXpHBjX95wqhLdZ5VAAJZAgACo9KkUsO_TfexFnb0HwQ",
    "CgACAgQAAxkBAAIQR2C0h5qEUDTz1IATJb3LaneMTvLJAAKUAgAC6V9FUGhbr491dDNRHwQ",
    "CgACAgQAAxkBAAIQSGC0h6wLXwpfeZ_G2xdWiDLxfY1pAAJaAgACxh3NUJs2Ww3_ZJ_eHwQ",
    "CgACAgQAAxkBAAIQSWC0h7aMqKriQQoFTwaqW3Apz2ZNAAIHAgACv7cNU8ooGtrchd2iHwQ"
]

UWU_STICKERS = [
    "CAACAgUAAxkBAAIQdWC0moF88wE72wmUeaOLMc342mF4AAIUAwACk6CgVWhMjd9B5B1FHwQ",
    "CAACAgUAAxkBAAIQeGC0mplxufMmOxW3UjkV92OjQFYxAAJMAwAC5ryoVZ68beJeQJcYHwQ",
    "CAACAgUAAx0CS3FrwgABA7lJYN6trj9IFjVBUefGCf3XtAHB8GUAAs8DAAKT3NFVjFwwcs1XzRYgBA"
]

OWO_GIFS = [
    "CgACAgQAAxkBAAIQWmC0iFdF7kgg7LY9mzNBekbqjhQcAAJmAgAC0BX9UsEPzw08-As7HwQ",
    "CgACAgQAAxkBAAIQW2C0iHD-zQIMP-KaeuANN10dE6wkAAJDAgACTnelUjD2cJlQc7acHwQ",
    "CgACAgQAAxkBAAIQXGC0iJiRiYcoGZV1iJ4ntAqwdTZPAAKxAgACxlEsUXBu3m2frBPlHwQ",
    "CgACAgQAAxkBAAIQXWC0iMihZxq8Za0Wys0syRLQ68s_AAItAgACktbMUm7m-H24_ILTHwQ",
    "CgACAgQAAxkBAAIQXmC0iRlW8csHLsoxPbUaMWW-5IudAAJsAgACbHesUJ68-FYsjr_xHwQ"
]

OWO_STICKERS = [
    "CAACAgEAAx0CRf9PfgACElxgtJhw1QnFz6IIPzzOf4QJYI06OwAC5TIAA-cvCK5J8Qz_LoGKHwQ",
    "CAACAgUAAxkBAAIQbGC0mik81vkrndPPJ7Vif9yuCdkjAAIOAgACiMGhVWgNT2REBs36HwQ"
]
