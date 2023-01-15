#This whole thing is necessary to fix an error due to circular imports.
#Since the circular imports are only necessary for type checking, it's not an issue.
from __future__ import annotations
from typing import TYPE_CHECKING

import database
from DataClasses import campaignData
from messaging.userConversation import *
from DataClasses.campaignData import Campaign

#TODO: USER MANAGES CREATION OF CAMPAIGNS AND SELECTION
# Control is then handed off to the campaign object
# Which then hands it off to the characterSheet
# etc.

#TODO:
#   Implement creation of the object for User, Campaign, ETC.



async def createUser(userID, userName) -> User:
    newUser = User(userID, userName)
    await database.addUser(newUser)
    return newUser
class User:
    def __init__(self,userID,userName):  #init a completely new user
        self._userID: str = userID
        self._userName: str = userName
        self._DMing: list[dict] = list()         #Contains the IDs and NAMES for all campaigns the player is DMing
        self._playing: list[dict] = list()      #Contains the IDs and NAMES for all campaigns the player is playing in
        #TODO: ADD TO DB!!!!!!!!!!!

    async def startConversation(self, userConvo: UserConversation):
        #This function is called to prompt the user to choose a campaign from which to pull data (or make a new one)
        exitConversation = False
        while not exitConversation:
            if len(self._playing) == 0 and len(self._DMing) == 0:
                chooseExisting = False
            else:
                chooseExisting = await userConvo.yesNo("Would you like to create/join a new campaign or select an existing one?", trueOption="Existing", falseOption="Create")

            if chooseExisting:
                if len(self._DMing) == 0:
                    isDMing = False
                elif len(self._playing) == 0:
                    isDMing = True
                else:
                    isDMing = await userConvo.yesNo("Would you like to select from the campaigns you DM or the ones you play in?",trueOption="DM", falseOption="Player")
                chosenCampaign = await userConvo.chooseFromListOfDict(self._DMing if isDMing else self._playing, "Which campaign?")
                await database.getCampaign(chosenCampaign["id"]).chooseCharacterSheet(userConvo)

            else: #Create a new one
                if await userConvo.yesNo("You have no active campaigns. Would you like to create one or join one?", trueOption="Create", falseOption="Join"):
                    newCampaign = await campaignData.createCampaign(userConvo)
                    self.addDMingCampaign(newCampaign)
                    await userConvo.show("Campaign created!")
                else:
                    #TODO: JOINING CAMPAIGNS
                    pass
                await database.updateUser(self)
            exitConversation = await userConvo.yesNo("Are you finished?")

        print("Session terminated. Use /start to begin a new one.")

    def getUserID(self) -> str:
        return self._userID

    def getUserName(self) -> str:
        return self._userName
    def addPlayingCampaign(self, newCampaign: Campaign) -> bool:
        self._playing.append(newCampaign.getCampaignIDAndName())
        return True

    def addDMingCampaign(self, newCampaign: Campaign) -> bool:
        self._DMing.append(newCampaign.getCampaignIDAndName())
        return True

