"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

import os
import shutil
import datetime
import subprocess
import asyncio

from asyncio import sleep
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext

from Cutiepii_Robot import DATABASE_NAME, OWNER_ID, CUTIEPII_PTB, LOGGER, BACKUP_PASS
from Cutiepii_Robot.modules.helper_funcs.chat_status import owner_plus


@owner_plus
def backup_now(_: Update, _: CallbackContext):
    cronjob.run(CUTIEPII_PTB=CUTIEPII_PTB)


@owner_plus
async def stop_jobs(update: Update):
    LOGGER.debug(j.stop())
    await update.effective_message.reply_text("Scheduler has been shut down")


@owner_plus
async def start_jobs(update: Update):
    LOGGER.debug(j.start())
    await update.effective_message.reply_text("Scheduler started")


zip_pass = BACKUP_PASS


async def backup_db(_: CallbackContext):
    bot = CUTIEPII_PTB.bot
    tmpmsg = "Performing backup, Please wait..."
    tmp = await bot.send_message(OWNER_ID, tmpmsg)
    datenow = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dbbkpname = f"db_{bot.username}_{datenow}.tar"
    bkplocation = f"backups/{datenow}"
    bkpcmd = f"pg_dump {DATABASE_NAME} --format=tar > {bkplocation}/{dbbkpname}"

    if not os.path.exists(bkplocation):
        os.makedirs(bkplocation)
        LOGGER.info("performing db backup")
    loginfo = "db backup"
    term(bkpcmd, loginfo)
    if not os.path.exists(f'{bkplocation}/{dbbkpname}'):
        await bot.send_message(OWNER_ID,
                               "An error occurred during the db backup")
        tmp.edit_text("Backup Failed!")
        await sleep(8)
        tmp.delete()
        return
    LOGGER.info("copying config, and logs to backup location")
    if os.path.exists('log.txt'):
        LOGGER.debug("logs copied")
        shutil.copyfile('log.txt', f'{bkplocation}/log.txt')
    if os.path.exists('Cutiepii_Robot/config.py'):
        LOGGER.debug("config copied")
        shutil.copyfile('Cutiepii_Robot/config.py', f'{bkplocation}/config.py')
    LOGGER.info("zipping the backup")
    zipcmd = f"zip --password '{zip_pass}' {bkplocation} {bkplocation}/*"
    zipinfo = "zipping db backup"
    LOGGER.info("zip started")
    term(zipcmd, zipinfo)
    LOGGER.info("zip done")
    await sleep(1)
    with open(f'backups/{datenow}.zip', 'rb') as bkp:
        nm = f"{bot.username} backup \n" + datenow
        await bot.send_document(OWNER_ID, document=bkp, caption=nm, timeout=20)
    LOGGER.info("removing zipped files")
    shutil.rmtree(f"backups/{datenow}")
    LOGGER.info("backup done")
    tmp.edit_text("Backup complete!")
    await sleep(5)
    tmp.delete()


@owner_plus
async def del_bkp_fldr(update: Update):
    shutil.rmtree("backups")
    await update.effective_message.reply_text(
        "'backups' directory has been purged!")


def term(cmd, info):
    process = subprocess.Popen(cmd,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
    stdout, stderr = process.communicate()
    stderr = stderr.decode()
    if stdout := stdout.decode():
        LOGGER.info(f"{info} successful!")
        LOGGER.info(f"{stdout}")
    if stderr:
        LOGGER.error(f"error while running {info}")
        LOGGER.info(f"{stderr}")


# run the backup daliy at 1:00
twhen = datetime.datetime.strptime('01:00', '%H:%M').time()
j = CUTIEPII_PTB.job_queue
cronjob = j.run_daily(callback=backup_db, name="database backups", time=twhen)

CUTIEPII_PTB.add_handler(CommandHandler("backupdb", backup_now))
CUTIEPII_PTB.add_handler(CommandHandler("stopjobs", stop_jobs))
CUTIEPII_PTB.add_handler(CommandHandler("startjobs", start_jobs))
CUTIEPII_PTB.add_handler(CommandHandler("purgebackups", del_bkp_fldr))
