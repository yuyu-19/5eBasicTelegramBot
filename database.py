import json
from ObjectClasses.user import User
from ObjectClasses.campaign import Campaign
# Split it into its own class to swap to SQL later, simple dicts will do for now
class Database:
    def __init__(self, dbPath=None):
        if dbPath is not None:
            data = json.load(open(dbPath))
            self.__dbpath = dbPath
            self.__users = data["users"]
            self.__campaigns = data["campaigns"]
        else:
            self.__users = []
            self.__campaigns = []

    def addUser(self, newUser: User):
        if newUser.userID in self.__users:
            raise Exception("User already exists!")
        else:
            self.__users.append(newUser)

    def addCampaign(self, newCampaign: Campaign):
        if newCampaign.campaignID in self.__campaigns:
            raise Exception("Campaign already exists!")
        else:
            self.__users.append(newCampaign)

    def getUser(self, userID) -> User:
        if userID in self.__users:
            return self.__users[userID]
        else:
            raise Exception("User not found!")

    def getCampaign(self, campaignID) -> Campaign:
        if campaignID in self.__campaigns:
            return self.__campaigns[campaignID]
        else:
            raise Exception("Campaign not found!")

    def saveToFile(self):
        dbJSON = {"users": self.__users, "campaigns": self.__campaigns}
        json.dump(dbJSON, open(self.__dbpath))