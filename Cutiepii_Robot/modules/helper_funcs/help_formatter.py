import re
import html
from typing import Optional, List

# Compile regexes once globally for maximum speed
RE_INLINE_CODE = re.compile(r'`([^`\n]+)`')
RE_BOLD_DOUBLE = re.compile(r'\*\*([^\*\n]+)\*\*')
RE_BOLD_SINGLE = re.compile(r'\*([^\*\n]+)\*')
RE_ITALIC = re.compile(r'_([^_\n]+)_')
RE_STRIKE = re.compile(r'~~([^~\n]+)~~')
RE_SPOILER = re.compile(r'\|\|([^\|\n]+)\|\|')
# Multiline regex to match commands inside bullets on the whole string
RE_BULLET = re.compile(r'^(\s*)([➛❍•\-\*✥❂])\s+(/[^:]+?)\s*:\s*(.*)$', re.MULTILINE)

# Pre-compiled HTML tag replacements
SUPPORTED_TAGS = ['b', 'i', 'code', 'u', 's', 'pre', 'blockquote', 'tg-spoiler']
TAG_REPLACEMENTS = []
for tag in SUPPORTED_TAGS:
    TAG_REPLACEMENTS.append((f"&lt;{tag}&gt;", f"<{tag}>"))
    TAG_REPLACEMENTS.append((f"&lt;/{tag}&gt;", f"</{tag}>"))

RE_BLOCKQUOTE_EXPAND = re.compile(r'&lt;blockquote\s+expandable&gt;', re.IGNORECASE)
RE_CODE_CLASS = re.compile(r'&lt;code\s+class="([^"]+)"&gt;', re.IGNORECASE)

def format_help_menu(module_name: str, help_text: str) -> str:
    """
    Dynamically reformats any module help text into premium Telegram HTML formatting.
    Converts simple Markdown (*, _, `, ~~, ||) to HTML and wraps lists and descriptions cleanly.
    Optimized to process the entire string at once for maximum speed.
    """
    if not help_text or not isinstance(help_text, str):
        return help_text
        
    # 1. HTML Escape the entire text block at once
    escaped_text = html.escape(help_text)
    
    # 2. Revert escaped valid HTML tags that we want to support
    for old_tag, new_tag in TAG_REPLACEMENTS:
        escaped_text = escaped_text.replace(old_tag, new_tag)
        
    # Support attributes like <blockquote expandable> or <code class="...">
    escaped_text = RE_BLOCKQUOTE_EXPAND.sub('<blockquote expandable>', escaped_text)
    escaped_text = RE_CODE_CLASS.sub(r'<code class="\1">', escaped_text)
    escaped_text = escaped_text.replace("&lt;/blockquote&gt;", "</blockquote>")
    escaped_text = escaped_text.replace("&lt;/code&gt;", "</code>")
    
    # 3. Convert Markdown to HTML on the whole text block
    escaped_text = RE_INLINE_CODE.sub(r'<code>\1</code>', escaped_text)
    escaped_text = RE_BOLD_DOUBLE.sub(r'<b>\1</b>', escaped_text)
    escaped_text = RE_BOLD_SINGLE.sub(r'<b>\1</b>', escaped_text)
    escaped_text = RE_ITALIC.sub(r'<i>\1</i>', escaped_text)
    escaped_text = RE_STRIKE.sub(r'<s>\1</s>', escaped_text)
    escaped_text = RE_SPOILER.sub(r'<tg-spoiler>\1</tg-spoiler>', escaped_text)
    
    # 4. Format Command Bullets using multiline replacement
    escaped_text = RE_BULLET.sub(r'\1- <code>\3</code>: \4', escaped_text)
    
    content = escaped_text.strip()
    
    # Determine if it's a long message based on newline count
    newline_count = content.count('\n')
    is_long = newline_count > 12
    blockquote_tag = "<blockquote expandable>" if is_long else "<blockquote>"
    
    return f"{blockquote_tag}{content}</blockquote>"
