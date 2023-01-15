import math

import systemDataProvider
from messaging.userConversation import UserConversation

class CharacterSheet:
    def __init__(self, creatorID, displayName):
        self._creatorID = creatorID
        self._displayName:str = displayName
        self._stats:dict[str, dict[str, str|int]] = systemDataProvider.getDefaultStats()
        self._skills:dict[str, dict[str, str|int]] = systemDataProvider.getDefaultSkillDict()

        # This is a list of objects. Each object has a display_name and a description, and associated rolls.
        self._features:list[dict[str,str]] = list()
        # They're ordered based on when they were gained.
        self._maxHP = 0
        #TODO: ASK THE DM FOR THESE STATS
        self._speed = 0
        self._size = ""
        self._languagesKnown:list[str] = list()
        self._savingThrows:dict[str, dict[str, str|int]] = systemDataProvider.getDefaultSavingThrows()
    def getDisplayData(self):
        return {
            "creator_id":self._creatorID,
            "display_name":self._displayName
        }

    def getEffectiveStatValue(self, statID):
        return self._stats[statID]["value"] + self._stats[statID]["fixed_modifier"]

    def getStatModifier(self, statID):
        return math.floor(self.getEffectiveStatValue(statID)/2)-5

    def startUserConversation(self, userConvo: UserConversation):
        pass

async def createCharacterSheet(userConvo: UserConversation) -> CharacterSheet:
    creatorID = userConvo.getUserID()
    displayName = await userConvo.requestCustomInput("What is the character's name?")
    return CharacterSheet(creatorID, displayName)