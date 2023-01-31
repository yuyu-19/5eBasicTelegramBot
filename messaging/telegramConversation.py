import asyncio
import logging
import math
import random
from typing import Optional

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

import database
from DataClasses.userData import createUser, User
from messaging.userConversation import UserConversation
from systemDataProvider import rollFormula

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)



#The init function initializes and starts listening for messages.
events:dict[str, dict[str, Optional[str]|Optional[asyncio.Event]]] = dict()


def initProvider(token):
    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start, block=False)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), messageHandler, block=False)
    application.add_handler(echo_handler)
    application.add_handler(start_handler)

    application.run_polling()

async def waitForUserResponse(prompt:str, context: ContextTypes.DEFAULT_TYPE, telegramID: int | str) -> str:
    telegramID = str(telegramID)
    if prompt != "":
        await context.bot.send_message(chat_id=int(telegramID), text=prompt)
    events[telegramID]["event"] = asyncio.Event()
    await events[telegramID]["event"].wait()
    events[telegramID]["event"] = None
    return events[telegramID]["lastMessage"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userID = str(update.effective_chat.id)
    if userID in events:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Conversation already ongoing!")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Conversation started!")
        events[userID] = dict()
        events[userID]["event"] = None
        events[userID]["lastMessage"] = None
        await createAndStartConversation(context, userID)

async def messageHandler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userID = str(update.effective_chat.id)
    if userID in events:
        if userID in events and events[userID]["event"] is not None:
            events[str(update.effective_chat.id)]["lastMessage"] = update.message.text
            events[userID]["event"].set()
            print("Found waiting event, fired it.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please start a conversation with /start first!")


async def createAndStartConversation(context, telegramID:str):
    userID = "telegram:"+telegramID
    try:
        user = database.getUser(userID)
    except ValueError:
        await context.bot.send_message(chat_id=int(telegramID), text="You are a new user. Would you like to link to another account?")
        userInput = ""
        while userInput.lower() != "y" and userInput.lower() != "n":
            userInput = await waitForUserResponse("y/n\n", context, telegramID)
        if userInput == "y":
            existingUserID = await waitForUserResponse("Please input the userID of the account you'd like to link to.\n", context, telegramID)
            try:
                existingUser = database.getUser(existingUserID)
                await database.addAlias(existingUser, userID)
                user = existingUser
            except ValueError:
                await context.bot.send_message(chat_id=int(telegramID), text="This user does not exist! Exiting...")
                return
        else:
            userName = await waitForUserResponse("Which username would you like to use?\n", context, telegramID)
            user = await createUser(userID, userName)

    await context.bot.send_message(chat_id=int(telegramID), text="You are logged in as " + user.getUserName() + " (" + user.getUserID() + ")")
    userConvo = TelegramConversation(user, context, int(telegramID))
    await userConvo.userHandoff()
    events.pop(telegramID)

class TelegramConversation(UserConversation):
    def __init__(self, currentUser: User, context: ContextTypes.DEFAULT_TYPE, telegramID: int):
        super().__init__(currentUser)
        self._context = context
        self._telegramID = telegramID
    async def chooseFromListOfStrings(self, optionsAvailable: list, prompt: str) -> str:
        await self.show(prompt)
        if len(optionsAvailable) == 1:
            await self.show("Selecting the only option available: " + optionsAvailable[0])
            return optionsAvailable[0]

        for option in optionsAvailable:
            await self.show(str(optionsAvailable.index(option) + 1) + ") " + option[0].upper() + option[1:].replace("_", " "))
        return optionsAvailable[await self.requestInt("", numMin=1, numMax=len(optionsAvailable)) - 1]

    async def chooseFromListOfDict(self, optionsAvailable: list, prompt: str) -> dict:  # Returns one dict out of all of them
        await self.show(prompt)
        if len(optionsAvailable) == 1:
            await self.show("Selecting the only option available: " + optionsAvailable[0]["display_name"])
            return optionsAvailable[0]

        for choice in optionsAvailable:
            await self.show(str(optionsAvailable.index(choice) + 1) + ") " + choice["display_name"])
        return optionsAvailable[await self.requestInt("", numMin=1, numMax=len(optionsAvailable)) - 1]

    async def chooseFromDict(self, optionsAvailable: dict, prompt: str) -> str:  # Returns the key corresponding with the selected item
        await self.show(prompt)
        if len(optionsAvailable) == 1:
            for key in optionsAvailable:
                await self.show("Selecting the only option available: " + optionsAvailable[key]["display_name"])
                return key
        keyList = list(optionsAvailable.keys())
        for key in keyList:
            await self.show(str(keyList.index(key) + 1) + ") " + optionsAvailable[key]["display_name"])
        chosenIndex = await self.requestInt("", numMin=1, numMax=len(keyList)) - 1
        return keyList[chosenIndex]

    async def yesNo(self, prompt: str, trueOption: str = "Yes", falseOption: str = "No") -> bool:
        await self.show(prompt)
        while True:
            userInput = (await self.requestCustomInput(trueOption + " or " + falseOption + "?"))
            userInput = userInput.lower()
            if (trueOption.lower().find(userInput) == 0) ^ (falseOption.lower().find(userInput) == 0):
                return trueOption.lower().find(userInput) == 0

    async def requestInt(self, prompt: str, numMin: float = float("-inf"), numMax: float = float("inf")) -> int:
        while True:
            if numMax != float("inf") and numMin != float("-inf"):
                chosenNumber = await self.requestNumber(prompt, int(numMin), int(numMax))
            elif numMax != float("inf"):
                chosenNumber = await self.requestNumber(prompt, numMax=int(numMax))
            elif numMin != float("-inf"):
                chosenNumber = await self.requestNumber(prompt, numMin=int(numMin))
            else:
                chosenNumber = await self.requestNumber(prompt)
            if chosenNumber.is_integer():
                return int(chosenNumber)
            else:
                await self.show("Please specify an integer.")

    async def requestNumber(self, prompt: str, numMin: float = float("-inf"), numMax: float = float("inf")) -> float:
        await self.show(prompt)
        if numMax == numMin:
            await self.show("Selecting the only available option, " + str(numMin))
            return float(numMin)
        inf = float("inf")
        negInf = float("-inf")
        if numMax < inf and numMin > negInf:
            await self.show("Choose a number between " + str(numMin) + " and " + str(numMax) + " (inclusive)")
        elif numMax < inf:
            await self.show("Choose a number below " + str(numMax))
        elif numMin > negInf:
            await self.show("Choose a number above " + str(numMin))
        userInput = 0
        validNumber = False
        while not validNumber:
            try:
                userInput = await self.requestCustomInput("")
                if userInput == "r":  # TODO: Remove this, it's purely for testing.
                    return float(random.randint(math.ceil(numMin), math.floor(numMax)))
                else:
                    userInput = float(userInput)
                validNumber = True
                if not (numMin <= userInput <= numMax): validNumber = False
                if not validNumber:
                    await self.show("Number out of range.")
            except:
                await self.show("Not a valid number.")
        return userInput

    async def show(self, prompt: str) -> bool:
        if prompt != "":
            await self._context.bot.send_message(chat_id=self._telegramID, text=prompt)
        return False

    async def requestCustomInput(self, prompt: str) -> str:
        return await waitForUserResponse(prompt, self._context, self._telegramID)

    async def requestRollFormula(self, prompt: str) -> str:
        wellFormed = False
        userFormula = ""
        while not wellFormed:
            try:
                userFormula = await self.requestCustomInput(prompt)
                rollFormula(userFormula)
                wellFormed = True
            except:
                wellFormed = False
        return userFormula

