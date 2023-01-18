import math

from systemDataProvider import *
from messaging.userConversation import UserConversation

class CharacterSheet:
    def __init__(self, creatorID, displayName):
        self._creatorID = creatorID
        self.display_name:str = displayName
        self._stats:dict[str, dict[str, str|int]] = getDefaultStats()
        self._skills:dict[str, dict[str, str|int]] = getDefaultSkillDict()
        self._proficiencyValue: int = 0

        # This is a list of objects. Each object has a display_name and a description, and associated rolls.
        self._features:list[dict[str,str]] = list()
        # They're ordered based on when they were gained.
        self._maxHP = 0
        #TODO: ASK THE DM FOR THESE STATS
        self._speed = 0
        self._size = ""
        self._languagesKnown:list[str] = list()
        self._savingThrows:dict[str, dict[str, str|int]] = getDefaultSavingThrows()
    def __getitem__(self, key): #This is just to allow the object to be used for userConvo.chooseFromDict
        match key:
            case "display_name":
                return self.display_name
    def getDisplayData(self):
        return {
            "creator_id":self._creatorID,
            "display_name":self.display_name
        }

    def rollStat(self, statID: str) -> int:
        print(self.getStatModifier(statID))
        return rollFormula("d20")+self.getStatModifier(statID)
    def rollSkill(self, skillID):
        print(self._skills[skillID]["proficiency_multiplier"]*self._proficiencyValue+self.getStatModifier(self._skills[skillID]["linked_stat"]))
        return rollFormula("d20") +self._skills[skillID]["proficiency_multiplier"]*self._proficiencyValue+self.getStatModifier(self._skills[skillID]["linked_stat"])
    def rollSavingThrow(self, saveID):
        print( self._savingThrows[saveID]["proficiency_multiplier"] * self._proficiencyValue + self.getStatModifier(self._savingThrows[saveID]["linked_stat"]))
        return rollFormula("d20") + self._savingThrows[saveID]["proficiency_multiplier"] * self._proficiencyValue + self.getStatModifier(self._savingThrows[saveID]["linked_stat"])
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