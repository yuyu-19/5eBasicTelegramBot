#TODO: LITERALLY just make these with console input/output for now lol.
# No reason to already do it via telegram, this should be easier to debug.
from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio

if TYPE_CHECKING:
    from DataClasses.userData import User


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
class UserConversation:
    def __init__(self, User: User):
        self._user:User = User

    async def chooseFromListOfStrings(self, choicesAvailable: list[str], prompt:str) -> str:
        #TODO: CHANGE THIS SO IF IT'S A DICT IT TAKES THE DISPLAY_NAME
        pass

    async def chooseFromListOfDict(self, choicesAvailable: list, prompt: str) -> dict:
        #TODO: CHANGE THIS SO IF IT'S A DICT IT TAKES THE DISPLAY_NAME
        pass

    async def chooseFromDict(self, choicesAvailable: dict, prompt: str) -> str:
        #TODO: CHANGE THIS SO IF IT'S A DICT IT TAKES THE DISPLAY_NAME
        pass

    def getUserID(self):
        return self._user.getUserID()

    async def yesNo(self,prompt:str, trueOption:str="Yes", falseOption:str="No") -> bool:
        pass

    async def requestInt(self, prompt:str, numMax:float = float("inf"), numMin:float = float("-inf")) -> int:
        pass

    async def requestNumber(self, prompt:str, numMax:float = float("inf"), numMin:float = float("-inf")) -> float:
        pass

    async def show(self,prompt:str) -> bool:
        pass


    async def requestCustomInput(self,prompt:str) -> str:
        pass

    async def requestRollFormula(self,prompt:str) -> str:
        pass

    async def userHandoff(self) -> bool:
        #TODO: Fetches the user corresponding to the current userID from the database and passes control over to it.

        pass

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

