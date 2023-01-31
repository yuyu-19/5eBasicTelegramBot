from __future__ import annotations

import copy
from math import floor

from messaging.userConversation import UserConversation
import systemDataProvider


class Spell:
    def __init__(self, spellData, spellID, classes):
        self.id = spellID
        self.display_name = spellData["display_name"]
        self.spell_level:int = spellData["spell_level"]
        self.classes:list[str] = classes
        self.cast_time:str = spellData["cast_time"]
        self.range:str = spellData["range"]
        self.duration:str = spellData["duration"]
        self.description:str = spellData["description"]
        self.higher_levels_description:str = spellData["higher_levels_description"] if "higher_levels_description" in spellData else ""
        #self.upcasting_data = spellData["upcasting_data"]
        self.roll_data = spellData["roll_data"]

    def __getitem__(self, item):    #For the sake of backwards compatibility.
        if item == "display_name":
            return self.display_name
        else:
            raise ValueError

    async def displayData(self, userConvo: UserConversation, characterLevel):
        outputString = self.display_name
        outputString += "\nLevel: " + str(self.spell_level)
        outputString += "\nUseable by: " + str(self.classes)
        outputString += "\nCast time: " + self.cast_time
        outputString += "\nRange: " + self.range
        outputString += "\nDuration: " + self.duration
        outputString += "\n" + self.description
        if self.higher_levels_description != "":
            outputString += "\n" + self.higher_levels_description
        if len(self.roll_data) > 0:
            outputString += "\nAvailable rolls: "
            for roll in self.getRollDisplayData(characterLevel):
                 outputString += "\n" + roll["display_name"]
        await userConvo.show(outputString)

    def getRollDisplayData(self, characterLevel):
        rollData = copy.deepcopy(self.roll_data)
        for rollIndex, roll in enumerate(rollData):
            if "scaling_amount" in roll:
                rollData[rollIndex]["display_name"] = roll["base_roll"] + "(increases by " + roll["scaling_amount"] + " for every " + str(roll["additional_levels_required"]) + " levels of upcasting)"
            else:
                if "cantrip_damage_scaling" in roll:
                    rollLevel = "1"
                    for levelValue in roll["cantrip_damage_scaling"]:
                        if int(levelValue) <= characterLevel and int(levelValue) > int(rollLevel):
                            rollLevel = levelValue
                    if rollLevel != "1":  # Set the cantrip's base roll to be the higher level version.
                        rollData[rollIndex]["base_roll"] = roll["cantrip_damage_scaling"][rollLevel]
                rollData[rollIndex]["display_name"] = roll["base_roll"]
        return rollData

    def hasRolls(self) -> bool:
        return len(self.roll_data) > 0

    async def rollSpell(self, userConvo: UserConversation, maxSpellLevel:int=9, characterLevel=1):
        if len(self.roll_data) == 0:
            return
        rollData = self.getRollDisplayData(characterLevel)
        chosenRoll = await userConvo.chooseFromListOfDict(rollData, "Please choose what you'd like to roll.")
        outputRoll = systemDataProvider.rollFormula(chosenRoll["base_roll"])

        if "scaling_amount" in chosenRoll:
            levelDifference = await userConvo.requestInt("At what level would you like to cast it?", self.spell_level, maxSpellLevel) - self.spell_level
            for i in range(0,floor(levelDifference/chosenRoll["additional_levels_required"])):
                outputRoll += systemDataProvider.rollFormula(chosenRoll["scaling_amount"])
        await userConvo.show("You rolled " + str(outputRoll))