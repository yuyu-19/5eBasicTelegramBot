import asyncio
import json
import os
import pickle

from DataClasses.userData import User
from DataClasses.campaignData import Campaign
# Split it into its own class to swap to SQL later, simple dicts will do for now

_users = {}
_campaigns = {}
_dbPath = ""
_userLock = asyncio.Lock()
_campaignLock = asyncio.Lock()
_nextAvailableCampaignID = 0
def initDB(dbPath=None):
    global _users
    global _campaigns
    global _dbPath
    if os.path.isfile(dbPath):
        data = pickle.load(open(dbPath, mode="rb"))
        _dbPath = dbPath
        _users = data["users"]
        _campaigns = data["campaigns"]
    else:
        _dbPath = os.path.join(os.getcwd(),"db.pickle")

async def addUser(newUser: User):
    if newUser.getUserID() in _users:
        raise Exception("User already exists!")
    else:
        async with _userLock:
            _users[newUser.getUserID()] = newUser
            saveToFile()

async def addCampaign(newCampaign: Campaign) -> int:
    async with _campaignLock:
        campaignID = len(_campaigns)    #This is actually O(1) complexity, so it's fine.
        newCampaign.setCampaignID(campaignID)
        _campaigns[str(campaignID)] = newCampaign
        saveToFile()
        return campaignID

async def addAlias(user: User, aliasID: str):
    aliasID = str(aliasID)
    async with _userLock:
        _users[aliasID] = user
        saveToFile()
def getUser(userID: str) -> User:
    userID = str(userID)
    if str(userID) in _users: #TODO: Possibility to sync across IDs?
        return _users[userID]
    else:
        raise ValueError("User does not exist!")

def getCampaign(campaignID: int) -> Campaign:
    campaignID = str(campaignID)
    if str(campaignID) in _campaigns:
        return _campaigns[campaignID]
    else:
        raise ValueError("Campaign not found!")
def saveToFile():
    dbDict = {"users": _users, "campaigns": _campaigns}
    pickle.dump(dbDict, open(_dbPath, mode="wb"))


async def updateUser(newUserVersion: User):
    async with _userLock:
        _users[str(newUserVersion.getUserID())] = newUserVersion
        saveToFile()

async def updateCampaign(newCampaignVersion: Campaign):
    async with _campaignLock:
        _campaigns[str(newCampaignVersion.getCampaignID())] = newCampaignVersion
        saveToFile()
