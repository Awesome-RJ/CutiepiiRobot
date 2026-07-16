import html
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd

QUOTES = [
    ('𝖡𝖾𝗅𝗂𝖾𝗏𝖾 𝗂𝗇 𝗒𝗈𝗎𝗋𝗌𝖾𝗅𝖿. 𝖭𝗈𝗍 𝗂𝗇 𝗍𝗁𝖾 𝗒𝗈𝗎 𝗐𝗁𝗈 𝖻𝖾𝗅𝗂𝖾𝗏𝖾𝗌 𝗂𝗇 𝗆𝖾. 𝖭𝗈𝗍 𝗍𝗁𝖾 𝗆𝖾 𝗐𝗁𝗈 𝖻𝖾𝗅𝗂𝖾𝗏𝖾𝗌 𝗂𝗇 𝗒𝗈𝗎. 𝖡𝖾𝗅𝗂𝖾𝗏𝖾 𝗂𝗇 𝗍𝗁𝖾 𝗒𝗈𝗎 𝗐𝗁𝗈 𝖻𝖾𝗅𝗂𝖾𝗏𝖾𝗌 𝗂𝗇 𝗒𝗈𝗎𝗋𝗌𝖾𝗅𝖿.', '𝖪𝖺𝗆𝗂𝗇𝖺', '𝖳𝖾𝗇𝗀𝖾𝗇 𝖳𝗈𝗉𝗉𝖺 𝖦𝗎𝗋𝗋𝖾𝗇 𝖫𝖺𝗀𝖺𝗇𝗇'),
    ("𝖨𝗍'𝗌 𝗇𝗈𝗍 𝗍𝗁𝖾 𝖿𝖺𝖼𝖾 𝗍𝗁𝖺𝗍 𝗆𝖺𝗄𝖾𝗌 𝗌𝗈𝗆𝖾𝗈𝗇𝖾 𝖺 𝗆𝗈𝗇𝗌𝗍𝖾𝗋, 𝗂𝗍'𝗌 𝗍𝗁𝖾 𝖼𝗁𝗈𝗂𝖼𝖾𝗌 𝗍𝗁𝖾𝗒 𝗆𝖺𝗄𝖾 𝗐𝗂𝗍𝗁 𝗍𝗁𝖾𝗂𝗋 𝗅𝗂𝗏𝖾𝗌.", '𝖭𝖺𝗋𝗎𝗍𝗈 𝖴𝗓𝗎𝗆𝖺𝗄𝗂', '𝖭𝖺𝗋𝗎𝗍𝗈'),
    ('𝖳𝗁𝖾 𝗈𝗇𝗅𝗒 𝗍𝗁𝗂𝗇𝗀 𝗍𝗁𝖺𝗍 𝖼𝖺𝗇 𝖽𝖾𝖿𝖾𝖺𝗍 𝗉𝗈𝗐𝖾𝗋 𝗂𝗌 𝗆𝗈𝗋𝖾 𝗉𝗈𝗐𝖾𝗋. 𝖳𝗁𝖺𝗍 𝗂𝗌 𝗍𝗁𝖾 𝗈𝗇𝖾 𝖼𝗈𝗇𝗌𝗍𝖺𝗇𝗍 𝗂𝗇 𝗍𝗁𝗂𝗌 𝗎𝗇𝗂𝗏𝖾𝗋𝗌𝖾. 𝖧𝗈𝗐𝖾𝗏𝖾𝗋, 𝗍𝗁𝖾𝗋𝖾 𝗂𝗌 𝗇𝗈 𝗉𝗈𝗂𝗇𝗍 𝗂𝗇 𝗉𝗈𝗐𝖾𝗋 𝗂𝖿 𝗂𝗍 𝖼𝗈𝗇𝗌𝗎𝗆𝖾𝗌 𝗂𝗍𝗌𝖾xl𝖿.', '𝖨𝗍𝖺𝖼𝗁𝗂 𝖴𝖼𝗁𝗂𝗁𝖺', '𝖭𝖺𝗋𝗎𝗍𝗈'),
    ("𝖭𝗈 𝗈𝗇𝖾 𝗄𝗇𝗈𝗐𝗌 𝗐𝗁𝖺𝗍 𝗍𝗁𝖾 𝖿𝗎𝗍𝗎𝗋𝖾 𝗁𝗈𝗅𝖽𝗌. 𝖳𝗁𝖺𝗍'𝗌 𝗐𝗁𝗒 𝗂𝗍𝗌 𝗉𝗈𝗍𝖾𝗇𝗍𝗂𝖺𝗅 𝗂𝗌 𝗂𝗇𝖿𝗂𝗇𝗂𝗍𝖾.", '𝖱𝗂𝗇𝗍𝖺𝗋𝗈𝗎 𝖮𝗄𝖺𝖻𝖾', '𝖲𝗍𝖾𝗂𝗇𝗌;𝖦𝖺𝗍𝖾'),
    ("𝖣𝗈𝗇'𝗍 𝖿𝗈𝗋𝗀𝖾𝗍. 𝖠𝗅𝗐𝖺𝗒𝗌, 𝗌𝗈𝗆𝖾𝗐𝗁𝖾𝗋𝖾, 𝗌𝗈𝗆𝖾𝗈𝗇𝖾 𝗂𝗌 𝖿𝗂𝗀𝗁𝗍𝗂𝗇𝗀 𝖿𝗈𝗋 𝗒𝗈𝗎. 𝖠𝗌 𝗅𝗈𝗇𝗀 𝖺𝗌 𝗒𝗈𝗎 𝗋𝖾𝗆𝖾𝗆𝖻𝖾𝗋 𝗁𝖾𝗋, 𝗒𝗈𝗎 𝖺𝗋𝖾 𝗇𝗈𝗍 𝖺𝗅𝗈𝗇𝖾.", '𝖬𝖺𝖽𝗈𝗄𝖺 𝖪𝖺𝗇𝖺𝗆𝖾', '𝖯𝗎𝖾𝗅𝗅𝖺 𝖬𝖺𝗀𝗂 𝖬𝖺𝖽𝗈𝗄𝖺 𝖬𝖺𝗀𝗂𝖼𝖺'),
    ("𝖳𝗁𝖾 𝗈𝗇𝗅𝗒 𝗍𝗁𝗂𝗇𝗀 𝗐𝖾'𝗋𝖾 𝖺𝗅𝗅𝗈𝗐𝖾𝖽 𝗍𝗈 𝖽𝗈 𝗂𝗌 𝗍𝗈 𝖻𝖾𝗅𝗂𝖾𝗏𝖾 𝗍𝗁𝖺𝗍 𝗐𝖾 𝗐𝗈𝗇'𝗍 𝗋𝖾𝗀𝗋𝖾𝗍 𝗍𝗁𝖾 𝖼𝗁𝗈𝗂𝖼𝖾 𝗐𝖾 𝗆𝖺𝖽𝖾.", '𝖫𝖾𝗏𝗂 𝖠𝖼𝗄𝖾𝗋𝗆𝖺𝗇', '𝖠𝗍𝗍𝖺𝖼𝗄 𝗈𝗇 𝖳𝗂𝗍𝖺𝗇'),
    ('𝖶𝗁𝖺𝗍𝖾𝗏𝖾𝗋 𝗒𝗈𝗎 𝖽𝗈, 𝖾𝗇𝗃𝗈𝗒 𝗂𝗍 𝗍𝗈 𝗍𝗁𝖾 𝖿𝗎𝗅𝗅𝖾𝗌𝗍. 𝖳𝗁𝖺𝗍 𝗂𝗌 𝗍𝗁𝖾 𝗌𝖾𝖼𝗋𝖾𝗍 𝗈𝖿 𝗅𝗂𝖿𝖾.', '𝖱𝗂𝖽𝖾𝗋 (𝖨𝗌𝗄𝖺𝗇𝖽𝖺𝗋)', '𝖥𝖺𝗍𝖾/𝖹𝖾𝗋𝗈'),
    ("𝖨𝖿 𝗒𝗈𝗎 𝖽𝗈𝗇't 𝗍𝖺𝗄𝖾 𝗋𝗂𝗌𝗄𝗌, 𝗒𝗈𝗎 𝖼𝖺𝗇'𝗍 𝖼𝗋𝖾𝖺𝗍𝖾 𝖺 𝖿𝗎𝗍𝗎𝗋𝖾.", '𝖬𝗈𝗇𝗄𝖾𝗒 𝖣. 𝖫𝗎𝖿𝖿𝗒', '𝖮𝗇𝖾 𝖯𝗂𝖾𝖼𝖾'),
    ('𝖨𝗇 𝗈𝗋𝖽𝖾𝗋 𝗍𝗈 𝗀𝗋𝗈𝗐, 𝗒𝗈𝗎 𝗆𝗎𝗌𝗍 𝖿𝖺𝖼𝖾 𝗍𝗁𝖾 𝗉𝖺𝗂𝗇 𝗈𝖿 𝗍𝗁𝖾 𝗉𝖺𝗌𝗍. 𝖠𝖼𝖼𝖾𝗉𝗍 𝗂𝗍 𝖺𝗇𝖽 𝗆𝗈𝗏𝖾 𝖿𝗈𝗋𝗐𝖺𝗋𝖽.', '𝖤𝗋𝗓𝖺 𝖲𝖼𝖺𝗋𝗅𝖾𝗍', '𝖥𝖺𝗂𝗋𝗒 𝖳𝖺𝗂𝗅'),
    ('𝖲𝗈𝗆𝖾𝗍𝗂𝗆𝖾𝗌 𝗍𝗁𝖾 𝗍𝗁𝗂𝗇𝗀𝗌 𝗍𝗁𝖺𝗍 𝗆𝖺𝗍𝗍𝖾𝗋 𝗍𝗁𝖾 𝗆𝗈𝗌𝗍 𝖺𝗋𝖾 𝗋𝗂𝗀𝗁𝗍 𝗂𝗇 𝖿𝗋𝗈𝗇𝗍 𝗈𝖿 𝗒𝗈𝗎.', '𝖠𝗌𝗎𝗇𝖺 𝖸𝗎𝗎𝗄𝗂', '𝖲𝗐𝗈𝗋𝖽 𝖠𝗋𝗍 𝖮𝗇𝗅𝗂𝗇𝖾'),
    ('𝖳𝗁𝖾 𝗐𝗈𝗋𝗅𝖽’𝗌 𝗇𝗈𝗍 𝗉𝖾𝗋𝖿𝖾𝖼𝗍, 𝖻𝗎𝗍 𝗂𝗍’𝗌 𝗍𝗁𝖾𝗋𝖾 𝖿𝗈𝗋 𝗎𝗌 𝗍𝗋𝗒𝗂𝗇𝗀 𝗍𝗁𝖾 𝖻𝖾𝗌𝗍 𝗂𝗍 𝖼𝖺𝗇. 𝖳𝗁𝖺𝗍’𝗌 𝗐𝗁𝖺𝗍 𝗆𝖺𝗄𝖾𝗌 𝗂𝗍 𝗌𝗈 𝖽𝖺𝗆𝗇 𝖻𝖾𝖺𝗎𝗍𝗂𝖿𝗎𝗅.', '𝖱𝗈𝗒 𝖬𝗎𝗌𝗍𝖺𝗇𝗀', '𝖥𝗎𝗅𝗅𝗆𝖾𝗍𝖺𝗅 𝖠𝗅𝖼𝗁𝖾𝗆𝗂𝗌𝗍: 𝖡𝗋𝗈𝗍𝗁𝖾𝗋𝗁𝗈𝗈𝖽'),
    ('𝖨𝖿 𝗇𝗈𝖻𝗈𝖽𝗒 𝖼𝖺𝗋𝖾𝗌 𝗍𝗈 𝖺𝖼𝖼𝖾𝗉𝗍 𝗒𝗈𝗎 𝖺𝗇𝖽 𝗐𝖺𝗇𝗍𝗌 𝗒𝗈𝗎 𝗂𝗇 𝗍𝗁𝗂𝗌 𝗐𝗈𝗋𝗅𝖽, 𝖺𝖼𝖼𝖾𝗉𝗍 𝗒𝗈𝗎𝗋𝗌𝖾𝗅𝖿 𝖺𝗇𝖽 𝗒𝗈𝗎 𝗐𝗂嫌𝗅 𝗌𝖾𝖾 𝗍𝗁𝖺𝗍 𝗒𝗈𝗎 𝖽𝗈𝗇’𝗍 𝗇𝖾𝖾𝖽 𝗍𝗁𝖾𝗆 𝖺𝗇𝖽 𝗍𝗁𝖾𝗂𝗋 𝗌𝖾𝗅𝖿𝗂𝗌𝗁 𝗂𝖽𝖾𝖺𝗌.', '𝖦𝗂𝗇𝗍𝗈𝗄𝗂 𝖲𝖺𝗄𝖺𝗍𝖺', '𝖦𝗂𝗇𝗍𝖺𝗆𝖺'),
    ('𝖶𝗁𝖺𝗍𝖾𝗏𝖾𝗋 𝗒𝗈𝗎 𝖽𝗈, 𝗒𝗈𝗎 𝗌𝗁𝗈𝗎𝗅𝖽 𝖽𝗈 𝗂𝗍 𝗐𝗂𝗍𝗁 𝖺𝗅𝗅 𝗒𝗈𝗎𝗋 𝗁𝖾𝖺𝗋𝗍.', '𝖲𝖺𝖻𝖾𝗋 (𝖠𝗋𝗍𝗈𝗋𝗂𝖺 𝖯𝖾𝗇𝖽𝗋𝖺𝗀𝗈𝗇)', '𝖥𝖺𝗍𝖾/𝗌𝗍𝖺𝗒 𝗇𝗂𝗀𝗁𝗍: 𝖴𝗇𝗅𝗂𝗆𝗂𝗍𝖾𝖽 𝖡𝗅𝖺𝖽𝖾 𝖶𝗈𝗋𝗄𝗌'),
    ('𝖤𝗏𝖾𝗇 𝗂𝖿 𝗍𝗁𝗂𝗇𝗀𝗌 𝖺𝗋𝖾 𝗉𝖺𝗂𝗇𝖿𝗎𝗅 𝖺𝗇𝖽 𝗍𝗈𝗎𝗀𝗁, 𝗉𝖾𝗈𝗉𝗅𝖾 𝗌𝗁𝗈𝗎𝗅𝖽 𝖺𝗉𝗉𝗋𝖾𝖼𝗂𝖺𝗍𝖾 𝗐𝗁𝖺𝗍 𝗂𝗍 𝗆𝖾𝖺𝗇𝗌 𝗍𝗈 𝖻𝖾 𝖺𝗅𝗂𝗏𝖾 𝖺𝗍 𝖺𝗅𝗅.', '𝖸𝖺𝗍𝗈', '𝖭𝗈𝗋𝖺𝗀𝖺𝗆𝗂'),
    ("𝖨'𝖽 𝗋𝖺𝗍𝗁𝖾𝗋 𝖽𝗂𝖾 𝗈𝗇 𝗆𝗒 𝖿𝖾𝖾𝗍 𝗍𝗁𝖺𝗇 𝗅𝗂𝗏𝖾 𝗈𝗇 𝗆𝗒 𝖿𝖺𝖼𝖾.", '𝖤𝗋𝖾𝗇 𝖸𝖾𝖺𝗀𝖾𝗋', '𝖠𝗍𝗍𝖺𝖼𝗄 𝗈𝗇 𝖳𝗂𝗍𝖺𝗇'),
    ("𝖨 𝖽𝗈𝗇'𝗍 𝗐𝖺𝗇𝗍 𝗍𝗈 𝖼𝗈𝗇𝗊𝗎𝖾𝗋 𝖺𝗇𝗒𝗍𝗁𝗂𝗇𝗀. 𝖨 𝗃𝗎𝗌𝗍 𝗍𝗁𝗂𝗇𝗄 𝗍𝗁𝖾 𝗀𝗎𝗒 𝗐𝗂𝗍𝗁 𝗍𝗁𝖾 𝗆𝗈𝗌𝗍 𝖿𝗋𝖾𝖾𝖽𝗈𝗆 𝗂𝗇 𝗍𝗁𝗂𝗌 𝗐𝗁𝗈𝗅𝖾 𝗈𝖼𝖾𝖺𝗇... 𝗂𝗌 𝗍𝗁𝖾 𝖯𝗂𝗋𝖺𝗍𝖾 𝖪𝗂𝗇𝗀!", '𝖬𝗈𝗇𝗄𝖾𝗒 𝖣. 𝖫𝗎𝖿𝖿𝗒', '𝖮𝗇𝖾 𝖯𝗂𝖾𝖼𝖾'),
    ("𝖨𝗍'𝗌 𝗇𝗈𝗍 𝗍𝗁𝖾 𝗌𝗍𝗋𝖾𝗇𝗀𝗍𝗁 𝗈𝖿 𝖺 𝗁𝖾𝗋𝗈 𝗍𝗁𝖺𝗍 𝗆𝖺𝗍𝗍𝖾𝗋𝗌, 𝖻𝗎𝗍 𝗍𝗁𝖾 𝗌𝗍𝗋𝖾𝗇𝗀𝗍𝗁 𝗈𝖿 𝗍𝗁𝖾𝗂𝗋 𝗁𝖾𝖺𝗋𝗍.", '𝖭𝖺𝗍𝗌𝗎 𝖣𝗋𝖺𝗀𝗇𝖾𝖾𝗅', '𝖥𝖺𝗂𝗋𝗒 𝖳𝖺𝗂𝗅'),
    ("𝖳𝗁𝖾 𝗐𝗈𝗋𝗅𝖽 𝗂𝗌 𝗆𝖾𝗋𝖼𝗂𝗅𝖾𝗌𝗌, 𝖺𝗇𝖽 𝗂𝗍'𝗌 𝖺𝗅𝗌𝗈 𝗏𝖾𝗋𝗒 𝖻𝖾𝖺𝗎𝗍𝗂𝖿𝗎𝗅.", '𝖬𝗂𝗄𝖺𝗌𝖺 𝖠𝖼𝗄𝖾𝗋𝗆𝖺𝗇', '𝖠𝗍𝗍𝖺𝖼𝗄 𝗈𝗇 𝖳𝗂𝗍𝖺𝗇'),
    ("𝖭𝗈 𝗈𝗇𝖾 𝗄𝗇𝗈𝗐𝗌 𝗐𝗁𝖺𝗍 𝗍𝗁𝖾 𝖿𝗎𝗍𝗎𝗋𝖾 𝗁𝗈𝗅𝖽𝗌. 𝖳𝗁𝖺𝗍'𝗌 𝗐𝗁𝗒 𝗐𝖾 𝖼𝖺𝗇 𝗇𝖾𝗏𝖾𝗋 𝗌𝖺𝗒 𝗀𝗈𝗈𝖽𝖻𝗒𝖾.", '𝖨𝗌𝖺𝖺𝖼 𝖭𝖾𝗍𝖾𝗋𝗈', '𝖧𝗎𝗇𝗍𝖾𝗋 𝗑 𝖧𝗎𝗇𝗍𝖾𝗋'),
    ("𝖨𝖿 𝗒𝗈𝗎 𝗐𝖺𝗇𝗇𝖺 𝗆𝖺𝗄𝖾 𝗉𝖾𝗈𝗉𝗅𝖾 𝖽𝗋𝖾𝖺𝗆, 𝗒𝗈𝗎'𝗏𝖾 𝗀𝗈𝗍𝗍𝖺 𝗌𝗍𝖺𝗋𝗍 𝖻𝗒 𝖻𝖾𝗅𝗂𝖾𝗏𝗂𝗇𝗀 𝗂𝗇 𝗍𝗁𝖺𝗍 𝖽𝗋𝖾𝖺𝗆 𝗒𝗈𝗎𝗋𝗌𝖾𝗅𝖿!", '𝖲𝗁𝗈𝗒𝗈 𝖧𝗂𝗇𝖺𝗍𝖺', '𝖧𝖺𝗂𝗄𝗒𝗎𝗎!!'),
    ('𝖡𝖾𝗂𝗇𝗀 𝗐𝖾𝖺𝗄 𝗂𝗌 𝗇𝗈𝗍𝗁𝗂𝗇𝗀 𝗍𝗈 𝖻𝖾 𝖺𝗌𝗁𝖺𝗆𝖾𝖽 𝗈𝖿. 𝖲𝗍𝖺𝗒𝗂𝗇𝗀 𝗐𝖾𝖺𝗄 𝗂𝗌.', '𝖨𝗓𝗎𝗄𝗎 𝖬𝗂𝖽𝗈𝗋𝗂𝗒𝖺', '𝖬𝗒 𝖧𝖾𝗋𝗈 𝖠𝖼𝖺𝖽𝖾𝗆𝗂𝖺'),
    ('𝖤𝗏𝖾𝗇 𝗂𝖿 𝗒𝗈𝗎’𝗋𝖾 𝗐𝖾𝖺𝗄, 𝗍𝗁𝖾𝗋𝖾 𝖺𝗋𝖾 𝗆𝗂𝗋𝖺𝖼𝗅𝖾𝗌 𝗒𝗈𝗎 𝖼𝖺𝗇 𝗌𝖾𝗂𝗓𝖾 𝗐𝗂𝗍𝗁 𝗒𝗈𝗎𝗋 𝗁𝖺𝗇𝖽𝗌 𝗂𝖿 𝗒𝗈𝗎 𝖿𝗂𝗀𝗁𝗍 𝗈𝗇 𝗍𝗈 𝗍𝗁𝖾 𝗏𝖾𝗋𝗒 𝖾𝗇𝖽.', '𝖦𝗈𝗇 𝖥𝗋𝖾𝖾𝖼𝗌𝗌', '𝖧𝗎𝗇𝗍𝖾𝗋 𝗑 𝖧𝗎𝗇𝗍𝖾𝗋'),
    ('𝖳𝗁𝖾𝗋𝖾 𝖺𝗋𝖾 𝗇𝗈 𝗌𝗁𝗈𝗋𝗍𝖼𝗎𝗍𝗌 𝗂𝗇 𝗅𝗂𝖿𝖾. 𝖳𝗈 𝗐𝗂𝗇, 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝗍𝗈 𝗐𝗈𝗋𝗄 𝗁𝖺𝗋𝖽, 𝖿𝖺𝖼𝖾 𝗒𝗈𝗎𝗋 𝖽𝖾𝗆𝗈𝗇𝗌, 𝖺𝗇𝖽 𝗇𝖾𝗏𝖾𝗋 𝗀𝗂𝗏𝖾 𝗎𝗉.', '𝖸𝖺𝗆𝗂 𝖲𝗎𝗄𝖾𝗁𝗂𝗋𝗈', '𝖡𝗅𝖺𝖼𝗄 𝖢𝗅𝗈𝗏𝖾𝗋'),
    ('𝖳𝗋𝗎𝖾 𝗌𝗍𝗋𝖾𝗇𝗀𝗍𝗁 𝖼𝗈𝗆𝖾𝗌 𝖿𝗋𝗈𝗆 𝗍𝗁𝖾 𝗁𝖾𝖺𝗋𝗍, 𝗇𝗈𝗍 𝗃𝗎𝗌 𝖻𝗋𝗎𝗍𝖾 𝖿𝗈𝗋𝖼𝖾.', '𝖤𝖽𝗐𝖺𝗋𝖽 𝖤𝗅𝗋𝗂𝖼', '𝖥𝗎𝗅𝗅𝗆𝖾𝗍𝖺𝗅 𝖠𝗅𝖼𝗁𝖾𝗆𝗂𝗌𝗍'),
    ('𝖳𝗁𝖾 𝖿𝖾𝖺𝗋 𝗈𝖿 𝖽𝖾𝖺𝗍𝗁 𝖿𝗈𝗅𝗅𝗈𝗐𝗌 𝖿𝗋𝗈𝗆 𝗍𝗁𝖾 𝖿𝖾𝖺𝗋 𝗈𝖿 𝗅𝗂𝖿𝖾. 𝖠 𝗆𝖺𝗇 𝗐𝗁𝗈 𝗅𝗂𝗏𝖾𝗌 𝖿𝗎𝗅𝗅𝗒 𝗂𝗌 𝗉𝗋𝖾𝗉𝖺𝗋𝖾𝖽 𝗍𝗈 𝖽𝗂𝖾 𝖺𝗍 𝖺𝗇𝗒 𝗍𝗂𝗆𝖾.', '𝖲𝗁𝗂𝗇𝗈𝖻𝗎 𝖲𝖾𝗇𝗌𝗎𝗂', '𝖸𝗎 𝖸𝗎 𝖧𝖺𝗄𝗎𝗌𝗁𝗈'),
    ('𝖨𝗇 𝗍𝗁𝗂𝗌 𝗐𝗈𝗋𝗅𝖽, 𝗐𝗁𝖾𝗋𝖾𝗏𝖾𝗋 𝗍𝗁𝖾𝗋𝖾 𝗂𝗌 𝗅𝗂𝗀𝗁𝗍 – 𝗍𝗁𝖾𝗋𝖾 𝖺𝗋𝖾 𝖺𝗅𝗌𝗈 𝗌𝗁𝖺𝖽𝗈𝗐𝗌. 𝖠𝗌 𝗅𝗈𝗇𝗀 𝖺𝗌 𝗍𝗁𝖾 𝖼𝗈𝗇𝖼𝖾𝗉𝗍 𝗈𝖿 𝗐𝗂𝗇𝗇𝖾𝗋𝗌 𝖾𝗑𝗂𝗌𝗍𝗌, 𝗍𝗁𝖾𝗋𝖾 𝗆𝗎𝗌𝗍 𝖺𝗅𝗌𝗈 𝖻𝖾 𝗅𝗈𝗌𝖾𝗋𝗌.', '𝖫𝖾𝗅𝗈𝗎𝖼𝗁 𝗏𝗂 𝖡𝗋𝗂𝗍𝖺𝗇𝗇𝗂𝖺', '𝖢𝗈𝖽𝖾 𝖦𝖾𝖺𝗌𝗌'),
    ('𝖨’𝖽 𝗋𝖺𝗍𝗁𝖾𝗋 𝗍𝗋𝗎𝗌𝗍 𝖺𝗇𝖽 𝗋𝖾𝗀𝗋𝖾𝗍 𝗍𝗁𝖺𝗇 𝖽𝗈𝗎𝖻𝗍 𝖺𝗇𝖽 𝗋𝖾𝗀𝗋𝖾𝗍.', '𝖪𝗂𝗋𝗂𝗍𝗌𝗎𝗀𝗎 𝖤𝗆𝗂𝗒𝖺', '𝖥𝖺𝗍𝖾/𝖹𝖾𝗋𝗈'),
    ('𝖸𝗈𝗎 𝗌𝗁𝗈𝗎𝗅𝖽 𝗇𝖾𝗏𝖾𝗋 𝗀𝗂𝗏𝖾 𝗎𝗉 𝗈𝗇 𝗅𝗂𝖿𝖾, 𝗇𝗈 𝗆𝖺𝗍𝗍𝖾𝗋 𝗁𝗈𝗐 𝗒𝗈𝗎 𝖿𝖾𝖾𝗅. 𝖭𝗈 𝗆𝖺𝗍𝗍𝖾𝗋 𝗁𝗈𝗐 𝗁𝖺𝗋𝖽 𝗍𝗁𝗂𝗇𝗀𝗌 𝗀𝖾𝗍, 𝗒𝗈𝗎 𝗁𝖺𝗏𝖾 𝗍𝗈 𝗁𝗈𝗅𝖽 𝗈𝗇 𝗍𝗈 𝗒𝗈𝗎𝗋 𝗅𝗂𝖿𝖾, 𝗇𝗈 𝗆𝖺𝗍𝗍𝖾𝗋 𝗐𝗁𝖺𝗍.', '𝖬𝗂𝗌𝖺𝗄𝗂 𝖳𝖺𝗄𝖺𝗁𝖺𝗌𝗁𝗂', '𝖩𝗎𝗇𝗃𝗈𝗎 𝖱𝗈𝗆𝖺𝗇𝗍𝗂𝖼𝖺'),
    ("𝖳𝗁𝖾 𝗍𝗋𝗎𝖾 𝗆𝖾𝖺𝗌𝗎𝗋𝖾 𝗈𝖿 𝖺 𝗌𝗁𝗂𝗇𝗈𝖻𝗂 𝗂𝗌 𝗇𝗈𝗍 𝗁𝗈𝗐 𝗁𝖾 𝗅𝗂𝗏𝖾𝗌 𝖻𝗎𝗍 𝗁𝗈𝗐 𝗁𝖾 𝖽𝗂𝖾𝗌. 𝖨𝗍's 𝗇𝗈𝗍 𝗐𝗁𝖺𝗍 𝗍𝗁𝖾𝗒 𝖽𝗈 𝗂𝗇 𝗅𝗂𝖿𝖾, 𝖻𝗎𝗍 𝗐𝗁𝖺𝗍 𝗍𝗁𝖾𝗒 𝖽𝗂𝖽 𝖻𝖾𝖿𝗈𝗋𝖾 𝖽𝗒𝗂𝗇𝗀 𝗍𝗁𝖺𝗍 𝗉𝗋𝗈𝗏𝖾𝗌 𝗍𝗁𝖾𝗂𝗋 𝗐𝗈𝗋𝗍𝗁.", '𝖩𝗂𝗋𝖺𝗂𝗒𝖺', '𝖭𝖺𝗋𝗎𝗍𝗈'),
]

