from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ObjectClasses.user import User
class Campaign:
    def __init__(self,campaignID):
        self.campaignID = campaignID
        self.DMs = []         #DM IDs
        self.players = []       #Player IDs
        self.PCdata = []           #PC sheets
        self.NPCdata = []          #NPC sheets

    def getPlayerIDs(self):
        return self.players

    def getDMIDs(self):
        return self.DMs

    def addPlayer(self, newPlayer: User):
        self.players.append(newPlayer.userID)

    def addDM(self, newDM: User):
        self.DMs.append(newDM.userID)

