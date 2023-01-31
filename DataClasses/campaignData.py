from __future__ import annotations
from typing import TYPE_CHECKING

import database
from DataClasses import PlayerCharacterSheet, characterSheet
from DataClasses.PlayerCharacterSheet import PCSheet
from DataClasses.characterSheet import CharacterSheet
from DataClasses.monsterSheet import MonsterSheet
from messaging.userConversation import UserConversation

if TYPE_CHECKING:
    from DataClasses.userData import User
#TODO:
# Synchronize campaign updates (for characters) and place a lock on a character sheet to prevent simultaneous editing.
async def createCampaign(userConvo: UserConversation) -> Campaign:
    campaignName = await userConvo.requestCustomInput("What would you like to name your campaign?")
    newCampaign = Campaign(userConvo.getUserID(),campaignName)
    await database.addCampaign(newCampaign)
    return newCampaign
class Campaign:
    def __init__(self, creatorID, campaignName):
        self._campaignID = -1
        self._campaignName = campaignName
        self._DMs = [creatorID]         #DM IDs
        self._players = []                          #Player IDs
        self._PCdata:list[PCSheet] = list()      #PC sheet objects
        self._NPCdata:list[CharacterSheet] = list()         #NPC sheet objects (either PCSheet or MonsterSheet)

    def getCampaignID(self):
        return self._campaignID
    async def chooseCharacterSheet(self, userConvo: UserConversation):
        userID = userConvo.getUserID()
        isDM = userID in self._DMs
        accessibleCharacterSheets = self._getAccessibleCharacterSheets(userID)
        await userConvo.show("Campaign ID (use this to allow other players to join): " + str(self._campaignID))

        if len(accessibleCharacterSheets) == 0 or await userConvo.yesNo("Would you like to create a new character sheet or view an existing one?", trueOption="Create", falseOption="View"):
            if not isDM or await userConvo.yesNo("Would you like to create a PC-like NPC or a monster?", trueOption="PC-like", falseOption="Monster"):
                chosenCharacterSheet = await PCSheet.PCSheetFactory(userConvo)
                self._PCdata.append(chosenCharacterSheet)
                await database.updateCampaign(self)
            else:
                chosenCharacterSheet = await MonsterSheet.monsterSheetFactory(userConvo)
                self._NPCdata.append(chosenCharacterSheet)
                await database.updateCampaign(self)

        elif len(accessibleCharacterSheets) > 0:
            chosenCharacterSheet = await userConvo.chooseFromListOfDict(accessibleCharacterSheets, "Which character sheet would you like to view?")
        else:
            return
        await chosenCharacterSheet.startUserConversation(userConvo)
        await database.updateCampaign(self) #Update campaign data to save any edits the user made.

    def getCampaignIDAndName(self) -> dict:
        return {
            "id": self._campaignID,
            "display_name": self._campaignName
        }

    def setCampaignID(self, campaignID):
        self._campaignID = campaignID
    def _getNewCharacterID(self, NPC = False) -> int:
        # Get the next available character ID.
        # Reason why this is in campaignData rather than in database like with the campaignID is because characterIDs are not unique between campaigns.
        if NPC:
            return len(self._NPCdata)
        else:
            return len(self._PCdata)

    def getPlayerIDs(self) -> list[dict]:
        return self._players

    def getDMIDs(self) -> list[dict]:
        return self._DMs

    async def addPlayer(self, newPlayerID):
        self._players.append(newPlayerID)
        await database.updateCampaign(self)

    async def addDM(self, newDMID):
        self._DMs.append(newDMID)
        await database.updateCampaign(self)

    def _getAccessibleCharacterSheets(self, userID) -> list[CharacterSheet]:
        isDM = userID in self._DMs
        availableCharacterSheets = []
        if isDM:
            # Show all, including monsters
            availableCharacterSheets.extend(self._PCdata)
            availableCharacterSheets.extend(self._NPCdata)
        else:
            for PlayerSheet in self._PCdata:
                if PlayerSheet.getDisplayData()["creator_id"] == userID:
                    availableCharacterSheets.append(PlayerSheet)
            #Show only theirs.

        return availableCharacterSheets

