"""
Android Helper Module for Cutiepii Robot
Provides commands to fetch device info, official TWRP recoveries, and Magisk releases.
"""

import httpx
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command="magisk")
async def magisk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the latest Magisk release."""
    message = update.effective_message
    url = "https://api.github.com/repos/topjohnwu/Magisk/releases/latest"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers={"User-Agent": "Cutiepii_Robot"}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                tag_name = data.get("tag_name", "N/A")
                changelog_url = data.get("html_url", "")
                assets = data.get("assets", [])
                download_url = ""
                for asset in assets:
                    if asset.get("name", "").endswith(".apk"):
                        download_url = asset.get("browser_download_url", "")
                        break
                
                msg = (
                    f"📦 <b>Magisk Latest Release ({tag_name})</b>\n\n"
                    f"🔗 <a href='{changelog_url}'>Changelog</a>\n"
                    f"⬇️ <a href='{download_url}'>Download APK</a>"
                )
                await message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                await message.reply_text("❌ Failed to fetch latest Magisk release from GitHub.")
        except Exception as e:
            await message.reply_text(f"❌ Error fetching Magisk details: {e}")


@cutiepii_cmd(command="twrp")
async def twrp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get official TWRP download link for a device."""
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Usage: <code>/twrp [device_codename]</code>\nExample: <code>/twrp sanders</code>", parse_mode=ParseMode.HTML)
        return

    codename = args[0].lower()
    url = f"https://dl.twrp.me/{codename}/"
    
    # We send a HEAD request to check if the link actually exists (if TWRP supports the device)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.head(url, follow_redirects=True, timeout=10)
            if response.status_code == 200:
                msg = (
                    f"🔍 <b>Official TWRP for {codename.upper()}</b>\n\n"
                    f"⬇️ <a href='{url}'>Download TWRP Recovery</a>"
                )
                await message.reply_text(msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            else:
                await message.reply_text(f"❌ No official TWRP recovery found for codename: <code>{codename}</code>.", parse_mode=ParseMode.HTML)
        except Exception as e:
            await message.reply_text(f"❌ Error checking TWRP support: {e}")


@cutiepii_cmd(command="device")
async def device_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get device specifications from PixelExperience API."""
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Usage: <code>/device [device_codename]</code>\nExample: <code>/device sweet</code>", parse_mode=ParseMode.HTML)
        return

    codename = args[0].lower()
    url = f"https://download.pixelexperience.org/api/v1/device/{codename}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if not data.get("error", False):
                    device_data = data.get("success", {})
                    brand = device_data.get("brand", "N/A")
                    name = device_data.get("name", "N/A")
                    spec_cpu = device_data.get("spec_cpu", "N/A")
                    spec_screen = device_data.get("spec_screen", "N/A")
                    spec_battery = device_data.get("spec_battery", "N/A")
                    spec_camera = device_data.get("spec_camera", "N/A")
                    
                    msg = (
                        f"📱 <b>Device Specifications: {brand} {name} ({codename.upper()})</b>\n\n"
                        f" ├ 🧠 <b>Processor:</b> {spec_cpu}\n"
                        f" ├ 🖥️ <b>Screen:</b> {spec_screen}\n"
                        f" ├ 🔋 <b>Battery:</b> {spec_battery}\n"
                        f" └ 📸 <b>Camera:</b> {spec_camera}\n"
                    )
                    await message.reply_text(msg, parse_mode=ParseMode.HTML)
                    return
            
            # Fallback to LineageOS wiki data or generic message
            await message.reply_text(
                f"ℹ️ <b>Device Codename:</b> <code>{codename}</code>\n"
                f"🔗 Check specifications on <a href='https://wiki.lineageos.org/devices/{codename}/'>LineageOS Wiki</a>",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )
        except Exception as e:
            await message.reply_text(f"❌ Error fetching device specifications: {e}")


__help__ = True

__mod_name__ = "Android"
__command_list__ = ["magisk", "twrp", "device"]
