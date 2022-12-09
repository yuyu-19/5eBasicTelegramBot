import SystemDataProvider

class CharacterSheet:
    def __init__(self,userID):
        self.linkedUser = userID
        #self.stats = SystemDataProvider.getDefaultStatArray()
        self.DMs = []         #Contains the IDs for all campaigns the player is DMing
        self.players = []       #Contains the IDs for all campaigns the player is playing in
        self.PCdata = []           #PC sheets
        self.NPCdata = []          #NPC sheets

    def getPlayerFromSheet(self):
        return self.linkedUser

    def getDMIDs(self):
        return self.DMs

    def addPlayer(self, newPlayer: User) -> User:
        self.players.append(newPlayer.userID)

    def addDM(self, newDM: User):
        self.DMs.append(newDM.userID)

