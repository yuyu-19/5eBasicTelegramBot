#Loads the system-specific data from the given folder and provides helper methods.
import copy
import jk_commentjson as json
import os

_defaultCharacterSheet = {}
_classes = {}
_spells = {}
def loadDefaultData(systemDataPath):
    global _defaultCharacterSheet
    _defaultCharacterSheet = json.load(open(os.path.join(systemDataPath, "sheetData.json")))
    #I won't check if all the skills reference an existing stat as I'm assuming valid system data.
    #TODO: Add other data, like items, spells, Monsters? etc.
    #TODO: Use jsmin to remove comments.
    global _classes
    _classes = json.load(open(os.path.join(systemDataPath, "classes.json")))
    global _spells
    _spells = json.load(open(os.path.join(systemDataPath, "spells.json")))
    #Let's try and parse the spells to find damage dice and upcast potential.
    #TODO: Handle the above in preprocessing rather than on the fly. No reason to do it every time after all.
    #Better idea: Literally just use 5etools' existing dataset for spells.


def getDefaultStats():
    return copy.deepcopy(_defaultCharacterSheet.stats)
#
def getDefaultSkills():
    return copy.deepcopy(_defaultCharacterSheet.skills)
def getClass(className):
    return copy.deepcopy(_classes[className])
def getClasses():
    return copy.deepcopy(_classes)

def getSpells():
    return copy.deepcopy(_spells)

def getSpell(spellID):
    return copy.deepcopy(_spells[spellID])

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
