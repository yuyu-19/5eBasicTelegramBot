from messaging.userConversation import UserConversation
from telegram import Update
from telegram.ext import CallbackContext
from DataClasses.userData import User
from telegram.ext import Updater, Dispatcher
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters




#The init function initializes and startrs listening for messages.
_updater = None
def initProvider(token):
    global _updater
    _updater = Updater(token, use_context=True)

    dispatcher = _updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), _messageHandler_echo))

    # Specific command handlers:
    dispatcher.add_handler(CommandHandler("start", _commandHandler_start))
    dispatcher.add_handler(CommandHandler("caps", _commandHandler_caps))

    _updater.start_polling()


def _messageHandler_echo(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

def _commandHandler_start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

def _commandHandler_caps(update: Update, context: CallbackContext):
    text_caps = ' '.join(context.args).upper()
    context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

class TelegramConversation(UserConversation):
    def __init__(self, userID):
        super().__init__(userID)

    def userChoice(self, choicesAvailable, prompt) -> str:
        _updater.dispatcher
        print(self._userID)
        #TODO: CHANGE THIS SO IF IT'S A DICT IT TAKES THE DISPLAY_NAME
        pass

    def yesNo(self,prompt:str, trueOption:str="Yes", falseOption:str="No") -> bool:
        pass

    def requestInt(self, prompt:str, maximum:float=float("inf"), minimum:float=-float("inf")) -> int:
        pass

    def show(self,prompt:str) -> None:
        pass


    def requestCustomInput(self,prompt:str) -> str:
        pass

    def requestRollFormula(self,prompt:str) -> str:
        pass