QUOTES_IMG = [
    'https://i.imgur.com/Iub4RYj.jpg',
    'https://i.imgur.com/uvNMdIl.jpg',
    'https://i.imgur.com/YOBOntg.jpg',
    'https://i.imgur.com/fFpO2ZQ.jpg',
    'https://i.imgur.com/f0xZceK.jpg',
    'https://i.imgur.com/RlVcCip.jpg',
    'https://i.imgur.com/CjpqLRF.jpg',
    'https://i.imgur.com/8BHZDk6.jpg',
    'https://i.imgur.com/8bHeMgy.jpg',
    'https://i.imgur.com/5K3lMvr.jpg',
    'https://i.imgur.com/NTzw4RN.jpg',
    'https://i.imgur.com/wJxryAn.jpg',
    'https://i.imgur.com/9L0DWzC.jpg',
    'https://i.imgur.com/sBe8TTs.jpg',
    'https://i.imgur.com/1Au8gdf.jpg',
    'https://i.imgur.com/28hFQeU.jpg',
    'https://i.imgur.com/Qvc03JY.jpg',
    'https://i.imgur.com/gSX6Xlf.jpg',
    'https://i.imgur.com/iP26Hwa.jpg',
    'https://i.imgur.com/uSsJoX8.jpg',
    'https://i.imgur.com/OvX3oHB.jpg',
    'https://i.imgur.com/JMWuksm.jpg',
    'https://i.imgur.com/lhM3fib.jpg',
    'https://i.imgur.com/64IYKkw.jpg',
    'https://i.imgur.com/nMbyA3J.jpg',
    'https://i.imgur.com/7KFQhY3.jpg',
    'https://i.imgur.com/mlKb7zt.jpg',
    'https://i.imgur.com/JCQGJVw.jpg',
    'https://i.imgur.com/hSFYDEz.jpg',
    'https://i.imgur.com/PQRjAgl.jpg',
    'https://i.imgur.com/ot9624U.jpg',
    'https://i.imgur.com/iXmqN9y.jpg',
    'https://i.imgur.com/RhNBeGr.jpg',
    'https://i.imgur.com/tcMVNa8.jpg',
    'https://i.imgur.com/LrVg810.jpg',
    'https://i.imgur.com/TcWfQlz.jpg',
    'https://i.imgur.com/muAUdvJ.jpg',
    'https://i.imgur.com/AtC7ZRV.jpg',
    'https://i.imgur.com/sCObQCQ.jpg',
    'https://i.imgur.com/AJFDI1r.jpg',
    'https://i.imgur.com/TCgmRrH.jpg',
    'https://i.imgur.com/LMdmhJU.jpg',
    'https://i.imgur.com/eyyax0N.jpg',
    'https://i.imgur.com/YtYxV66.jpg',
    'https://i.imgur.com/292w4ye.jpg',
    'https://i.imgur.com/6Fm1vdw.jpg',
    'https://i.imgur.com/2vnBOZd.jpg',
    'https://i.imgur.com/j5hI9Eb.jpg',
    'https://i.imgur.com/cAv7pJB.jpg',
    'https://i.imgur.com/jvI7Vil.jpg',
    'https://i.imgur.com/fANpjsg.jpg',
    'https://i.imgur.com/5o1SJyo.jpg',
    'https://i.imgur.com/dSVxmh8.jpg',
    'https://i.imgur.com/02dXlAD.jpg',
    'https://i.imgur.com/htvIoGY.jpg',
    'https://i.imgur.com/hy6BXOj.jpg',
    'https://i.imgur.com/OuwzNYu.jpg',
    'https://i.imgur.com/L8vwvc2.jpg',
    'https://i.imgur.com/3VMVF9y.jpg',
    'https://i.imgur.com/yzjq2n2.jpg',
    'https://i.imgur.com/0qK7TAN.jpg',
    'https://i.imgur.com/zvcxSOX.jpg',
    'https://i.imgur.com/FO7bApW.jpg',
    'https://i.imgur.com/KK06gwg.jpg',
    'https://i.imgur.com/6lG4tsO.jpg',
]

