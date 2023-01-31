from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import systemDataProvider
from messaging.userConversation import UserConversation
from systemDataProvider import rollFormula




class GenericItem:
    @staticmethod
    async def genericItemFactory(userConvo: UserConversation, maxPrice=float("inf")) -> GenericItem:
        newItemData = await GenericItem.baseItemFactory(userConvo, maxPrice)

        if await userConvo.yesNo("Does the item have a roll associated with it?"):
            newItemData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))
            while await userConvo.yesNo("Would you like to add another roll?"):
                newItemData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))

        return GenericItem(newItemData)

    @staticmethod
    async def baseItemFactory(userConvo: UserConversation, maxPrice=float("inf")) -> dict[str, str | bool | list | int]:
        newItemData = dict()
        newItemData["price"] = await userConvo.requestNumber(
            "What is the item's price in gold? (1 silver = 0.1 gold, 1 copper = 0.001 gold)", 0,
            maxPrice)
        newItemData["display_name"] = await userConvo.requestCustomInput("What's the item's name?")
        newItemData["description"] = await userConvo.requestCustomInput("What's the item's description?")
        newItemData["weight"] = await userConvo.requestCustomInput("How much does the item weigh in pounds?")
        newItemData["associated_rolls"] = list()
        return newItemData

    @staticmethod
    async def askItemRollData(userConvo: UserConversation):
        rollData: dict[str, int | str | bool | list] = dict()
        rollData["base_roll"] = await userConvo.requestRollFormula("What is the roll formula?")

        rollData["stat_modifiers"] = list()
        if await userConvo.yesNo("Can you add a stat modifier to the roll?"):
            viableStats = systemDataProvider.getDefaultStats()
            chosenStatID = await userConvo.chooseFromDict(viableStats, "Which stat modifier are you able to add?")
            rollData["stat_modifiers"].append(chosenStatID)
            viableStats.pop(chosenStatID)
            while await userConvo.yesNo("Are you able to add a different modifier?") and len(
                    viableStats) >= 1:
                chosenStatID = await userConvo.chooseFromDict(viableStats, "Which stat?")
                viableStats.pop(chosenStatID)
                rollData["stat_modifiers"].append(chosenStatID)
        rollData["proficiency"] = await userConvo.yesNo("Do you add your proficiency to the roll?")

        rollData["display_name"] = rollData["base_roll"]
        if rollData["proficiency"]: rollData["display_name"] += "+PROF"
        if len(rollData["stat_modifiers"]) > 0:
            rollData["display_name"] += "+"
            for stat in rollData["stat_modifiers"]:
                rollData["display_name"] += stat + "/"
            rollData["display_name"] = rollData["display_name"][:len(rollData["display_name"]) - 1]
        return rollData

    def __init__(self, itemData: str|dict):
        self.type = "misc"

        if isinstance(itemData, str):
            itemData = {"display_name": itemData}

        self.price = itemData["price"] if "price" in itemData else 0.0
        self.display_name = itemData["display_name"]    #The item must always have a display name.
        self.description = itemData["description"] if "description" in itemData else ""
        self.weight = itemData["weight"] if "weight" in itemData else "0"
        self.associated_rolls:list = itemData["associated_rolls"] if "associated_rolls" in itemData else list()

    def __getitem__(self, item):
        if item == "display_name":
            return self.display_name
        else:
            raise ValueError

    def _get_display_data(self) -> str:
        outputString = self.display_name + "\n"

        if isinstance(self.description, float):
            self.description = ""

        outputString += self.description + "\n"
        outputString += "Weighs " + self.weight + " lbs \n"
        if len(self.associated_rolls) > 0:
            outputString += "Associated rolls: "
            for roll in self.associated_rolls:
                outputString += roll["display_name"] + "\n"
        return outputString

    def hasRolls(self) -> bool:
        return len(self.associated_rolls) > 0

    async def rollAssociated(self, userConvo: UserConversation, statModifiers:dict[str, int], proficiencyBonus:int):
        if len(self.associated_rolls) > 0:
            chosenRoll = await userConvo.chooseFromListOfDict(self.associated_rolls, "What would you like to roll?")
            result = rollFormula(chosenRoll["base_roll"])
            if chosenRoll["proficiency"]:
                result += proficiencyBonus
            if len(chosenRoll["stat_modifiers"]) > 0:
                chosenStatID = await userConvo.chooseFromListOfStrings(chosenRoll["stat_modifiers"], "Which stat modifier would you like to add?")
                result += statModifiers[chosenStatID]
            await userConvo.show("You rolled " + str(result))

    async def display_data(self, userConvo: UserConversation):
        await userConvo.show(self._get_display_data())

    async def requestEdit(self, userConvo: UserConversation):
        options = ["price","display_name","description","weight","associated_rolls"]
        userFinished = False
        while not userFinished:
            selectedOption = await userConvo.chooseFromListOfStrings(options, "Select which property to edit.")
            await userConvo.show(str(getattr(self, selectedOption)))
            if selectedOption != "associated_rolls":
                setattr(self, selectedOption, await userConvo.requestCustomInput("Please input the new value."))
            else:
                rollOptions = ["add","exit"]
                if len(self.associated_rolls) > 0:
                    rollOptions.insert(1,"remove")
                match await userConvo.chooseFromListOfStrings(rollOptions, "Please choose an option."):
                    case "add":
                        self.associated_rolls.append(await self.askItemRollData(userConvo))
                    case "remove":
                        self.associated_rolls.remove(await userConvo.chooseFromListOfDict(self.associated_rolls, "Choose which roll to remove."))
            userFinished = await userConvo.yesNo("Are you finished editing the item?")


    # "misc":[
    # {
    #   "type":"misc",
    #   "price": 0.34,
    #   "display_name": "",
    #   "description:"",
    #   "weight": "",
    #   IF MISC OR WEAPON
    #   "associated_rolls": [
        #   {
        #       "base_roll": "x",
        #       "stat_modifiers": ["str","dex"],
        #       "proficiency" : true
        #   }
    #   ]
    #   IF ARMOR
    #   "armor_type": "light",
    #   "base_AC": 14,
    #   "str_req": 4,
    #   "stealth_disad": false
    # }
    # ]
