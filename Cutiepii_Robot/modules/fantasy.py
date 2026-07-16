"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import random
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

# ========================================
# Command: /wizard [spells|houses|elixirs|wizards] [query]
# ========================================

@cutiepii_cmd(command="wizard", group=430)
async def wizard_world(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text(
            "🔮 <b>Harry Potter Wizard World Search</b>\n\n"
            "<b>Usage:</b>\n"
            "❍ <code>/wizard spells [query]</code> - Search for spells or incantations.\n"
            "❍ <code>/wizard houses [query]</code> - Search for Hogwarts houses.\n"
            "❍ <code>/wizard elixirs [query]</code> - Search for magical potions.\n"
            "❍ <code>/wizard wizards [query]</code> - Search for wizards/witches.\n\n"
            "<i>Example: /wizard spells lumos</i>",
            parse_mode=ParseMode.HTML
        )
        return

    category = args[0].lower()
    query = " ".join(args[1:]).strip() if len(args) > 1 else ""

    if category not in ["spells", "houses", "elixirs", "wizards"]:
        await message.reply_text("Invalid category. Use <code>spells</code>, <code>houses</code>, <code>elixirs</code>, or <code>wizards</code>.", parse_mode=ParseMode.HTML)
        return

    await message.reply_chat_action("typing")
    base_url = "https://wizard-world-api.herokuapp.com"

    try:
        if category == "spells":
            url = f"{base_url}/Spells"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                await message.reply_text("Wizard World API is currently unavailable.")
                return
            data = r.json()
            if query:
                results = [s for s in data if query.lower() in s.get("name", "").lower() or query.lower() in s.get("incantation", "").lower() or query.lower() in s.get("effect", "").lower()]
            else:
                results = [random.choice(data)] if data else []

            if not results:
                await message.reply_text(f"No spells found matching: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return

            reply = "🪄 <b>Harry Potter Spells:</b>\n\n"
            for item in results[:5]:  # Limit to 5 results
                name = item.get("name", "Unknown")
                inc = item.get("incantation", "None")
                effect = item.get("effect", "Unknown")
                stype = item.get("type", "Unknown")
                light = item.get("light", "Unknown")
                reply += (
                    f"▪️ <b>{html.escape(name)}</b>\n"
                    f"  💬 <b>Incantation:</b> <code>{html.escape(inc)}</code>\n"
                    f"  ✨ <b>Effect:</b> {html.escape(effect)}\n"
                    f"  🏷️ <b>Type:</b> {html.escape(stype)}\n"
                    f"  💡 <b>Light:</b> {html.escape(light)}\n\n"
                )
            await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML)

        elif category == "houses":
            url = f"{base_url}/Houses"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                await message.reply_text("Wizard World API is currently unavailable.")
                return
            data = r.json()
            if query:
                results = [h for h in data if query.lower() in h.get("name", "").lower() or query.lower() in h.get("founder", "").lower()]
            else:
                results = data

            if not results:
                await message.reply_text(f"No houses found matching: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return

            reply = "🏰 <b>Hogwarts Houses:</b>\n\n"
            for item in results:
                name = item.get("name", "Unknown")
                colors = item.get("houseColours", "Unknown")
                founder = item.get("founder", "Unknown")
                animal = item.get("animal", "Unknown")
                element = item.get("element", "Unknown")
                ghost = item.get("ghost", "Unknown")
                room = item.get("commonRoom", "Unknown")
                reply += (
                    f"🛡️ <b>{html.escape(name)}</b>\n"
                    f"  🎨 <b>Colours:</b> {html.escape(colors)}\n"
                    f"  👤 <b>Founder:</b> {html.escape(founder)}\n"
                    f"  🦁 <b>Animal:</b> {html.escape(animal)}\n"
                    f"  🌪️ <b>Element:</b> {html.escape(element)}\n"
                    f"  👻 <b>Ghost:</b> {html.escape(ghost)}\n"
                    f"  🚪 <b>Common Room:</b> {html.escape(room)}\n\n"
                )
            await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML)

        elif category == "elixirs":
            url = f"{base_url}/Elixirs"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                await message.reply_text("Wizard World API is currently unavailable.")
                return
            data = r.json()
            if query:
                results = [e for e in data if query.lower() in e.get("name", "").lower() or query.lower() in e.get("effect", "").lower()]
            else:
                results = [random.choice(data)] if data else []

            if not results:
                await message.reply_text(f"No elixirs found matching: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return

            reply = "🧪 <b>Magical Potions & Elixirs:</b>\n\n"
            for item in results[:3]:  # Limit to 3
                name = item.get("name", "Unknown")
                effect = item.get("effect", "None")
                side_effects = item.get("sideEffects", "None")
                difficulty = item.get("difficulty", "Unknown")
                ingredients = ", ".join(ing.get("name", "") for ing in item.get("ingredients", [])) or "None"
                reply += (
                    f"▪️ <b>{html.escape(name)}</b>\n"
                    f"  ✨ <b>Effect:</b> {html.escape(effect)}\n"
                    f"  ⚠️ <b>Side Effects:</b> {html.escape(side_effects)}\n"
                    f"  📊 <b>Difficulty:</b> {html.escape(difficulty)}\n"
                    f"  🍀 <b>Ingredients:</b> {html.escape(ingredients)}\n\n"
                )
            await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML)

        elif category == "wizards":
            url = f"{base_url}/Wizards"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                await message.reply_text("Wizard World API is currently unavailable.")
                return
            data = r.json()
            if query:
                results = [
                    w for w in data 
                    if query.lower() in f"{w.get('firstName', '')} {w.get('lastName', '')}".lower()
                ]
            else:
                # Pick 5 random wizards
                results = random.sample(data, min(5, len(data))) if data else []

            if not results:
                await message.reply_text(f"No wizards found matching: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return

            reply = "🧙‍♂️ <b>Magical Wizards & Witches:</b>\n\n"
            for item in results[:10]:  # Limit to 10
                first = item.get("firstName", "")
                last = item.get("lastName", "")
                name = f"{first} {last}".strip() or "Unknown Wizard"
                elixirs = ", ".join(e.get("name", "") for e in item.get("elixirs", [])) or "None"
                reply += (
                    f"▪️ <b>{html.escape(name)}</b>\n"
                    f"  🧪 <b>Potions Invented:</b> {html.escape(elixirs)}\n\n"
                )
            await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"An error occurred while communicating with the magic network: {e}")


# ========================================
# Command: /poke [name/id]
# ========================================

@cutiepii_cmd(command="poke", group=431)
async def pokemon_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Please specify a Pokemon name or ID. Usage: `/poke [name/id]`", parse_mode=ParseMode.MARKDOWN)
        return

    poke_input = args[0].strip().lower()
    await message.reply_chat_action("upload_photo")

    try:
        url = f"https://pokeapi.co/api/v2/pokemon/{poke_input}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 404:
            await message.reply_text(f"Could not find Pokemon: <b>{html.escape(poke_input)}</b>", parse_mode=ParseMode.HTML)
            return
        if r.status_code != 200:
            await message.reply_text("PokéAPI is currently unavailable. Please try again later.")
            return

        data = r.json()
        
        # Parse data
        name = data.get("name", "Unknown").capitalize()
        poke_id = data.get("id", 0)
        height = data.get("height", 0) / 10.0  # in meters
        weight = data.get("weight", 0) / 10.0  # in kg
        types = ", ".join(t.get("type", {}).get("name", "").capitalize() for t in data.get("types", []))
        abilities = ", ".join(a.get("ability", {}).get("name", "").replace("-", " ").capitalize() for a in data.get("abilities", []))
        
        # Stats
        stats = {s.get("stat", {}).get("name", ""): s.get("base_stat", 0) for s in data.get("stats", [])}
        hp = stats.get("hp", 0)
        atk = stats.get("attack", 0)
        dfn = stats.get("defense", 0)
        sp_atk = stats.get("special-attack", 0)
        sp_dfn = stats.get("special-defense", 0)
        spd = stats.get("speed", 0)

        # High-res official artwork
        artwork = data.get("sprites", {}).get("other", {}).get("official-artwork", {}).get("front_default") or data.get("sprites", {}).get("front_default")

        caption = (
            f"🎮 <b>Pokédex Entry #{poke_id}: {name}</b>\n\n"
            f"🧬 <b>Types:</b> {types}\n"
            f"📐 <b>Height:</b> {height} m | ⚖️ <b>Weight:</b> {weight} kg\n"
            f"🧠 <b>Abilities:</b> {abilities}\n\n"
            f"📊 <b>Base Stats:</b>\n"
            f"❍ <b>HP:</b> <code>{hp}</code>\n"
            f"❍ <b>Attack:</b> <code>{atk}</code> | <b>Defense:</b> <code>{dfn}</code>\n"
            f"❍ <b>Sp. Atk:</b> <code>{sp_atk}</code> | <b>Sp. Def:</b> <code>{sp_dfn}</code>\n"
            f"❍ <b>Speed:</b> <code>{spd}</code>"
        )

        if artwork:
            await message.reply_photo(photo=artwork, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"An error occurred during Pokédex lookup: {e}")


# ========================================
# Command: /rick [character name]
# ========================================

@cutiepii_cmd(command="rick", group=432)
async def rick_morty_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    await message.reply_chat_action("upload_photo")

    try:
        # If no arguments, fetch a random character
        if not args:
            rand_id = random.randint(1, 826)
            url = f"https://rickandmortyapi.com/api/character/{rand_id}"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                await message.reply_text("Rick & Morty API is currently unavailable.")
                return
            char = r.json()
        else:
            query = " ".join(args).strip()
            url = f"https://rickandmortyapi.com/api/character/?name={query}"
            r = requests.get(url, timeout=10)
            if r.status_code == 404:
                await message.reply_text(f"Wubba lubba dub dub! No character found matching: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return
            if r.status_code != 200:
                await message.reply_text("Rick & Morty API is currently unavailable.")
                return
            results = r.json().get("results", [])
            if not results:
                await message.reply_text(f"No character found matching: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return
            char = results[0]  # Pick the first result

        # Parse character info
        name = char.get("name", "Unknown")
        status = char.get("status", "Unknown")
        species = char.get("species", "Unknown")
        gender = char.get("gender", "Unknown")
        origin = char.get("origin", {}).get("name", "Unknown")
        location = char.get("location", {}).get("name", "Unknown")
        image = char.get("image")

        status_emoji = "🟢" if status.lower() == "alive" else "🔴" if status.lower() == "dead" else "🟡"

        caption = (
            f"🛸 <b>Rick & Morty Character Info</b>\n\n"
            f"👤 <b>Name:</b> {html.escape(name)}\n"
            f"{status_emoji} <b>Status:</b> {html.escape(status)}\n"
            f"🧬 <b>Species:</b> {html.escape(species)}\n"
            f"⚧️ <b>Gender:</b> {html.escape(gender)}\n"
            f"🌍 <b>Origin:</b> {html.escape(origin)}\n"
            f"📍 <b>Last Location:</b> {html.escape(location)}"
        )

        if image:
            await message.reply_photo(photo=image, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"An error occurred while exploring the multiverse: {e}")


# ========================================
# Module Help and Stats
# ========================================

__help__ = True

__mod_name__ = "Fantasy"
