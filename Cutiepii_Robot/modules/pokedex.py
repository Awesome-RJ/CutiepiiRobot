import html
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import LOGGER, http
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command=["pokedex", "pokemon"])
async def pokedex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if not context.args:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a Pokémon name or ID. Usage: <code>/pokedex [name]</code>", parse_mode=ParseMode.HTML)
        return
    
    pokemon = context.args[0].lower().strip()
    pokedex_url = f"https://pokeapi.co/api/v2/pokemon/{pokemon}"
    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{pokemon}"
    
    status_message = await message.reply_text("<b>Pokédex Search</b>\nSearching Pokédex...", parse_mode=ParseMode.HTML)
    
    try:
        # Run both API requests concurrently
        r1, r2 = await asyncio.gather(
            http.get(pokedex_url, timeout=10.0),
            http.get(species_url, timeout=10.0),
            return_exceptions=True
        )
    except Exception as e:
        LOGGER.error(f"Failed to fetch Pokemon data: {e}")
        await status_message.edit_text("<b>Error</b>\nFailed to retrieve Pokémon data.", parse_mode=ParseMode.HTML)
        return

    # Check first response (basic info)
    if isinstance(r1, Exception) or r1.status_code != 200:
        await status_message.edit_text("<b>No Results Found</b>\nPokémon not found. Please verify the name or ID.", parse_mode=ParseMode.HTML)
        return

    data = r1.json()
    pokemon_name = data["name"].capitalize()
    pokedex_id = data["id"]
    
    # Types
    poke_type = ", ".join([t["type"]["name"].capitalize() for t in data["types"]])
    
    # Image
    poke_img = (
        data["sprites"]["other"]["official-artwork"]["front_default"]
        or f"https://img.pokemondb.net/artwork/large/{data['name']}.jpg"
    )
    
    # Abilities
    abilities = ", ".join([a["ability"]["name"].capitalize() for a in data["abilities"]])
    
    # Height & Weight
    height = f"{data['height'] / 10} m"
    weight = f"{data['weight'] / 10} kg"
    
    # Stats formatted as list
    stats_list = "\n".join([f"- <b>{s['stat']['name'].capitalize()}:</b> {s['base_stat']}" for s in data["stats"]])
    
    # Default values for description and gender
    description = "No description available."
    gender = "Unknown"

    # Process second response (species info)
    if not isinstance(r2, Exception) and r2.status_code == 200:
        sdata = r2.json()
        
        # English description
        for entry in sdata.get("flavor_text_entries", []):
            if entry.get("language", {}).get("name") == "en":
                description = entry["flavor_text"].replace("\n", " ").replace("\f", " ")
                break
                
        # Gender ratio
        gr = sdata.get("gender_rate", -1)
        if gr == -1:
            gender = "Genderless"
        else:
            female = (gr / 8) * 100
            male = 100 - female
            gender = f"Male: {male}% / Female: {female}%"

    caption = f"""<b>Pokémon:</b> {html.escape(pokemon_name)}
<b>Pokédex ID:</b> #{pokedex_id}
<b>Type:</b> {html.escape(poke_type)}
<b>Abilities:</b> {html.escape(abilities)}
<b>Height:</b> {height}
<b>Weight:</b> {weight}
<b>Gender Ratio:</b> {gender}

<b>Base Stats:</b>
{stats_list}

<b>Description:</b>
{html.escape(description)}"""

    try:
        await message.reply_photo(photo=poke_img, caption=caption, parse_mode=ParseMode.HTML)
        await status_message.delete()
    except Exception as e:
        LOGGER.error(f"Failed to send pokedex message: {e}")
        await status_message.edit_text("<b>Error</b>\nFailed to transmit the Pokémon data.", parse_mode=ParseMode.HTML)


__mod_name__ = "Pokedex"

__help__ = True
