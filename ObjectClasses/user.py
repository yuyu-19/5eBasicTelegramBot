#This whole thing is necessary to fix an error due to circular imports.
#Since the circular imports are only necessary for type checking, it's not an issue.
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ObjectClasses.campaign import Campaign

class User:
    def __init__(self,userID):
        self.userID = userID
        self.DMing = []         #Contains the IDs for all campaigns the player is DMing
        self.playing = []       #Contains the IDs for all campaigns the player is playing in


    def getPlayingCampaigns(self):
        return self.playing

    def getDMingCampaigns(self):
        return self.DMing

    def addPlayingCampaign(self, newCampaign: Campaign):
        self.playing.append(newCampaign.campaignID)

    def addDMingCampaign(self, newCampaign: Campaign):
        self.DMing.append(newCampaign.campaignID)

