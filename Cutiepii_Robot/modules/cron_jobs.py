"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
import os
import shutil
import datetime
import subprocess
import asyncio

from time import sleep
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE

from Cutiepii_Robot import DATABASE_NAME, OWNER_ID, dispatcher, LOGGER, BACKUP_PASS
from Cutiepii_Robot.modules.helper_funcs.chat_status import owner_plus

@owner_plus
@cutiepii_cmd(command="backupdb")
async def backup_now(_: Update, ctx: CallbackContext):
    await cronjob.run(u)

@owner_plus
@cutiepii_cmd(command="stopjobs")
async def stop_jobs(update: Update, _: CallbackContext):
    LOGGER.debug(j.stop())
    update.effective_message.reply_text("Scheduler has been shut down")

@owner_plus
@cutiepii_cmd(command="startjobs")
async def start_jobs(update: Update, _: CallbackContext):
    LOGGER.debug(j.start())
    update.effective_message.reply_text("Scheduler started")

zip_pass = BACKUP_PASS

async def backup_db(context: CallbackContext):
    bot = context.bot
    bot_user = await bot.get_me()
    bot_username = bot_user.username
    
    tmpmsg = "⏳ <b>Performing database backup...</b>\n<i>Please wait, this might take a few moments.</i>"
    tmp = await bot.send_message(OWNER_ID, tmpmsg, parse_mode=ParseMode.HTML)
    datenow = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dbbkpname = "db_{}_{}.tar".format(bot_username, datenow)

    # Use absolute paths relative to project root
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "..", ".."))
    backups_dir = os.path.join(project_root, "backups")
    bkplocation = os.path.join(backups_dir, datenow)
    dbbkppath = os.path.join(bkplocation, dbbkpname)

    bkpcmd = "pg_dump {} --format=tar > {}".format(DATABASE_NAME, dbbkppath)

    if not os.path.exists(bkplocation):
        os.makedirs(bkplocation)
    LOGGER.info("performing db backup")
    loginfo = "db backup"
    term(bkpcmd, loginfo)
    if not os.path.exists(dbbkppath):
        await bot.send_message(OWNER_ID, "An error occurred during the db backup")
        await tmp.edit_text("Backup Failed!")
        await asyncio.sleep(8)
        await tmp.delete()
        return 
    else:
        LOGGER.info("copying config, and logs to backup location")
        logger_path = os.path.join(project_root, 'LOGGER.txt')
        config_path = os.path.join(project_root, 'Cutiepii_Robot/config.py')
        if os.path.exists(logger_path):
            LOGGER.debug("logs copied")
            shutil.copyfile(logger_path, os.path.join(bkplocation, 'LOGGER.txt'))
        if os.path.exists(config_path):
            LOGGER.debug("config copied")
            shutil.copyfile(config_path, os.path.join(bkplocation, 'config.py'))
        LOGGER.info("zipping the backup")
        zip_file_path = os.path.join(backups_dir, '{}.zip'.format(datenow))
        zip_success = False

        if zip_pass:
            zipcmd = "zip --password '{}' {} {}/*".format(zip_pass, bkplocation, bkplocation)
            zipinfo = "zipping db backup"
            LOGGER.info("zip started")
            term(zipcmd, zipinfo)
            if os.path.exists(zip_file_path):
                zip_success = True
                LOGGER.info("zip done using command line tool")

        if not zip_success:
            import zipfile
            LOGGER.info("Creating zip archive using Python's zipfile module")
            try:
                with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(bkplocation):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, bkplocation)
                            zipf.write(file_path, arcname)
                zip_success = True
                LOGGER.info("zip done using python zipfile module")
            except Exception as e:
                LOGGER.error(f"Failed to create zip archive via python zipfile: {e}")

        if zip_success and os.path.exists(zip_file_path):
            with open(zip_file_path, 'rb') as bkp:
                nm = "{} backup \n".format(bot_username) + datenow
                await bot.send_document(OWNER_ID,
                                document=bkp,
                                caption=nm,
                                read_timeout=20,
                                write_timeout=20
                                )
        else:
            await bot.send_message(OWNER_ID, "❌ Database backup failed: Could not create zip archive.")

        LOGGER.info("removing zipped files")
        if os.path.exists(bkplocation):
            shutil.rmtree(bkplocation)
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
        LOGGER.info("backup done")
        await tmp.edit_text(
            "✅ <b>Backup complete!</b>\n<i>The archive has been successfully generated and sent.</i>" if zip_success else "❌ <b>Backup Failed!</b>",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(5)
        await tmp.delete()

@owner_plus
@cutiepii_cmd(command="purgebackups")
async def del_bkp_fldr(update: Update, _: CallbackContext):
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "..", ".."))
    backups_dir = os.path.join(project_root, "backups")
    if os.path.exists(backups_dir):
        shutil.rmtree(backups_dir)
    update.effective_message.reply_text("'backups' directory has been purged!")

def term(cmd, info):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    stdout, stderr = process.communicate()
    stderr = stderr.decode()
    stdout = stdout.decode()
    if stdout:
        LOGGER.info(f"{info} successful!")
        LOGGER.info(f"{stdout}")
    if stderr:
        LOGGER.error(f"error while running {info}")
        LOGGER.info(f"{stderr}")

from Cutiepii_Robot import updater as u
# run the backup daliy at 1:00
twhen = datetime.datetime.strptime('01:00', '%H:%M').time()
j = u.job_queue
cronjob = j.run_daily(callback=backup_db, name="database backups", time=twhen)

