from __future__ import annotations
import math
from typing import Union

from DataClasses.armorItem import ArmorItem
from DataClasses.genericItem import GenericItem
from DataClasses.weaponItem import WeaponItem
from messaging.userConversation import UserConversation
import systemDataProvider
from systemDataProvider import *
from DataClasses.characterSheet import CharacterSheet

#This method parses a choice block and gets the user response(s).
async def _askChoiceBlock(userConvo: UserConversation, data, allowRoll=False, allowCustomInput=False) -> list[str]|list[dict]:
    userChoices = list()
    choiceName = data["display_name"]

    if "amount" in data:
        numberOfChoices = data["amount"]
    else:   #Assume user can only choose 1 option if no amount is listed
        numberOfChoices = 1

    if numberOfChoices > 0:
        await userConvo.show("Choosing a " + choiceName)

    #If the options are a list of strings, it will return a list of strings. If they are dicts, then it will return dicts.
    options:Union[list[str], list[dict]] = copy.deepcopy(data["options"])

    for i in range(numberOfChoices):
        choiceResult = ""
        if allowCustomInput:
            userCustomChoice = await userConvo.yesNo(
                "Would you like to input a custom value?")
            if userCustomChoice:
                choiceResult = await userConvo.requestCustomInput("Please input your custom value.")

        if allowRoll and choiceResult == "":  # Only if the user still hasn't picked anything
            userRollChoice = await userConvo.yesNo("Would you like to roll?")
            if userRollChoice:
                roll = rollFormula("1d" + str(len(data)))
                if isinstance(options, list):
                    choiceResult = options[roll]
                else:   #Must be a dict.
                    choiceResult = list(options.keys())[roll]
                    choiceResult = options[choiceResult]

                if isinstance(choiceResult, dict):
                    await userConvo.show("You rolled: " + choiceResult["display_name"])
                elif isinstance(choiceResult, str):
                    await userConvo.show("You rolled: " + choiceResult[0] + choiceResult[1:])

        if choiceResult == "":  # Only if the user still hasn't picked anything
            #Let's check if the options are strings or objects and act accordingly.
            if isinstance(options, dict):
                choiceResult = await userConvo.chooseFromDict(options, "Please select which item you'd like")
            elif isinstance(options, list):
                if isinstance(options[0], dict):
                    choiceResult = await userConvo.chooseFromListOfDict(options, "Please select which item you'd like")
                else:
                    choiceResult = await userConvo.chooseFromListOfStrings(options, "Please select which item you'd like")

            if isinstance(choiceResult, dict):
                await userConvo.show("Your selected " + choiceName + " is: " + choiceResult["display_name"])
            else:
                await userConvo.show("Your selected " + choiceName + " is: " + choiceResult[0] + choiceResult[1:])
        if isinstance(options, list):
            options.remove(choiceResult)
        elif isinstance(options, dict):
            options.pop(choiceResult)
        userChoices.append(choiceResult)

    return userChoices


async def requestItem(userConvo: UserConversation, maxPrice = float("inf")) -> GenericItem|WeaponItem|ArmorItem:
    itemTypes = ["armor", "weapon", "misc"]

    itemType = await userConvo.chooseFromListOfStrings(itemTypes,
                                                       "Which type of item would you like?")
    match itemType:
        case "misc":
            return await GenericItem.genericItemFactory(userConvo, maxPrice)
        case "armor":
            return await ArmorItem.armorFactory(userConvo, maxPrice)
        case "weapon":
            return await WeaponItem.weaponFactory(userConvo, maxPrice)

