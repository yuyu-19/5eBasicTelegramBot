#Loads the system-specific data from the given folder and provides helper methods.
import copy
import random

import jk_commentjson as json
import os

_defaultCharacterSheetData = {}
_classes = {}
_spells = {}
_spellsByLevel = {}
_spellsByClass = {}
_backgrounds = {}
_races = {}
def loadDefaultData(systemDataPath):
    global _defaultCharacterSheetData
    _defaultCharacterSheetData = json.load(open(os.path.join(systemDataPath, "sheetData.json")))
    #I won't check if all the skills reference an existing stat as I'm assuming valid system data.
    #TODO: Add other data, like items, spells, Monsters? etc.
    global _classes
    _classes = json.load(open(os.path.join(systemDataPath, "classes.json")))
    global _spells
    _spells = json.load(open(os.path.join(systemDataPath, "spells.json")))
    global _races
    _races = json.load(open(os.path.join(systemDataPath, "races.json")))
    global _backgrounds
    _backgrounds = json.load(open(os.path.join(systemDataPath, "backgrounds.json")))

    #TODO: Finish parsing with the scratch script

    # Now that we have the spell array, let's create a couple of internal indexes.
    # Specifically one to iterate over spells by levels and one over spells by class.
    for spellID, spellData in _spells.items():
        if str(spellData["spell_level"]) not in _spellsByLevel:
            _spellsByLevel[str(spellData["spell_level"])] = {}
        _spellsByLevel[str(spellData["spell_level"])][spellID] = spellData
        for castingClass in spellData["classes"]:

            if castingClass not in _spellsByClass:
                _spellsByClass[castingClass] = {}

            if str(spellData["spell_level"]) not in _spellsByClass[castingClass]:
                _spellsByClass[castingClass][str(spellData["spell_level"])] = {}

            _spellsByClass[castingClass][str(spellData["spell_level"])][spellID] = spellData




def getIDsByName(data: dict) -> dict:
    outputDict = dict()
    for key, item in data:
        outputDict[item["display_name"]] = key
    return outputDict
def getDefaultStats() -> dict:
    return copy.deepcopy(_defaultCharacterSheetData["stats"])
def getDefaultSavingThrows() -> dict:
    return copy.deepcopy(_defaultCharacterSheetData["saving_throws"])
def dictToListWithIDs(data:dict) -> list:
    outputList = list()
    for key,item in data.items():
        item["id"] = key
        outputList.append(item)
    return outputList
def getAllLanguages() -> list:
    return copy.deepcopy(_defaultCharacterSheetData["languages"])
def getDefaultSkillDict() -> dict:
    return copy.deepcopy(_defaultCharacterSheetData["skills"])

def getSkill(skillName) -> dict:
    return copy.deepcopy(_defaultCharacterSheetData["skills"][skillName])

def getBackgrounds() -> dict:
    return copy.deepcopy(_backgrounds)
def getBackground(backgroundID) -> dict:
    return copy.deepcopy(_backgrounds[backgroundID])
def getClass(classID) -> dict:
    return copy.deepcopy(_classes[classID])
def getClasses() -> dict:
    return copy.deepcopy(_classes)

def getSpells() -> dict:
    return copy.deepcopy(_spells)

def getSpell(spellID) -> dict:
    return copy.deepcopy(_spells[spellID])

def getSpellsByLevel(spellLevel) -> dict:
    return copy.deepcopy(_spellsByLevel[spellLevel])

def getSpellsByClass(castingClass) -> dict:
    return copy.deepcopy(_spellsByClass[castingClass])

def getSpellsByClassAndLevel(castingClass, spellLevel:int) -> dict:
    return copy.deepcopy(_spellsByClass[castingClass][str(spellLevel)])

def getClassLevelData(classID, level) -> dict:
    return copy.deepcopy(_classes[classID]["levels"][str(level)])
def getClassData(classID) -> dict:
    return copy.deepcopy(_classes[classID])

def getRaces() -> dict:
    return copy.deepcopy(_races)

def getRaceData(raceID: str) -> dict:
    return copy.deepcopy(_races[raceID])



"""
Sample stat:
TODO: REWORK STATS AND SKILLS SO THEY'RE LIKE THIS 
(without having the value/modifier/proficiency fields, those are added by characterSheet.py):
"STR" : {
	"display_name":"Strength",
	"value":0,
	"modifier":"-5"
}

Sample skill:
"animal_handling" : {
    "display_name":"Animal Handling",
    "linked_stat":"WIS",
    "value":0,
    "proficiency_multiplier": 0
}

Sample class:
"cleric": {
    "display_name":"Cleric",
    "hit_die": "d8",
    "saving_throws": ["Wisdom","Charisma"],
    "armor_proficiencies": ["light","medium","shields"],
    "proficiencies": ["light_armor","medium_armor","shields","simple_weapons"]
}

Sample spell:
"spell2": {
    "display_name": "blah blah",
    "spell_level":"1",

    "can_upcast": True/False,
    "damage_dice":"3d10",
    "damage_type":"psychic",
    
    "usable_classes":["wizard"],
    "cast_time": "1 reaction",
    "range": "5 ft.",
    "components": "S,V",
    "description": "something something roll 3d10 psychic damage"
}
"""

def rollFormula(formula):
    if "+" in formula:
        total = int(formula[formula.find("+") + 1:])
        formula = formula[:formula.find("+")]
    elif "-" in formula:
        total = int(formula[formula.find("-") + 1:])
        formula = formula[:formula.find("-")]
    else:
        total = 0
    if "d" in formula:
        if formula.find("d") == 0:
            dieNumber = 1
        else:
            dieNumber = int(formula[:formula.find("d")])
        dieSize = formula[formula.find("d")+1:]
    else:
        raise ValueError("Invalid roll formula, no die size specified")

    isAdvantage = False
    isDisadvantage = False
    keepDie = 0
    if "kh" in dieSize:
        keepDie = int(dieSize[dieSize.find("kh")+2:])
        dieSize = int(dieSize[:dieSize.find("kh")])
        isAdvantage = True
    elif "kl" in dieSize:
        keepDie = int(dieSize[dieSize.find("kl") + 2:])
        dieSize = int(dieSize[:dieSize.find("kl")])
        isDisadvantage = True
    else:
        dieSize = int(dieSize)

    if isAdvantage or isDisadvantage:
        rolls = []
        for i in range(dieNumber):
            rolls.append(random.randint(1, dieSize))
        rolls.sort(reverse=isAdvantage)
        for i in range(keepDie):
            total += rolls[i]
    else:
        for i in range(dieNumber):
            total += random.randint(1, dieSize)

    return total
