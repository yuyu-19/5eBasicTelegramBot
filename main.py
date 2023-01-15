import asyncio
import json
import logging
import os

#TODO: Isolate all telegram shit to its own class, so it can easily be swapped out for something else
#TODO: Update core database data only once the user is done inputting it (and just update it in general lmao)

#TODO: idea: create a messageHandler per every userID, putting them in a dict
#This way incoming messages can be redirected to the correct handler

from telegram.ext import Updater, Dispatcher
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

import systemDataProvider
import database
from messaging.consoleConversation import ConsoleConversation, inputLoop
from messaging.telegramConversation import TelegramConversation
import messaging.telegramConversation

if __name__ == '__main__':
    # Logging config
    with open("config.json") as f:
        configData = json.load(f)


    logLevel = logging.getLevelName(configData["logLevel"])
    if type(logLevel) != int:
        print("Invalid logLevel defined in config. Defaulting to ERROR.")
        logLevel = 40

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logLevel
    )

    aps_logger = logging.getLogger('apscheduler')
    aps_logger.setLevel(logging.WARNING)

    # Is there an existing database file? If so, load it
    databasePath = configData["databasePath"]
    if os.path.isfile(databasePath):
        database.initDB(databasePath)
    else:
        database.initDB(databasePath)

    systemDataPath = configData["systemDataPath"]
    systemDataProvider.loadDefaultData(systemDataPath)
    #messaging.telegramConversation.initProvider(configData["token"])
    print("Starting inputloop...")
    asyncio.run(messaging.consoleConversation.inputLoop(), debug=True)