@cutiepii_callback(pattern=r"^change_quote$")
async def change_quote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quote, character, anime = random.choice(QUOTES)
    text = f"<i>❝ {quote} ❞</i>\n\n<b>{character}</b> from <b>{anime}</b>"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Change", callback_data="change_quote")]]
    )

    try:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


@cutiepii_callback(pattern=r"^change_img_quote$")
async def change_img_quote_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    random_image = random.choice(QUOTES_IMG)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Change", callback_data="change_img_quote")]]
    )

    try:
        await query.edit_message_media(
            media=InputMediaPhoto(media=random_image),
            reply_markup=keyboard
        )
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


@cutiepii_cmd(command=["animequote", "aquote"])
async def text_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    quote, character, anime = random.choice(QUOTES)
    text = f"<i>❝ {quote} ❞</i>\n\n<b>{character}</b> from <b>{anime}</b>"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Change", callback_data="change_quote")]]
    )
    await message.reply_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["iaquotes", "iaquote"])
async def image_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    random_image = random.choice(QUOTES_IMG)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Change", callback_data="change_img_quote")]]
    )
    await message.reply_photo(photo=random_image, reply_markup=keyboard)


# Register Callback Handlers


async def get_random_shayri():
    url = "https://hindi-quotes.vercel.app/random"
    try:
        from Cutiepii_Robot import http
        response = await http.get(url, timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            shayri = data.get("quote", "शायरी प्राप्त करने में त्रुटि हुई!")
            shayri_type = data.get("type", "अनजान प्रकार")
            return shayri, shayri_type
        else:
            return "त्रुटि: शायरी प्राप्त करने में त्रुटि हुई। कृपया बाद में प्रयास करें।", None
    except Exception as e:
        return f"त्रुटि: {str(e)}", None


@cutiepii_cmd(command="shayri")
async def fetch_shayri(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    shayri, shayri_type = await get_random_shayri()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Change", callback_data="change_shayri")]]
    )
    if shayri_type:
        text = f"<b>शायरी का प्रकार</b>: {html.escape(shayri_type.capitalize())}\n\n❝ <i>{html.escape(shayri)}</i> ❞"
        await message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(shayri)


@cutiepii_callback(pattern=r"^change_shayri$")
async def change_shayri_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    shayri, shayri_type = await get_random_shayri()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Change", callback_data="change_shayri")]]
    )
    if shayri_type:
        text = f"<b>शायरी का प्रकार</b>: {html.escape(shayri_type.capitalize())}\n\n❝ <i>{html.escape(shayri)}</i> ❞"
        try:
            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        await query.answer(shayri, show_alert=True)



__mod_name__ = "Quotes"

__help__ = True
