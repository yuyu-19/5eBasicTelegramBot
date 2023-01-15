from __future__ import annotations
from typing import TYPE_CHECKING

import database
from DataClasses import PlayerCharacterSheet, characterSheet
from DataClasses.PlayerCharacterSheet import PCSheet
from DataClasses.characterSheet import CharacterSheet
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
        self._NPCdata:list[CharacterSheet] = list()         #NPC sheet objects

    def getCampaignID(self):
        return self._campaignID
    async def chooseCharacterSheet(self, userConvo: UserConversation):
        userID = userConvo.getUserID()
        isDM = userID in self._DMs
        accessibleCharacterSheets = self._getVisibleCharacterSheets(userID)
        #TODO: CREATING A NEW CHARACTER SHEET, UPDATE THE CAMPAIGN DATA
        if len(accessibleCharacterSheets) == 0 or await userConvo.yesNo("Would you like to create a new character sheet or view an existing one?", trueOption="Create", falseOption="View"):
            if not isDM or await userConvo.yesNo("Would you like to create a PC-like NPC or a monster?", trueOption="PC-like", falseOption="Monster"):
                chosenCharacterSheet = await PlayerCharacterSheet.createPCSheet(userConvo)
                self._PCdata.append(chosenCharacterSheet)
                await database.updateCampaign(self)
            else:
                chosenCharacterSheet = await characterSheet.createCharacterSheet(userConvo)
                #TODO: Implement monster character sheets
                await database.updateCampaign(self)
                pass

        elif len(accessibleCharacterSheets) > 0:
            chosenCharacterSheet = await userConvo.chooseFromListOfDict(accessibleCharacterSheets, "Which character sheet would you like to view?")
        else:
            return
        await chosenCharacterSheet.startUserConversation(userConvo)

        #TODO: Show the user the chosenCharacterSheet

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

    def addPlayer(self, newPlayerID):
        self._players.append(newPlayerID)

    def addDM(self, newDMID):
        self._DMs.append(newDMID)

    def _getVisibleCharacterSheets(self, userID) -> list[CharacterSheet]:
        isDM = userID in self._DMs
        availableCharacterSheets = []
        if isDM:
            # Show all, including monsters
            availableCharacterSheets.extend(self._PCdata)
            availableCharacterSheets.extend(self._NPCdata)
        else:
            for PlayerSheet in self._PCdata:
                if PlayerSheet.getDisplayData()["ownerID"] == userID:
                    availableCharacterSheets.append(PlayerSheet)
            #Show only theirs.

        return availableCharacterSheets
        pass

