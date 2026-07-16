"""
Multi-Language Support System for Cutiepii Robot
Inspired by EnterpriseALRobot's language system
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

# Available languages
AVAILABLE_LANGUAGES = {
    "en": "English 🇬🇧",
    "hi": "हिन्दी 🇮🇳",
    "es": "Español 🇪🇸",
    "fr": "Français 🇫🇷",
    "de": "Deutsch 🇩🇪",
    "pt": "Português 🇵🇹",
    "ru": "Русский 🇷🇺",
    "ar": "العربية 🇸🇦",
    "id": "Indonesian 🇮🇩",
    "it": "Italiano 🇮🇹",
}

DEFAULT_LANGUAGE = "en"

# Cache for loaded language strings
_language_cache: Dict[str, Dict[str, Any]] = {}


def get_lang_folder() -> Path:
    """Get the langs folder path."""
    return Path(__file__).parent


def load_language(lang_code: str) -> Dict[str, Any]:
    """
    Load language strings from YAML file.
    
    Args:
        lang_code: Language code (e.g., 'en', 'hi')
    
    Returns:
        Dictionary containing all language strings
    """
    # Check cache first
    if lang_code in _language_cache:
        return _language_cache[lang_code]
    
    # Validate language code
    if lang_code not in AVAILABLE_LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    # Load language file
    lang_file = get_lang_folder() / f"{lang_code}.yaml"
    
    if not lang_file.exists():
        # Fallback to English
        lang_file = get_lang_folder() / f"{DEFAULT_LANGUAGE}.yaml"
    
    try:
        with open(lang_file, "r", encoding="utf-8") as f:
            lang_data = yaml.safe_load(f)
            _language_cache[lang_code] = lang_data
            return lang_data
    except Exception as e:
        print(f"Error loading language file {lang_file}: {e}")
        return {}


def get_string(lang_code: str, key: str, **kwargs) -> str:
    """
    Get a translated string.
    
    Args:
        lang_code: Language code
        key: String key (e.g., 'admin.help')
        **kwargs: Format arguments
    
    Returns:
        Translated and formatted string
    """
    lang_data = load_language(lang_code)
    
    # Navigate nested keys (e.g., 'admin.help')
    keys = key.split('.')
    value = lang_data
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Fallback to English
            eng_data = load_language(DEFAULT_LANGUAGE)
            value = eng_data
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return f"String not found: {key}"
            break
    
    # Format string if it's a string type
    if isinstance(value, str) and kwargs:
        try:
            return value.format(**kwargs)
        except KeyError:
            return value
    
    return str(value)


def get_help_text(lang_code: str, module_name: str) -> str:
    """
    Get help text for a specific module.
    
    Args:
        lang_code: Language code
        module_name: Module name (e.g., 'admin', 'bans')
    
    Returns:
        Help text string
    """
    return get_string(lang_code, f"{module_name}.help")


def clear_cache():
    """Clear the language cache."""
    global _language_cache
    _language_cache = {}


# Initialize by loading default language
load_language(DEFAULT_LANGUAGE)
