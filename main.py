import asyncio
import json
import logging
import commandHandlers
from telegram.ext import Updater, Dispatcher
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters

def registerHandlers(dispatcher: Dispatcher):

    echo_handler = MessageHandler(Filters.text & (~Filters.command), commandHandlers.messageHandler_echo)
    dispatcher.add_handler(echo_handler)

    # Register all commandHandlers listed in the file
    handlerPrefix = "commandHandler_"

    method_list = [func for func in dir(commandHandlers) if callable(getattr(commandHandlers, func)) and func.startswith(handlerPrefix)]
    for handlerName in method_list:
        dispatcher.add_handler(CommandHandler(handlerName[len(handlerPrefix):len(handlerName)], getattr(commandHandlers, handlerName)))


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



    updater = Updater(token=configData["token"], use_context=True)
    registerHandlers(updater.dispatcher)

    updater.start_polling()

