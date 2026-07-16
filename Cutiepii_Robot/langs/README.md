# 🌐 Multi-Language System for Cutiepii Robot

This directory contains the multi-language support system for Cutiepii Robot, inspired by [EnterpriseALRobot's language system](https://github.com/AnimeKaizoku/EnterpriseALRobot/tree/master/tg_bot/langs).

---

## 📁 Directory Structure

```
langs/
├── __init__.py          # Language loader and manager
├── en.yaml              # English (Default)
├── hi.yaml              # Hindi (हिन्दी)
├── es.yaml              # Spanish (Español)
├── fr.yaml              # French (Français)
├── de.yaml              # German (Deutsch)
├── pt.yaml              # Portuguese (Português)
├── ru.yaml              # Russian (Русский)
├── ar.yaml              # Arabic (العربية)
├── id.yaml              # Indonesian
├── it.yaml              # Italian (Italiano)
└── README.md            # This file
```

---

## 🌍 Available Languages

| Code | Language | Status |
|------|----------|--------|
| `en` | English 🇬🇧 | ✅ Complete |
| `hi` | हिन्दी 🇮🇳 | ✅ Complete |
| `es` | Español 🇪🇸 | ✅ Complete |
| `fr` | Français 🇫🇷 | 🔄 In Progress |
| `de` | Deutsch 🇩🇪 | 🔄 In Progress |
| `pt` | Português 🇵🇹 | 🔄 In Progress |
| `ru` | Русский 🇷🇺 | 🔄 In Progress |
| `ar` | العربية 🇸🇦 | 🔄 In Progress |
| `id` | Indonesian 🇮🇩 | 🔄 In Progress |
| `it` | Italiano 🇮🇹 | 🔄 In Progress |

---

## 📝 YAML File Structure

Each language file follows this structure:

```yaml
# Language metadata
language:
  select: "Language selection text"
  changed: "Language changed message"
  current: "Current language message"

# Module help texts
admin:
  help: |
    Multi-line help text
    for admin module

bans:
  help: |
    Multi-line help text
    for bans module

# ... more modules
```

---

## 🚀 Usage

### For Users

1. **Change Language:**
   ```
   /language or /lang
   ```
   This opens an interactive menu to select your preferred language.

2. **Check Current Language:**
   ```
   /currentlang
   ```

3. **Language Priority:**
   - In groups: Group language setting applies to all members
   - In private chat: Personal language preference
   - Group setting overrides personal preference

### For Developers

#### Loading a Language String

```python
from Cutiepii_Robot.langs import get_string, get_help_text

# Get a specific string
text = get_string("en", "language.select")

# Get help text for a module
help_text = get_help_text("en", "admin")

# Get string with formatting
text = get_string("en", "welcome.message", name="John", count=5)
```

#### Get User's Language

```python
from Cutiepii_Robot.modules.sql import lang_sql

# Get language for chat/user
lang_code = lang_sql.get_lang(chat_id=123456, user_id=789012)

# Set language
lang_sql.set_chat_lang(chat_id=123456, lang_code="hi")
lang_sql.set_user_lang(user_id=789012, lang_code="es")
```

#### Using in Modules

```python
from telegram import Update
from telegram.ext import ContextTypes
from Cutiepii_Robot.modules.sql import lang_sql
from Cutiepii_Robot.langs import get_help_text

async def some_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get user's language
    lang = lang_sql.get_lang(
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id
    )
    
    # Get localized help text
    help_text = get_help_text(lang, "admin")
    
    await update.message.reply_text(help_text)
```

---

## 🔧 Adding a New Language

### Step 1: Create Language File

Create a new file `langs/xx.yaml` (where `xx` is the language code):

```yaml
# Language metadata
language:
  select: "Translated language selection text"
  changed: "Translated language changed message"
  current: "Translated current language message"

# Translate all module help texts
admin:
  help: |
    Translated admin help text
    
bans:
  help: |
    Translated bans help text

# ... translate all modules
```

### Step 2: Update Available Languages

Edit `langs/__init__.py`:

```python
AVAILABLE_LANGUAGES = {
    "en": "English 🇬🇧",
    "hi": "हिन्दी 🇮🇳",
    "es": "Español 🇪🇸",
    "xx": "Your Language 🏳️",  # Add your language here
    # ... more languages
}
```

### Step 3: Test Your Translation

```python
from Cutiepii_Robot.langs import get_string, load_language

# Load your language
data = load_language("xx")
print(data)

# Test a string
text = get_string("xx", "language.select")
print(text)
```

---

## 📋 Translation Guidelines

### 1. Preserve Formatting

Keep all markdown formatting:
- `*bold*` → Stay bold
- `**text**` → Stay bold
- Backticks `` `code` `` → Stay as code
- `➛` → Keep the arrow symbol

### 2. Preserve Command Names

Commands should NOT be translated:
- ✅ `/help` stays `/help`
- ❌ `/ayuda` (don't translate to Spanish)

### 3. Preserve Placeholders

Keep format placeholders:
- `{name}` → Keep as is
- `{count}` → Keep as is
- `{BOT_NAME}` → Keep as is

### 4. Adapt Cultural Context

- Use appropriate greetings for the culture
- Adjust formality level as needed
- Use culturally relevant examples

### 5. Test Thoroughly

- Check all special characters display correctly
- Verify emoji display properly
- Test in actual Telegram to see formatting

---

## 🎨 Best Practices

### 1. Consistency

- Use the same term for the same concept throughout
- Keep tone consistent across all modules
- Maintain the same level of formality

### 2. Clarity

- Use clear, simple language
- Avoid ambiguous terms
- Explain technical terms when needed

### 3. Completeness

- Translate ALL strings, not just some
- Don't leave English fallbacks unless necessary
- Include all help texts for all modules

### 4. Quality

- Have native speakers review
- Test in real usage scenarios
- Get feedback from users

---

## 🔍 String Keys Reference

### Language Module

- `language.select` - Language selection menu text
- `language.changed` - Language changed confirmation
- `language.current` - Current language display

### Module Help Texts

- `{module_name}.help` - Full help text for module

Examples:
- `admin.help`
- `bans.help`
- `warns.help`
- `welcome.help`
- `locks.help`
- `notes.help`
- `filters.help`
- etc.

---

## 📊 Translation Progress

Track your translation progress:

- [ ] Language metadata (select, changed, current)
- [ ] Admin module
- [ ] Bans module
- [ ] Warns module
- [ ] Anti-Flood module
- [ ] Welcome module
- [ ] Locks module
- [ ] Notes module
- [ ] Filters module
- [ ] Blacklist module
- [ ] Fun module
- [ ] Google module
- [ ] Translator module
- [ ] Stickers module
- [ ] Reminders module
- [ ] ... (add all modules)

---

## 🤝 Contributing Translations

Want to help translate Cutiepii Robot?

1. **Fork the Repository**
2. **Create Your Language File**
3. **Translate All Strings**
4. **Test Your Translation**
5. **Submit a Pull Request**

### Translation Checklist

- [ ] All strings translated
- [ ] Formatting preserved
- [ ] Commands not translated
- [ ] Placeholders preserved
- [ ] Tested in Telegram
- [ ] Reviewed by native speaker
- [ ] README updated

---

## 🐛 Troubleshooting

### Language Not Showing

1. Check if language file exists in `langs/` directory
2. Verify language code in `AVAILABLE_LANGUAGES` dict
3. Check YAML syntax is valid
4. Restart the bot

### Strings Not Loading

1. Check YAML indentation (use spaces, not tabs)
2. Verify string keys match exactly
3. Check for special characters that need escaping
4. Review logs for error messages

### Formatting Issues

1. Ensure markdown is properly escaped
2. Check that backticks are paired correctly
3. Verify emoji codes are valid
4. Test in actual Telegram client

---

## 📞 Support

Need help with translations?

- Open an issue on GitHub
- Join our support chat
- Check the documentation
- Ask in the community forum

---

## 📜 License

All translation files are licensed under BSD 2-Clause License, same as the main project.

---

## 🙏 Credits

- **Language System Inspired By:** [EnterpriseALRobot](https://github.com/AnimeKaizoku/EnterpriseALRobot)
- **Current Translations:**
  - English: Cutiepii Team
  - Hindi: Cutiepii Team
  - Spanish: Cutiepii Team
  - (Add contributors here)

---

## 🎉 Thank You!

Thanks to all translators who help make Cutiepii Robot accessible to users worldwide!

Your contributions help break language barriers and bring communities together! 🌍❤️