class PCSheet(CharacterSheet):

    @staticmethod
    async def PCSheetFactory(userConvo: UserConversation) -> PCSheet:  # TODO: Make this static to adhere to the factory method pattern.
        # <editor-fold desc="Race">
        allRaceData = getRaces()
        raceID = await userConvo.chooseFromDict(allRaceData, "Please choose a race.")
        raceData = allRaceData[raceID]

        newSheet = PCSheet(userConvo.getUserID(), await userConvo.requestCustomInput("Please input the character's name."))
        await newSheet._applyRaceData(userConvo, raceData["default"])
        if "subraces_choice" in raceData:
            if await userConvo.yesNo("Would you like to choose a subrace?"):
                subraceData = await _askChoiceBlock(userConvo, raceData["subraces_choice"])
                await newSheet._applyRaceData(userConvo, subraceData[0])
        # </editor-fold>

        # <editor-fold desc="Class">
        allClassData = getClasses()
        classID = await userConvo.chooseFromDict(allClassData, "Please choose a class.")
        chosenClassData = getClassData(classID)

        await newSheet._applyProficiencyChoiceBlock(userConvo, chosenClassData["proficiency_choices"])
        newSheet._hpDie = chosenClassData["hit_die"]
        newSheet._maxHP = int(chosenClassData["hit_die"][1:])

        if classID not in newSheet._allClassesLevelData:
            newSheet._allClassesLevelData[classID] = dict()
        newSheet._allClassesLevelData[classID]["levels"] = 1
        newSheet._allClassesLevelData[classID]["display_name"] = chosenClassData["display_name"]
        newSheet._allClassesLevelData[classID]["subclass_id"] = ""
        newSheet._allClassesLevelData[classID]["subclass_display_name"] = ""

        # <editor-fold desc="Class Equipment">
        usingStandardEquipment = await userConvo.yesNo("Would you like the starting equipment "
                                                       "for your class and background or to choose items manually with a random amount of gold?", "Standard equipment", "Buy items")
        if usingStandardEquipment:
            for key, value in chosenClassData["inventory"].items():
                match key:
                    # TODO: FIX UP GIVEN EQUIPMENT TO INCLUDE THESE DETAILS.
                    case "gold":
                        newSheet._inventory[key] += value
                    case "armor":
                        for item in value:
                            newSheet._inventory[key].append(ArmorItem(item))
                    case "misc":
                        for item in value:
                            newSheet._inventory[key].append(GenericItem(item))
                    case "weapon":
                        for item in value:
                            newSheet._inventory[key].append(WeaponItem(item))
        else:
            newSheet._inventory["gold"] = rollFormula(chosenClassData["starting_gold_roll"])
            await userConvo.show("You've been given " + str(newSheet._inventory["gold"]) + " gold instead of your equipment.")
            while True:
                await userConvo.show("You currently have " + str(newSheet._inventory["gold"]) + " gold left.")
                if not await userConvo.yesNo("Would you like to purchase another item?"):
                    break
                newItem = await requestItem(userConvo, newSheet._inventory["gold"])
                newSheet._inventory["gold"] -= newItem.price
                newSheet._inventory[newItem.type].append(newItem)

        # </editor-fold>

        # <editor-fold desc="Scores">
        if await userConvo.yesNo("Would you like to use the point buy variable rule?"):
            scoreMinimum = 8
            scoreMaximum = 15
            scoreCosts = [1, 1, 1, 1, 1, 2, 2]
            for statID, stat in newSheet._stats.items():
                stat["value"] = scoreMinimum
            pointsAvailable = 27

            while pointsAvailable > 0 or not await userConvo.yesNo("Are you finished changing the stats?"):
                await userConvo.show("You have " + str(pointsAvailable) + " points available.")
                if 0 < pointsAvailable < 27:
                    increaseStat = await userConvo.yesNo("Would you like to increase or decrease a stat?", "Increase", "Decrease")
                elif pointsAvailable == 0:
                    increaseStat = False
                else:
                    increaseStat = True

                if increaseStat:
                    statsWithScores = dict()
                    for statID, statData in newSheet._stats.items():
                        if not statData["value"] >= scoreMaximum and scoreCosts[statData["value"] - scoreMinimum] <= pointsAvailable:
                            # Stat must not exceed or match maximum also the cost must not be too high
                            statsWithScores[statID] = {"display_name": statData["display_name"] + " (" + str(statData["value"])
                                                                       + "->" + str(statData["value"] + 1) + ")" +
                                                                       " (-" + str(scoreCosts[statData["value"] - scoreMinimum]) + " points)"}

                    chosenStatID = await userConvo.chooseFromDict(statsWithScores, "Which stat would you like to increase?")
                    pointsAvailable -= scoreCosts[newSheet._stats[chosenStatID]["value"] - scoreMinimum]
                    newSheet._stats[chosenStatID]["value"] += 1
                else:
                    statsWithScores = dict()
                    for statID, statData in newSheet._stats.items():
                        if not statData["value"] <= scoreMinimum:
                            # Stat must not be below or match minimum
                            statsWithScores[statID] = \
                                {"display_name": statData["display_name"] + " (" + str(statData["value"])
                                                 + "->" + str(statData["value"] - 1) + ")" +
                                                 " (+" + str(scoreCosts[statData["value"] - scoreMinimum]) + " points)"}

                    chosenStatID = await userConvo.chooseFromDict(statsWithScores, "Which stat would you like to decrease?")
                    pointsAvailable += scoreCosts[newSheet._stats[chosenStatID]["value"] - scoreMinimum]
                    newSheet._stats[chosenStatID]["value"] -= 1
            await userConvo.show("Your current stats are:")
            for statID, statData in newSheet._stats.items():
                if statData["fixed_modifier"] != 0:
                    await userConvo.show(statData["display_name"] + ": " + str(statData["value"]) + "+" + str(statData["fixed_modifier"]))
                else:
                    await userConvo.show(statData["display_name"] + ": " + str(statData["value"]))


        else:
            if await userConvo.yesNo("Would you like to use the standard array or to roll for stats?", trueOption="Standard Array", falseOption="Roll"):
                scoreArray = ["15", "14", "13", "12", "10", "8"]
            else:
                scoreArray = []
                for i in range(len(newSheet._stats)):
                    scoreArray.append(str(rollFormula("4d6kh3")))

            await userConvo.show("You have the following stat scores available: " + str(scoreArray))
            for statID, stat in newSheet._stats.items():
                if stat["fixed_modifier"] != 0:
                    await userConvo.show("You have a " + str(stat["fixed_modifier"]) + " bonus to this stat.")
                stat["value"] = int(await userConvo.chooseFromListOfStrings(scoreArray, "Which score would you like to use for " + stat["display_name"]))
                scoreArray.remove(str(stat["value"]))
        # </editor-fold>

        # <editor-fold desc="Background">
        backgroundsData = getBackgrounds()
        customBackgroundChoice = await userConvo.yesNo("Would you like to create a custom background?")

        if not customBackgroundChoice:
            chosenBackgroundID = await userConvo.chooseFromDict(backgroundsData, "Please choose a premade background")

            chosenBackgroundData = backgroundsData[chosenBackgroundID]
            newSheet._fluff["background"] = chosenBackgroundData["display_name"]

            newSheet._applyProficiencyBlock(chosenBackgroundData["proficiency"])
            await newSheet._applyFluffChoiceBlock(userConvo, chosenBackgroundData["fluff_choices"])
            for key, data in newSheet._fluff.items():
                if data == "" and key != "speciality":
                    newSheet._fluff[key] = await userConvo.requestCustomInput("Please input the character's " + key)

            await newSheet._applyProficiencyChoiceBlock(userConvo, chosenBackgroundData["proficiency_choices"])

            availableLanguages = getAllLanguages()
            for language in newSheet._languagesKnown:
                availableLanguages.remove(language)
            for i in range(chosenBackgroundData["languages_available"]):
                chosenLanguage = await userConvo.chooseFromListOfStrings(availableLanguages, "Please choose a language:")
                newSheet._languagesKnown.append(chosenLanguage)
                availableLanguages.remove(chosenLanguage)
            if "features" in chosenBackgroundData:
                for feature in chosenBackgroundData["features"]:
                    newSheet._features.append(feature)
        else:
            newSheet._fluff["background"] = "custom"
            await userConvo.show("You have 2 languages or tool proficiencies available.")
            toolProficienciesAmount = await userConvo.requestInt("How many tool proficiencies would you like?", 0, 2)

            customProficiencyChoiceBlock = {
                "skill": {
                    "display_name": "Skill Proficiency",
                    "amount": 2,
                    "options": list(getDefaultSkillDict().keys())  # All skills can be picked from.
                },
                "tool": {
                    "display_name": "Tool Proficiency",
                    "amount": toolProficienciesAmount,
                    "options": []
                }
            }

            allToolsAvailable = set()  # We'll add all the tool proficiency options from existing backgrounds.
            allEquipmentAvailable = dict()
            for key, currentBackgroundData in backgroundsData.items():
                if "proficiency" in currentBackgroundData:
                    if "tool" in currentBackgroundData["proficiency"]:
                        allToolsAvailable = allToolsAvailable.union(currentBackgroundData["proficiency"]["tool"])
                if "proficiency_choices" in currentBackgroundData:
                    if "tool" in currentBackgroundData["proficiency_choices"]:
                        allToolsAvailable = allToolsAvailable.union(currentBackgroundData["proficiency_choices"]["tool"]["options"])
                if "inventory" in currentBackgroundData:
                    allEquipmentAvailable[key] = currentBackgroundData["inventory"]
            customProficiencyChoiceBlock["tool"]["options"] = list(allToolsAvailable)
            await newSheet._applyProficiencyChoiceBlock(userConvo, customProficiencyChoiceBlock)

            # Ask and apply custom fluff:
            newSheet._fluff["ideal"] = await userConvo.requestCustomInput("What is your ideal?")
            newSheet._fluff["personality_trait"] = await userConvo.requestCustomInput("What is your personality trait?")
            newSheet._fluff["bond"] = await userConvo.requestCustomInput("What is your bond?")
            newSheet._fluff["flaw"] = await userConvo.requestCustomInput("What is your flaw?")

            availableLanguages = getAllLanguages()
            for language in newSheet._languagesKnown:
                availableLanguages.remove(language)
            for i in range(2 - toolProficienciesAmount):
                chosenLanguage = await userConvo.chooseFromListOfStrings(availableLanguages, "Please choose a language:")
                newSheet._languagesKnown.append(chosenLanguage)
                availableLanguages.remove(chosenLanguage)

            if not usingStandardEquipment:
                chosenEquipmentBackground = await userConvo.chooseFromDict(allEquipmentAvailable, "Which background's equipment would you like?")
                chosenEquipment = allEquipmentAvailable[chosenEquipmentBackground]
                for key, value in chosenEquipment.items():
                    match key:
                        case "gold":
                            newSheet._inventory[key] += value
                        case "armor":
                            for item in value:
                                newSheet._inventory[key].append(ArmorItem(item))
                        case "misc":
                            for item in value:
                                newSheet._inventory[key].append(GenericItem(item))
                        case "weapon":
                            for item in value:
                                newSheet._inventory[key].append(WeaponItem(item))
        # </editor-fold>

        await newSheet.levelUp(userConvo, classID)
        return newSheet

    def __init__(self, creatorID, displayName):
        super().__init__(creatorID, displayName) #This initializes stats
        self._fluff:dict[str, str] = {
            "personality_trait": "",
            "ideal": "",
            "bond": "",
            "flaw" : "",
            "background" : "",
            "eye_color": "",
            "height":"",
            "age": "",
            "speciality": ""
        }
        self._hpDie:str = ""


        self._inventory: dict[str, list[GenericItem|WeaponItem|ArmorItem]|float] = dict()
        self._inventory["misc"]:list[GenericItem] = list()
        self._inventory["weapon"]: list[ArmorItem] = list()
        self._inventory["armor"]: list[WeaponItem] = list()
        self._inventory["gold"]:float = 0.0 #Since gold is the most commonly used item, everything else will scale around its value.

        self._race:str = ""

        #"misc":list[GenericItem]

        for skillID, skill in self._skills.items():
            skill["proficiency_multiplier"] = 0

        self._characterLevel = 0

        self._allClassesLevelData: dict[str, dict[str, list|int|dict[str, list[Spell]|int|str]]|str|int] = dict()
        #"fighter": {
        #   "levels": 1,
        #   "subclass_id": "",
        #   "subclass_display_name": "",
        #},
        # "wizard": {
        #   "levels": 2,
        #   "max_spell_level": 1
        #   "subclass_id": "evocation",
        #   "subclass_display_name": "Evocation Study",
        #   "spellcasting_data": {
        #           "0": {
        #                 "spells_known": list[Spell]
        #                 "spells_prepared": list[Spell]
        #                 "spells_always_prepared": list[Spell]
        #                 "spell_slot_max": 1
        #           },
        #           "1": {
        #                 "spells_known": list[Spell]
        #                 "spells_prepared": list[Spell]
        #                 "spells_always_prepared": list[Spell]
        #           }
        #     },
        # }

    async def _showSummary(self, userConvo:UserConversation):
        outputString = "Character: " + self.display_name
        outputString += "\n" + "Creator ID: " + self._creatorID
        outputString += "\n" + "Max HP: " + str(self._maxHP) + "+" + str(self.getStatModifier("con")*self._characterLevel)
        for feature in self._features:
            if feature["id"] == "dwarven_toughness":
                outputString += "+" + str(self._characterLevel)
        outputString += "\n" + "Proficiency bonus: " + str(self._proficiencyBonus)
        await userConvo.show(outputString)

        AC = 10 + self.getStatModifier("dex")
        equippedArmor = None
        for item in self._inventory["armor"]:
            if item.equipped:
                equippedArmor = item
                AC = item.calculateAC(self.getStatModifier("dex"))
        if equippedArmor is not None:
            await userConvo.show("AC: " + str(AC) + " - wearing " + equippedArmor["display_name"])
        else:
            await userConvo.show("AC: " + str(AC) + " - no armor equipped")
        await self._displaySpeed(userConvo)

        for classID, value in self._allClassesLevelData.items():
            await userConvo.show(str(value["levels"]) + " levels in " + value["display_name"])
            if "subclass_id" in value and value["subclass_id"] != "":
                await userConvo.show("Subclass: " + value["subclass_display_name"])
            if "spellcasting_data" in value:
                await userConvo.show("Cantrips known: " + str(len(self.getKnownSpellsByLevel(classID, maxLevel=0)["0"])))
                await userConvo.show("Maximum spell level: " + str(value["max_spell_level"]))
    async def _displaySpeed(self, userConvo: UserConversation):
        encumbered = False
        for item in self._inventory["armor"]:
            if item.equipped and item.armor_type == "heavy":
                encumbered = self.getEffectiveStatValue("str") < item.str_req
        if "dwarf" in self._race.lower():
            encumbered = False
        speedString = "Speed:\n"
        for key, value in self._speed.items():
            if int(value) > 0:
                speedString += key + " speed: " + str(value) + (" (-10 due to low STR score)" if encumbered else "") + "\n"
            elif key == "climbing" or key == "swimming":
                speedString += key + " speed: " + str(math.floor((self._speed["walking"] - (10 if encumbered else 0)) / 2)) + " (Half of walking speed)\n"
        await userConvo.show(speedString)
    async def startUserConversation(self, userConvo: UserConversation):
        userFinished = False
        rootOptions = ["stats","size","max_hp","display_name", "skills", "saving throws","language", "speed", "features", "character fluff", "proficiencies", "inventory", "level up"]
        for classID in self._allClassesLevelData:
            if "spellcasting_data" in self._allClassesLevelData[classID]:
                rootOptions.insert(4,"spells")
                break
        while not userFinished:
            await self._showSummary(userConvo)
            chosenOption = (await userConvo.chooseFromListOfStrings(rootOptions, "What would you like to view/edit/roll?")).lower()
            match chosenOption:
                case "stats":
                    await self._dialogStats(userConvo)
                case "skills":
                    await self._dialogSavesSkills(userConvo, True)
                case "saving throws":
                    await self._dialogSavesSkills(userConvo, False)
                case "features":
                    await self._dialogFeatures(userConvo)
                case "speed":
                    await self._dialogSpeed(userConvo)
                case "language":
                    await self._dialogLanguage(userConvo)
                case "size":
                    await userConvo.show("Current size category: " + self._size)
                    if await userConvo.yesNo("Would you like to change the size category?"):
                        self._size = await userConvo.requestCustomInput("Please input the new size category.")
                case "max_hp":
                    await userConvo.show("Current max HP: " + str(self._maxHP)+ "+" + str(self.getStatModifier("con")*self._characterLevel))
                    if await userConvo.yesNo("Would you like to change the max HP?"):
                        self._maxHP = await userConvo.requestInt("Please input the new max HP.")
                case "display_name":
                    await userConvo.show("Current display name: " + self.display_name)
                    if await userConvo.yesNo("Would you like to change the display name?"):
                        self.display_name = await userConvo.requestCustomInput("Please input the new display name.")
                case "character fluff":
                    outputString = ""
                    for key, value in self._fluff.items():
                        outputString += key[0].upper() + key[1:] + ": " + value + "\n"
                    await userConvo.show(outputString)
                    if await userConvo.yesNo("Would you like to edit one?"):
                        editeableOptions = list(self._fluff.keys())
                        editeableOptions.remove("background")
                        chosenFluffOption = (await userConvo.chooseFromListOfStrings(editeableOptions, "Please choose one.")).lower()
                        self._fluff[chosenFluffOption] = await userConvo.requestCustomInput("Please input the new value.")
                case "proficiencies":
                    await self._dialogProficiency(userConvo)
                case "inventory":
                    await self._dialogInventory(userConvo)
                case "spells":  #TODO: ADD VIEWING SPELLS AND ALSO ROLLING
                    await self._dialogSpells(userConvo)
                case "level up":
                    #This would be swapped to a choice for multiclassing, but since we're not supporting it, we don't.
                    if await userConvo.yesNo("Are you sure you'd like to level up? This cannot be undone."):
                        await self.levelUp(userConvo, list(self._allClassesLevelData.keys())[0])
            userFinished = await userConvo.yesNo("Finish editing and save?")

    #This function parses the given race data and applies its properties to the character
    async def _dialogInventory(self, userConvo:UserConversation):
        await self._dialogInventoryOrProficiency(userConvo, False)
    async def _dialogProficiency(self, userConvo:UserConversation):
        await self._dialogInventoryOrProficiency(userConvo, True)

    async def _dialogInventoryOrProficiency(self, userConvo:UserConversation, isProficiency):
        if isProficiency:
            await userConvo.show("Here are your current proficiencies:")
            identifier = "proficiency"
            propertyToEdit: dict[str, list | float] = self._proficiencies
        else:
            await userConvo.show("Here's your current inventory:")
            identifier = "item"
            propertyToEdit: dict[str, list[GenericItem] | float] = self._inventory

        for innerKey in propertyToEdit.keys():
            if innerKey != "gold":
                outputString = ""
                for singleObject in propertyToEdit[innerKey]:
                    if identifier == "item":
                        outputString += singleObject.display_name + ", "
                    else:
                        outputString += singleObject + ", "
                outputString = outputString[:len(outputString) - 2]
                await userConvo.show("\n" + innerKey[0].upper() + innerKey[1:] + ":" + "\n" + outputString)
        options = ["add", "remove", "exit"]

        if identifier == "item":
            options.insert(0, "view")
            options.insert(2, "edit")
            itemsWithAssociatedRolls = list()
            for itemType, items in self._inventory.items():
                if itemType != "gold":
                    for item in items:
                        if item.hasRolls():
                            itemsWithAssociatedRolls.append(item)

            if len(itemsWithAssociatedRolls) > 0:
                options.insert(2, "roll")

        match await userConvo.chooseFromListOfStrings(options, "Choose an option."):  # TODO: ADD ITEM EDITING, SPLIT THEM INTO THEIR OWN CLASS, AND EDIT GOLD.
            case "view":
                chosenType = await userConvo.chooseFromListOfStrings(list(propertyToEdit.keys()), "Please select which type of " + identifier + " would you like to view.")
                if chosenType == "gold":
                    await userConvo.show("You have " + str(propertyToEdit[chosenType]) + " gold.")
                else:
                    chosenItem = await userConvo.chooseFromListOfDict(propertyToEdit[chosenType], "Please choose a " + identifier + " to view.")
                    await chosenItem.display_data(userConvo)

                    if chosenType == "armor":
                        chosenArmor: ArmorItem = chosenItem
                        if await userConvo.yesNo("Would you like to " + ("unequip" if chosenArmor.equipped else "equip") + " this armor?"):
                            if not chosenArmor.equipped:
                                for item in self._inventory["armor"]:
                                    item.equipped = False
                                await userConvo.show("Your new AC is " + str(chosenArmor.calculateAC(self.getStatModifier("dex"))))
                            chosenArmor.equipped = not chosenArmor.equipped
            case "add":
                if identifier == "item":
                    newItem = await requestItem(userConvo)
                    propertyToEdit[newItem.type].append(newItem)
                else:
                    chosenType = await userConvo.chooseFromListOfStrings(list(propertyToEdit.keys()), "Please select which type of " + identifier + " would you like to add.")
                    propertyToEdit[chosenType].append(await userConvo.requestCustomInput("Please input the new " + identifier + " you'd like to add."))
            case "remove":
                chosenType = await userConvo.chooseFromListOfStrings(list(propertyToEdit.keys()), "Please select which type of " + identifier + " would you like to remove.")
                if identifier == "item":
                    chosenItem = await userConvo.chooseFromListOfDict(propertyToEdit[chosenType], "Please choose a " + identifier + " to remove.")
                    await chosenItem.display_data(userConvo)
                    if await userConvo.yesNo("Are you sure you'd like to remove this item?"):
                        propertyToEdit[chosenType].remove(chosenItem)
                else:
                    propertyToEdit[chosenType].remove(await userConvo.chooseFromListOfStrings(propertyToEdit[chosenType], "Please choose a " + identifier + " to remove."))
            case "edit":
                chosenType = await userConvo.chooseFromListOfStrings(list(propertyToEdit.keys()), "Please select which type of " + identifier + " would you like to remove.")
                chosenItem: GenericItem = await userConvo.chooseFromListOfDict(propertyToEdit[chosenType], "Please choose an item.")
                await chosenItem.display_data(userConvo)
                await chosenItem.requestEdit(userConvo)
            case "roll":
                chosenItem = await userConvo.chooseFromListOfDict(itemsWithAssociatedRolls, "Please choose an item.")
                await chosenItem.display_data(userConvo)
                statModifiers = dict()
                for statID in self._stats:
                    statModifiers[statID] = self.getStatModifier(statID)
                await chosenItem.rollAssociated(userConvo, statModifiers, self._proficiencyBonus)


    async def _dialogSpells(self, userConvo:UserConversation):
        spellCastingClassesIDs = list()
        for key, value in self._allClassesLevelData.items():
            if "spellcasting_data" in value:
                spellCastingClassesIDs.append(key)
        chosenClassID = await userConvo.chooseFromListOfStrings(spellCastingClassesIDs, "Choose a class.")

        await userConvo.show("Spell save DC: "+ str(8 + self.getStatModifier(getSpellcastingAbilityForClass(chosenClassID)) + self._proficiencyBonus))
        options = ["view", "change prepared spells", "exit"]
        if chosenClassID == "wizard":
            options.insert(2, "learn")

        tempList = [self.getAlwaysPreparedSpellsByLevel(chosenClassID), self.getNormalPreparedSpellsByLevel(chosenClassID)]
        spellsWithRollsByLevel = dict()
        allSpellsByLevel = tempList[0] | tempList[1]
        for spellDict in tempList:
            total = 0
            for key, value in spellDict.items():
                total += len(value)
            if total > 0:
                if tempList.index(spellDict) == 0:
                    await userConvo.show("Your always prepared spells are:")
                else:
                    await userConvo.show("Your prepared spells are:")
                for levelNumber, levelSpells in spellDict.items():
                    outputString = "\nSpell level " + levelNumber + "\n"
                    for spell in levelSpells:
                        outputString += spell.display_name + ", "
                        if spell.hasRolls():
                            if levelNumber not in spellsWithRollsByLevel:
                                spellsWithRollsByLevel[levelNumber] = list()
                            spellsWithRollsByLevel[levelNumber].append(spell)
                    outputString = outputString[:len(outputString) - 2]
                    await userConvo.show(outputString)
        if len(spellsWithRollsByLevel) > 0:
            options.insert(1,"roll")

        match await userConvo.chooseFromListOfStrings(options, "Choose an option."):
            case "view":
                chosenLevel = await userConvo.chooseFromListOfStrings(list(allSpellsByLevel.keys()), "What level spell would you view?")
                chosenSpell: Spell = await userConvo.chooseFromListOfDict(allSpellsByLevel[chosenLevel], "Choose a spell to view.")
                await chosenSpell.displayData(userConvo, self._characterLevel)
            case "learn":
                await self.chooseAndLearnSpell(chosenClassID, userConvo)
            case "roll":
                if await userConvo.yesNo("Would you like to roll a spell attack or make a roll from a spell?","Attack","Spell roll"):
                    await userConvo.show("You rolled: " + str(rollFormula("d20")) +"+"+ str(self._proficiencyBonus) +"+"+ str(self.getStatModifier(getSpellcastingAbilityForClass(chosenClassID))))
                else:
                    chosenLevel = await userConvo.chooseFromListOfStrings(list(spellsWithRollsByLevel.keys()), "What level spell would you like to roll dice for?")
                    chosenSpell: Spell = await userConvo.chooseFromListOfDict(spellsWithRollsByLevel[chosenLevel], "Choose a spell to roll dice for.")
                    await chosenSpell.rollSpell(userConvo, self._allClassesLevelData[chosenClassID]["max_spell_level"], self._characterLevel)
            case "change prepared spells":
                await self.prepareSpells(chosenClassID, userConvo)
    async def _applyRaceData(self, userConvo:UserConversation,raceData):
        # Let's add all the data from the main race.
        # Ability score modifiers
        if self._race != "":
            self._race += "("+raceData["display_name"]+")"
        else:
            self._race = raceData["display_name"]    #We take the default name.
        if "ability_score_modifiers" in raceData:
            for key, value in raceData["ability_score_modifiers"].items():
                self._stats[key]["fixed_modifier"] = value
        # Languages
        if "languages" in raceData:
            self._languagesKnown.extend(raceData["languages"])
        if "languages_available" in raceData:
            availableLanguages = getAllLanguages()
            for language in self._languagesKnown:
                availableLanguages.remove(language)
            for i in range(0, raceData["languages_available"]):
                chosenLanguage = await userConvo.chooseFromListOfStrings(availableLanguages, "Please select a language to learn.")
                self._languagesKnown.append(chosenLanguage)
                availableLanguages.remove(chosenLanguage)
        # Features
        if "features" in raceData:
            self._features.extend(raceData["features"])

        # Speed, Size
        if "speed" in raceData:
            for key, value in raceData["speed"].items():
                self._speed[key] = value
        if "size" in raceData:
            self._size = raceData["size"]
        # Proficiencies
        if "proficiency" in raceData:
            self._applyProficiencyBlock(raceData["proficiency"])

        if "proficiency_choices" in raceData:
            await self._applyProficiencyChoiceBlock(userConvo, raceData["proficiency_choices"])
    #This function parases the given choiceObject for all possible choices and writes to the given targetObject

    def _applyProficiencyBlock(self, proficiencyBlock):
        for proficiencyType, proficiencyData in proficiencyBlock.items():
            if proficiencyType == "skill":
                for skillID in proficiencyData:
                    self._skills[skillID]["proficiency_multiplier"] = 1
            elif proficiencyType == "saving_throw":
                for savingThrowID in proficiencyData:
                    self._savingThrows[savingThrowID]["proficiency_multiplier"] = 1
            else:
                self._proficiencies[proficiencyType].extend(proficiencyData)


    async def _applyFluffChoiceBlock(self, userConvo: UserConversation, fluffChoiceData):
        for key,data in fluffChoiceData.items():
            chosenFluff = await _askChoiceBlock(userConvo, data, False, False)
            self._fluff[key] = chosenFluff[0]
    async def _applyProficiencyChoiceBlock(self, userConvo:UserConversation, proficiencyChoiceData):
        for proficiencyType,choiceData in proficiencyChoiceData.items():
            #Remove things the character is already proficient in
            if proficiencyType == "skill":
                availableOptions = dict()
                for skillID in choiceData["options"]:
                    if self._skills[skillID]["proficiency_multiplier"] == 0:
                        availableOptions[skillID] = self._skills[skillID]
                choiceData["options"] = availableOptions
                chosenProficiencies = await _askChoiceBlock(userConvo, choiceData, False, False)
                for chosenProficiency in chosenProficiencies:
                    self._skills[chosenProficiency]["proficiency_multiplier"] = 1
            else:
                availableOptions = list()
                for proficiency in choiceData["options"]:
                    if proficiency not in self._proficiencies[proficiencyType]:
                        availableOptions.append(proficiency)
                choiceData["options"] = availableOptions
                chosenProficiencies = await _askChoiceBlock(userConvo, choiceData, False, False)
                self._proficiencies[proficiencyType].extend(chosenProficiencies)

    def setSkillProficiency(self, skillID):
        self._skills[skillID]["proficiency_multiplier"] = 1
    def setSkillExpertise(self, skillID):
        self._skills[skillID]["proficiency_multiplier"] = 2


    async def levelUp(self, userConvo: UserConversation, classID):
        # Remember to add HP roll or average, etc etc
        self._characterLevel += 1

        if classID not in self._allClassesLevelData:
            self._allClassesLevelData[classID] = dict()

        levelData = getClassLevelData(classID, self._characterLevel)
        selectedClassLevelData = self._allClassesLevelData[classID]
        selectedClassLevelData["levels"] += 1

        if "spell_slots" in levelData:
            if "spellcasting_data" not in selectedClassLevelData:
                selectedClassLevelData["spellcasting_data"] = dict()

            spellSlotArray = levelData["spell_slots"]
            for spellLevel in range(0, len(spellSlotArray)):
                if str(spellLevel) not in selectedClassLevelData["spellcasting_data"]:
                    selectedClassLevelData["spellcasting_data"][str(spellLevel)] = {
                        "spells_known": list(),
                        "spells_prepared": list(),
                        "spells_always_prepared": list()
                    }

                if spellLevel > 0:
                    selectedClassLevelData["spellcasting_data"][str(spellLevel)]["spell_slot_max"] = spellSlotArray[spellLevel-1]

            selectedClassLevelData["max_spell_level"] = len(spellSlotArray)
            if "cantrips_known" in levelData:
                while len(self.getKnownSpellsByLevel(classID, maxLevel=0)["0"]) < levelData["cantrips_known"]:
                    #Character has less cantrips available than he should.
                    await self.chooseCantrip(classID, userConvo)


            # If the user is leveling a spellcasting class, prepare additional spells according to level/stat changes.
            if classID == "wizard":  #Learns 2 spells per level
                for i in range(2):
                    await self.chooseAndLearnSpell(classID, userConvo)
            elif classID == "cleric": #Learns all spells
                spellcastingClassData = self._allClassesLevelData[classID]
                maxSpellLevel = spellcastingClassData["max_spell_level"]
                for spellID in getSpellsByClassAndLevel(classID, maxSpellLevel):
                    self.learnSpell(classID, spellID)
            await self.prepareSpells(classID, userConvo)

        if "features" in levelData:
            for feature in levelData["features"]:
                if feature["id"] == "asi":  #Changes the description to specify which stats were increased.
                    feature["description"] = await self.applyAbilityScoreImprovement(userConvo)
                self._features.append(feature)

        if "features_choices" in levelData:
            for choiceID, featureChoice in levelData["features_choices"].items():
                choiceResults = await _askChoiceBlock(userConvo, featureChoice)
                if choiceID == "subclass":
                    choiceResult = choiceResults[0]  #User cannot take multiple subclasses.
                    selectedClassLevelData["subclass_id"] = choiceResult["subclass_id"]
                    selectedClassLevelData["subclass_display_name"] = choiceResult["display_name"]
                for chosenFeature in choiceResults:
                    self._features.append(chosenFeature)

        if "features_subclass" in levelData:
            self._features.extend(levelData["features_subclass"][selectedClassLevelData["subclass_id"]])

        if self._characterLevel > 1:
            if await userConvo.yesNo("Would you like to take the average HP or roll?", trueOption="Average", falseOption="Roll"):
                self._maxHP += int(int(self._hpDie[1:])/2+1) #Take half and round up
            else:
                rollResult = rollFormula(self._hpDie)
                await userConvo.show("Rolled " + str(rollResult))
                self._maxHP += rollResult



        self._proficiencyBonus = math.floor((self._characterLevel - 1) / 4) + 2

    async def applyAbilityScoreImprovement(self, userConvo: UserConversation):
        await userConvo.show("Your current stats are:")
        for statID, statData in self._stats.items():
            if statData["fixed_modifier"] != 0:
                await userConvo.show(statData["display_name"] + ": " + str(statData["value"]) + "+" + str(statData["fixed_modifier"]))
            else:
                await userConvo.show(statData["display_name"] + ": " + str(statData["value"]))
        if await userConvo.yesNo("Would you like to increase your stats or select a feat?", trueOption = "stats", falseOption="feat"):
            await userConvo.show("Remember: you cannot increase a stat beyond 20 in this way.")
            finalDescription = ""
            oneStatByTwo = await userConvo.yesNo("Would you like to increase a stat by 2 or two stats by 1?", "One stat by 2", "Two stats by 1")
            validStats = dict()
            for statID, statData in self._stats.items():
                if statData["value"] + statData["fixed_modifier"] <= 18 if oneStatByTwo else 19:
                    validStats[statID] = statData

            for i in range(1 if oneStatByTwo else 2):
                chosenStatID = await userConvo.chooseFromDict(validStats, "Which stat would you like to increase?")
                if oneStatByTwo:
                    self._stats[chosenStatID]["value"] += 2
                    finalDescription = "Gain +2 in " + self._stats[chosenStatID]["display_name"]
                else:
                    self._stats[chosenStatID]["value"] += 1
                    if finalDescription == "":
                        finalDescription = "Gain +1 in " + self._stats[chosenStatID]["display_name"] + " "
                    else:
                        finalDescription += "and " + self._stats[chosenStatID]["display_name"]

                validStats.pop(chosenStatID)
        else:
            finalDescription = await userConvo.requestCustomInput("Please input the description of the feat.")
        return finalDescription

    async def chooseCantrip(self, classID, userConvo: UserConversation):    #Forces the user to choose a cantrip from those available.
        cantripsAvailable = getSpellsByClassAndLevel(classID, 0)
        for cantripKnown in self.getKnownSpellsByLevel(classID, maxLevel=0)["0"]:
            cantripsAvailable.pop(cantripKnown.id)
        cantripChosen = await userConvo.chooseFromDict(cantripsAvailable, "Which cantrip would you like to add to your list?")
        self._allClassesLevelData[classID]["spellcasting_data"]["0"]["spells_known"].append(getSpell(cantripChosen))

    async def chooseAndLearnSpell(self, classID, userConvo: UserConversation):
        spellcastingClassData = self._allClassesLevelData[classID]
        maxSpellLevel = spellcastingClassData["max_spell_level"]
        chosenSpellLevel = await userConvo.requestInt("From what level would you like to learn a spell from?", 1, maxSpellLevel)
        availableSpells = getSpellsByClassAndLevel(classID, chosenSpellLevel)

        if str(chosenSpellLevel) not in spellcastingClassData["spellcasting_data"]:
            spellcastingClassData["spellcasting_data"][str(chosenSpellLevel)] = {
                "spells_known": list(),
                "spells_prepared": list(),
                "spells_always_prepared": list()
            }

        for spell in self.getKnownSpellsByLevel(classID, chosenSpellLevel, chosenSpellLevel)[str(chosenSpellLevel)]:
            availableSpells.pop(spell.id) #Remove the ones the character already knows.

        if len(availableSpells) == 0:
            await userConvo.show("You already know all the spells you can currently learn!")
            return

        chosenSpell = await userConvo.chooseFromDict(availableSpells, "Which spell would you like to learn?")
        self.learnSpell(classID, chosenSpell)
    async def prepareSpells(self, classID, userConvo: UserConversation):
        spellcastingClassData:dict[str, int|str|dict[str,dict[str,list[Spell]]]] = self._allClassesLevelData[classID]
        match classID:
            case "cleric":
                maxPreparedSpells = max(1,self.getStatModifier("wis"))
                maxPreparedSpells += max(1,spellcastingClassData["levels"]) #To account for the very first level.
            case "wizard":
                maxPreparedSpells = max(1,self.getStatModifier("int"))
                maxPreparedSpells += max(1,spellcastingClassData["levels"])
            case _: #Do nothing.
                return
        maxSpellLevel = spellcastingClassData["max_spell_level"]
        numOfCurrentlyPreparedSpells = 0
        for spellLevel, spellLevelData in spellcastingClassData["spellcasting_data"].items():
            if int(spellLevel) > 0:
                numOfCurrentlyPreparedSpells += len(spellLevelData["spells_prepared"])

        doneChanging = False

        await userConvo.show("Your currently prepared leveled spells are:")
        for spellLevel, spellLevelData in self.getNormalPreparedSpellsByLevel(classID, minLevel=1).items():
            await userConvo.show("Level " + spellLevel + ":")
            outputString = ""
            for spellData in spellLevelData:
                outputString += spellData.display_name + ", "
            outputString = outputString[:len(outputString) - 2]
            await userConvo.show(outputString)

        if maxPreparedSpells - numOfCurrentlyPreparedSpells > 0:
            await userConvo.show("You can still prepare " + str(maxPreparedSpells - numOfCurrentlyPreparedSpells) + " spells.")
        while not doneChanging:
            chosenSpellLevel = await userConvo.requestInt("What spell level would you like to change?", 1, maxSpellLevel)
            preparedSpellsInLevel = len(self.getNormalPreparedSpellsByLevel(classID, chosenSpellLevel, chosenSpellLevel)[str(chosenSpellLevel)])
            nonPreparedSpellsInLevel = len(self.getNotPreparedSpellsByLevel(classID, chosenSpellLevel, chosenSpellLevel)[str(chosenSpellLevel)])
            prepareOrUnprepare = False
            if preparedSpellsInLevel > 0 and maxPreparedSpells-numOfCurrentlyPreparedSpells>0 and nonPreparedSpellsInLevel > 0:
                #We have both available slots and currently prepared spells.
                prepareOrUnprepare = await userConvo.yesNo("Would you like to prepare a spell or unprepare one?","Prepare","Unprepare")
            elif preparedSpellsInLevel > 0:
                prepareOrUnprepare = False
            elif maxPreparedSpells-numOfCurrentlyPreparedSpells > 0 and nonPreparedSpellsInLevel > 0:
                prepareOrUnprepare = True

            if prepareOrUnprepare:
                #User wants to prepare a spell of that level.
                spellsAvailable:list[Spell] = self.getNotPreparedSpellsByLevel(classID, chosenSpellLevel, chosenSpellLevel)[str(chosenSpellLevel)]

                chosenSpell = await userConvo.chooseFromListOfDict(spellsAvailable, "Which spell would you like to prepare?")
                spellcastingClassData["spellcasting_data"][str(chosenSpellLevel)]["spells_prepared"].append(chosenSpell) #It'll return a spell. Ignore the bitching.
                numOfCurrentlyPreparedSpells += 1
            else:
                # User wants to UN-prepare a spell of that level.
                spellsAvailable = self.getNormalPreparedSpellsByLevel(classID, chosenSpellLevel, chosenSpellLevel)[str(chosenSpellLevel)]
                chosenSpell = await userConvo.chooseFromListOfDict(spellsAvailable, "Which spell would you like to un-prepare?")
                spellcastingClassData["spellcasting_data"][str(chosenSpellLevel)]["spells_prepared"].remove(chosenSpell)
                numOfCurrentlyPreparedSpells -= 1

            await userConvo.show("Your currently prepared leveled spells are:")
            for spellLevel, spellLevelData in self.getNormalPreparedSpellsByLevel(classID, minLevel=1).items():
                await userConvo.show("Level " + spellLevel + ":")
                outputString = ""
                for spellData in spellLevelData:
                    outputString += spellData.display_name +", "
                outputString = outputString[:len(outputString)-2]
                await userConvo.show(outputString)

            if maxPreparedSpells-numOfCurrentlyPreparedSpells > 0:
                await userConvo.show("You can still prepare " + str(maxPreparedSpells-numOfCurrentlyPreparedSpells) + " spells.")
                if nonPreparedSpellsInLevel == 0:
                    await userConvo.show("But you don't know any more spells of this level!")
            doneChanging = await userConvo.yesNo("Are you finished making changes to your prepared spells?")
            # TODO: THIS DOESN'T PREPARE ALL SPELLS? ALSO IT CRASHES WHEN I SAY NO.


    def learnSpell(self, classID, spellID):
        spellData:Spell = systemDataProvider.getSpell(spellID)
        #Only learn it if you don't know it yet
        if spellData not in self._allClassesLevelData[classID]["spellcasting_data"][str(spellData.spell_level)]["spells_known"]:
            self._allClassesLevelData[classID]["spellcasting_data"][str(spellData.spell_level)]["spells_known"].append(spellData)

    def _getClassSpells(self, classID, minLevel=1, maxLevel=9, prepared=False, alwaysPrepared=False, notPrepared=False, allKnown=False):
        spellsByLevel:dict[str, list[Spell]] = dict()
        if self._allClassesLevelData[classID]["max_spell_level"] < maxLevel:
            maxLevel = self._allClassesLevelData[classID]["max_spell_level"]

        if notPrepared:  # We first fill it with all known spells, then remove them.
            allKnown = True

        for spellLevel, spellLevelData in self._allClassesLevelData[classID]["spellcasting_data"].items():
            if minLevel <= int(spellLevel) <= maxLevel:

                if spellLevel not in spellsByLevel:
                    spellsByLevel[spellLevel] = list()
                if allKnown:
                    for spellData in spellLevelData["spells_known"]:
                        spellsByLevel[spellLevel].append(spellData)
                else:
                    if prepared:
                        for spellData in spellLevelData["spells_prepared"]:
                            spellsByLevel[spellLevel].append(spellData)
                    if alwaysPrepared:
                        for spellData in spellLevelData["spells_always_prepared"]:
                            spellsByLevel[spellLevel].append(spellData)

                if notPrepared: #Remove the ones that are prepared.
                    for spellData in spellLevelData["spells_prepared"]:
                        spellsByLevel[spellLevel].remove(spellData)
                    for spellData in spellLevelData["spells_always_prepared"]:
                        spellsByLevel[spellLevel].remove(spellData)

        return spellsByLevel

    def getNormalPreparedSpellsByLevel(self, classID, minLevel=1, maxLevel=9) -> dict[str, list[Spell]]:
        return self._getClassSpells(classID, minLevel, maxLevel, prepared=True)
    def getAlwaysPreparedSpellsByLevel(self, classID, minLevel=1, maxLevel=9) -> dict[str, list[Spell]]:
        return self._getClassSpells(classID, minLevel, maxLevel, alwaysPrepared=True)
    def getKnownSpellsByLevel(self, classID, minLevel=0, maxLevel=9) -> dict[str, list[Spell]]:
        return self._getClassSpells(classID, minLevel, maxLevel, allKnown=True)
    def getNotPreparedSpellsByLevel(self, classID, minLevel=0, maxLevel=9) -> dict[str, list[Spell]]:
        return self._getClassSpells(classID, minLevel, maxLevel, notPrepared=True)