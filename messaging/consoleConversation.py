import asyncio
import math
import random

import database
import systemDataProvider
from DataClasses.userData import createUser, User
from messaging.userConversation import UserConversation
from aioconsole import *

from systemDataProvider import rollFormula
#TODO:
# Sync users and prevent multiple conversations from the same user - done
# Create map WITH LOCK containing all current user conversations mapped by user - done

def inputLoop():
    userID = "console:" + input("Which userID would you like to be?\n") #UserIDs are in the format platform:ID to avoid overlap
    while True:
        line = input("Please type \"/start\" to begin a conversation.\n")
        command = line.strip()
        match command:
            case "/start" | "s":
                print("Start!")
                asyncio.run(createAndStartConversation(userID))

            case _:
                print("Invalid command.")

async def createAndStartConversation(userID):
    try:
        user = database.getUser(userID)
    except ValueError:
        await aprint("You are a new user. Would you like to link to another account?")
        userInput = ""
        while userInput.lower() != "y" and userInput.lower() != "n":
            userInput = await ainput("y/n\n")
        if userInput == "y":
            existingUserID = await ainput("Please input the userID of the account you'd like to link to.\n")
            try:
                existingUser = database.getUser(existingUserID)
                await database.addAlias(existingUser, userID)
                user = existingUser
            except ValueError:
                await aprint("This user does not exist! Exiting...")
                return
        else:
            userName = await ainput("Which username would you like to use?\n")
            user = await createUser(userID, userName)
    try:
        await registerUserConversation(user)    #This throws a ValueError if the user already has a conversation active!
    except ValueError:
        await aprint("User already has an active conversation! Try a different userID!")
        return
    await aprint("You are logged in as " + user.getUserName() + " (" + user.getUserID() + ")")
    userConvo = ConsoleConversation(user)
    await userConvo.userHandoff()
    await unregisterUserConversation(user)

class ConsoleConversation(UserConversation):
    async def chooseFromListOfStrings(self, optionsAvailable: list, prompt: str) -> str:
        await self.show(prompt)
        if len(optionsAvailable) == 1:
            await self.show("Selecting the only option available: " + optionsAvailable[0])
            return optionsAvailable[0]

        for option in optionsAvailable:
            await self.show(str(optionsAvailable.index(option)+1) + ") " + option[0].upper() + option[1:].replace("_"," "))
        return optionsAvailable[await self.requestInt("", numMin=1, numMax=len(optionsAvailable)) - 1]

    async def chooseFromListOfDict(self, optionsAvailable: list, prompt: str) -> dict: #Returns one dict out of all of them
        await self.show(prompt)
        if len(optionsAvailable) == 1:
            await self.show("Selecting the only option available: " + optionsAvailable[0]["display_name"])
            return optionsAvailable[0]

        for choice in optionsAvailable:
            await self.show(str(optionsAvailable.index(choice)+1) + ") " + choice["display_name"])
        return optionsAvailable[await self.requestInt("", numMin=1, numMax=len(optionsAvailable)) - 1]
    async def chooseFromDict(self, optionsAvailable: dict, prompt: str) -> str: #Returns the key corresponding with the selected item
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

    async def yesNo(self,prompt:str, trueOption:str="Yes", falseOption:str="No") -> bool:
        await self.show(prompt)
        while True:
            userInput = await self.requestCustomInput(trueOption + " or " + falseOption + "?")
            if (trueOption.lower().find(userInput.lower()) == 0) ^ (falseOption.lower().find(userInput.lower()) == 0):
                return trueOption.lower().find(userInput.lower()) == 0


    async def requestInt(self, prompt:str, numMin:float = float("-inf"), numMax:float = float("inf")) -> int:
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

    async def requestNumber(self, prompt:str, numMin:float = float("-inf"), numMax:float = float("inf")) -> float:
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
                if userInput == "r":    #TODO: Remove this, it's purely for testing.
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

    async def show(self,prompt:str) -> bool:
        await aprint(prompt)
        return False

    async def requestCustomInput(self,prompt:str) -> str:
        await self.show(prompt)
        return await ainput("")

    async def requestRollFormula(self,prompt:str) -> str:
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


_existingConversations: list[User] = list()
_conversationLock = asyncio.Lock()
async def registerUserConversation(user: User):
    async with _conversationLock:
        if user not in _existingConversations:
            _existingConversations.append(user)
        else:
            raise ValueError("User already has an ongoing conversation!")

async def unregisterUserConversation(user: User):
    async with _conversationLock:
        if user in _existingConversations:
            _existingConversations.remove(user)
        else:
            raise ValueError("User doesn't have an ongoing conversation!")