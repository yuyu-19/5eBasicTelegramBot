#TODO: LITERALLY just make these with console input/output for now lol.
# No reason to already do it via telegram, this should be easier to debug.
from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio

if TYPE_CHECKING:
    from DataClasses.userData import User


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
class UserConversation:
    def __init__(self, currentUser: User):
        self._user:currentUser = currentUser

    async def chooseFromListOfStrings(self, choicesAvailable: list[str], prompt:str) -> str:
        pass

    async def chooseFromListOfDict(self, choicesAvailable: list, prompt: str) -> dict:
        pass

    async def chooseFromDict(self, choicesAvailable: dict, prompt: str) -> str:
        pass

    def getUserID(self):
        return self._user.getUserID()

    async def yesNo(self,prompt:str, trueOption:str="Yes", falseOption:str="No") -> bool:
        pass

    async def requestInt(self, prompt:str, numMin:float = float("-inf"), numMax:float = float("inf")) -> int:
        pass

    async def requestNumber(self, prompt:str, numMin:float = float("-inf"), numMax:float = float("inf")) -> float:
        pass

    async def show(self,prompt:str) -> bool:
        pass


    async def requestCustomInput(self,prompt:str) -> str:
        pass

    async def requestRollFormula(self,prompt:str) -> str:
        pass

    async def userHandoff(self) -> bool:
        await self._user.startConversation(self)  # Hand control over to the userData class
        return True



