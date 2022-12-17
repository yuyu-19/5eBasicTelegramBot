import SystemDataProvider
from ObjectClasses.user import User


class CharacterSheet:
    def __init__(self,userID):
        #Remember that proficiency is (floor((character_level-1)/4)+2) for players
        self._creatorID = userID
        self._stats = SystemDataProvider.getDefaultStats()
        for statID,stat in self._stats:
            stat["value"] = 10

        self._savingThrows = SystemDataProvider.getDefaultStats()
        for statID,savingThrow in self._savingThrows:
            savingThrow["proficiency_multiplier"] = 0
        self.abilities = [] #Contains all abilities gained from the class/subclass

    def getLinkedUserID(self):
        return self._creatorID

    def setStat(self, statID, amount):
        self._stats[statID] = amount
        return



