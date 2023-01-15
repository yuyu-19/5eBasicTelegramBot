import math
from typing import Union

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


class PCSheet(CharacterSheet):
    def __init__(self, creatorID, displayName):
        super().__init__(creatorID, displayName) #This initializes stats
        self._maxHPRaw:int = 0  #This is the max HP without the constitution bonus
        self._proficiencyValue:int = 0
        self._proficiencies:dict[str, list[str]] = {
            "tool": [],
            "weapon": [],
            "armor" : []
        }
        self._fluff:dict[str, str] = {
            "personality": "",
            "ideal": "",
            "bond": "",
            "flaw" : "",
            "background" : ""
        }
        self._hpDie:str = ""


        #This is a list of objects? With name and description.
        self._inventory: dict[str, list|float] = {
            "misc":[],
            "weapon":[],
            "armor":[],
            "gold": 0.0         #Since gold is the most commonly used item, everything else will scale around its value.
        }                       #1 silver is 1/10th, 1 copper is 1/100th, and so on.

        for skillID, skill in self._skills.items():
            skill["proficiency_multiplier"] = 0

        self._characterLevel = 0

        self._allClassesLevelData = {}
        #"fighter": {
        #   "levels": 1,
        #   "subclass_id": "",
        #   "subclass_name": "",
        #},
        # "wizard": {
        #   "levels": 2,
        #   "max_spell_level": 1
        #   "cantrips_known": 4
        #   "subclass_id": "evocation",
        #   "subclass_name": "Evocation Study",
        #   "spells_available": {
        #       "0": {
        #           "something_something" : {
        #               "display_name": "thing",
        #               "prepared": True
        #           }
        #       },
        #       "1": {
        #           "spell_slot_max": 3,
        #           "spell_id":{ "display_name": "stuff","prepared":false }
        #       }
        #   }     Each spell here only lists its ID and whether or not it's prepared.
        # },


    async def characterMancer(self, userConvo: UserConversation):
        # <editor-fold desc="Race">
        allRaceData = getRaces()
        raceID = await userConvo.chooseFromDict(allRaceData, "Please choose a race.")
        raceData = allRaceData[raceID]
        await self._applyRaceData(userConvo, raceData["default"])

        if await userConvo.yesNo("Would you like to choose a subrace?"):
            subraceData = await _askChoiceBlock(userConvo, raceData["subraces_choice"])
            await self._applyRaceData(userConvo, subraceData[0])
        # </editor-fold>


        # <editor-fold desc="Class">
        allClassData = getClasses()
        classID = await userConvo.chooseFromDict(allClassData, "Please choose a class.")
        chosenClassData = getClassData(classID)

        await self._applyProficiencyChoiceBlock(userConvo, chosenClassData["proficiency_choices"])
        self._hpDie = chosenClassData["hit_die"]
        self._maxHPRaw = int(chosenClassData["hit_die"][1:])

        if classID not in self._allClassesLevelData:
            self._allClassesLevelData[classID] = dict()
        self._allClassesLevelData[classID]["levels"] = 1
        self._allClassesLevelData[classID]["subclass_id"] = None
        self._allClassesLevelData[classID]["subclass_name"] = None


        # <editor-fold desc="Class Equipment">
        usingStandardEquipment = await userConvo.yesNo("Would you like the starting equipment "
                                                    "for your class and background or to choose items manually with a random amount of gold?","Standard equipment","Buy items")
        if usingStandardEquipment:
            for key,value in chosenClassData["inventory"].items():
                if key != "gold":
                    self._inventory[key].extend(value)
                else:
                    self._inventory[key] = value
        else:
            self._inventory["gold"] = rollFormula(chosenClassData["starting_gold_roll"])
            await userConvo.show("You've been given " + str(self._inventory["gold"]) + " gold instead of your equipment.")
            newItem = dict()
            itemTypes = ["armor","weapon","misc","done"]
            while True:
                await userConvo.show("You currently have " + str(self._inventory["gold"]) + " gold left.")
                if not await userConvo.yesNo("Would you like to purchase an item?"):
                    break

                itemType = await userConvo.chooseFromListOfStrings(itemTypes,
                                                            "Which type of item would you like?")
                newItem["price"] = await userConvo.requestNumber("What is the item's price in gold? (1 silver = 0.1 gold, 1 copper = 0.001 gold)", numMin=0, numMax=self._inventory["gold"])
                self._inventory["gold"] -= newItem["price"]

                newItem["display_name"] = await userConvo.requestCustomInput("What's the item's name?")
                newItem["weight"] = await userConvo.requestCustomInput("How much does the item weigh in pounds?")
                newItem["description"] = await userConvo.requestCustomInput("What's the item's description?")
                match itemType:
                    case "misc":
                        newItem["associated_rolls"] = list()
                        if await userConvo.yesNo("Does the item have a roll associated with it?"):
                            newItem["associated_rolls"].append(await userConvo.requestCustomInput("What is the roll formula?"))
                            while await userConvo.yesNo("Would you like to add another roll?"):
                                newItem["associated_rolls"].append(
                                    await userConvo.requestRollFormula("What is the roll formula?"))
                    case "weapon":
                        viableStats = systemDataProvider.getDefaultStats()
                        newItem["proficiency"] = await userConvo.yesNo("Are you proficient with the weapon?")
                        newItem["attack_stats"] = list()
                        chosenStatID = await userConvo.chooseFromDict(viableStats, "Which stat do you use to attack with this weapon?")
                        newItem["attack_stats"].append(chosenStatID)
                        viableStats.pop(chosenStatID)
                        while await userConvo.yesNo("Are you able to use a different stat to attack?") and len(viableStats) >= 1:
                            chosenStatID = await userConvo.chooseFromDict(viableStats, "Which stat?")
                            viableStats.pop(chosenStatID)
                            newItem["attack_stats"].append(chosenStatID)

                        if await userConvo.yesNo("Does the weapon have a modifier to hit?"):
                            newItem["attack_bonus"] = await userConvo.requestInt("What is it?")
                        else:
                            newItem["attack_bonus"] = 0
                        newItem["associated_rolls"] = list()

                        newItem["associated_rolls"].append(await userConvo.requestRollFormula("What is the weapon's damage roll?"))
                        while await userConvo.yesNo("Would you like to add another roll?"):
                            newItem["associated_rolls"].append(
                                await userConvo.requestRollFormula("What is the roll formula?"))

                    case "armor":
                        armorTypes = ["heavy","medium","light"]
                        newItem["armor_type"] = await userConvo.chooseFromListOfStrings(armorTypes, "What type of armor is it?")
                        newItem["AC"] = await userConvo.requestInt("What is it's base armor class?", numMin=0)
                        if await userConvo.yesNo("Does it have a strength requirement?"):
                            newItem["str_req"] = await userConvo.requestInt("What is it?")
                        newItem["stealth_disad"] = await userConvo.yesNo("Does it impose disadvantage on stealth checks?")



        # </editor-fold>





        # <editor-fold desc="Scores">
        if await userConvo.yesNo("Would you like to use the point buy variable rule?"):
            scoreMinimum = 8
            scoreMaximum = 15
            scoreCosts = [1,1,1,1,1,2,2]
            for statID, stat in self._stats.items():
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
                    for statID,statData in self._stats.items():
                        if not statData["value"] >= scoreMaximum and scoreCosts[statData["value"]-scoreMinimum] <= pointsAvailable:
                            # Stat must not exceed or match maximum also the cost must not be too high
                            statsWithScores[statID] = {"display_name":statData["display_name"]+" ("+str(statData["value"])
                                                +"->"+str(statData["value"]+1)+")" +
                                                " (-" +str(scoreCosts[statData["value"]-scoreMinimum])+" points)"}

                    chosenStatID = await userConvo.chooseFromDict(statsWithScores, "Which stat would you like to increase?")
                    pointsAvailable -= scoreCosts[self._stats[chosenStatID]["value"]-scoreMinimum]
                    self._stats[chosenStatID]["value"] += 1
                else:
                    statsWithScores = dict()
                    for statID, statData in self._stats.items():
                        if not statData["value"] <= scoreMinimum:
                            # Stat must not be below or match minimum
                            statsWithScores[statID] = \
                                {"display_name": statData["display_name"] + " (" + str(statData["value"])
                                + "->" + str(statData["value"] - 1) + ")" +
                                " (+" + str(scoreCosts[statData["value"] - scoreMinimum]) + " points)"}

                    chosenStatID = await userConvo.chooseFromDict(statsWithScores, "Which stat would you like to decrease?")
                    pointsAvailable += scoreCosts[self._stats[chosenStatID]["value"] - scoreMinimum]
                    self._stats[chosenStatID]["value"] -= 1
            await userConvo.show("Your current stats are:")
            for statID, statData in self._stats.items():
                if statData["fixed_modifier"] != 0:
                    await userConvo.show(statData["display_name"]+": " + str(statData["value"]) + "+" + str(statData["fixed_modifier"]))
                else:
                    await userConvo.show(statData["display_name"] + ": " + str(statData["value"]))


        else:
            if await userConvo.yesNo("Would you like to use the standard array or to roll for stats?", trueOption="Standard Array", falseOption="Roll"):
                scoreArray = ["15", "14", "13", "12", "10", "8"]
            else:
                scoreArray = []
                for i in range(len(self._stats)):
                    scoreArray.append(str(rollFormula("4d6kh3")))

            await userConvo.show("You have the following stat scores available: " + str(scoreArray))
            for statID, stat in self._stats.items():
                print(stat)
                if stat["fixed_modifier"] != 0:
                    await userConvo.show("You have a " + str(stat["fixed_modifier"]) + " bonus to this stat.")
                stat["value"] = int(await userConvo.chooseFromListOfStrings(scoreArray, "Which score would you like to use for " + stat["display_name"]))
                scoreArray.remove(str(stat["value"]))
        # </editor-fold>
        self._maxHP = self._maxHPRaw + self.getStatModifier("con")
        # <editor-fold desc="Background">
        backgroundsData = getBackgrounds()
        customBackgroundChoice = await userConvo.yesNo("Would you like to create a custom background?")

        if not customBackgroundChoice:
            chosenBackgroundID = await userConvo.chooseFromDict(backgroundsData, "Please choose a premade background")

            chosenBackgroundData = backgroundsData[chosenBackgroundID]
            self._fluff["background"] = chosenBackgroundID[0].upper() + chosenBackgroundID[1:]

            self._applyProficiencyBlock(chosenBackgroundData["proficiency"])
            await self._applyFluffChoiceBlock(userConvo, chosenBackgroundData["fluff_choices"])
            await self._applyProficiencyChoiceBlock(userConvo, chosenBackgroundData["proficiency_choices"])

            availableLanguages = getAllLanguages()
            for i in range(chosenBackgroundData["languages_available"]):
                chosenLanguage = await userConvo.chooseFromListOfStrings(availableLanguages, "Please choose a language:")
                self._languagesKnown.append(chosenLanguage)
                availableLanguages.remove(chosenLanguage)
        else:
            self._fluff["background"] = "custom"
            await userConvo.show("You have 2 languages or tool proficiencies available.")
            toolProficienciesAmount = await userConvo.requestInt("How many tool proficiencies would you like?", numMin=0, numMax=2)

            customProficiencyChoiceBlock = {
                "skill": {
                    "display_name": "Skill Proficiency",
                    "amount": 2,
                    "options": list(getDefaultSkillDict().keys())  #All skills can be picked from.
                },
                "tool": {
                  "display_name": "Tool Proficiency",
                  "amount": toolProficienciesAmount,
                  "options": []
                }
            }

            allToolsAvailable = set() #We'll add all the tool proficiency options from existing backgrounds.
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
            await self._applyProficiencyChoiceBlock(userConvo,customProficiencyChoiceBlock)

            #Ask and apply custom fluff:
            self._fluff["ideal"] = await userConvo.requestCustomInput("What is your ideal?")
            self._fluff["personality_trait"] = await userConvo.requestCustomInput("What is your personality trait?")
            self._fluff["bond"] = await userConvo.requestCustomInput("What is your bond?")
            self._fluff["flaw"] = await userConvo.requestCustomInput("What is your flaw?")

            availableLanguages = getAllLanguages()
            for i in range(2-toolProficienciesAmount):
                chosenLanguage = await userConvo.chooseFromListOfStrings(availableLanguages, "Please choose a language:")
                self._languagesKnown.append(chosenLanguage)
                availableLanguages.remove(chosenLanguage)

            if not usingStandardEquipment:
                chosenEquipmentBackground = await userConvo.chooseFromDict(allEquipmentAvailable, "Which background's equipment would you like?")
                chosenEquipment = allEquipmentAvailable[chosenEquipmentBackground]
                for key, value in chosenEquipment.items():
                    if key != "gold":
                        self._inventory[key].extend(value)
                    else:
                        self._inventory["gold"] += value
        # </editor-fold>

        await self.levelUp(userConvo, classID)

    async def startUserConversation(self, userConvo: UserConversation):
        #TODO: THIS
        await userConvo.show("HEY, WE DID IT")
        userFinished = False
        options = ["Stats", "Skills", "Saving throws", "Features", "Character fluff", "Proficiencies", "Inventory"]

        for classID in self._allClassesLevelData:
            if "spells_available" in self._allClassesLevelData[classID]:
                options.append("Spells")
        while not userFinished:
            chosenOption = (await userConvo.chooseFromListOfStrings(options, "What would you like to view/edit?")).lower()
            match chosenOption:
                case "stats":
                    for statID, stat in self._stats.items():
                        await userConvo.show(stat["display_name"] + " - " + str(stat["value"]))
                    while await userConvo.yesNo("Would you like to edit a stat?"):
                        chosenStatID = await userConvo.chooseFromDict(self._stats, "Which stat would you like to modify?")
                        self._stats[chosenStatID]["value"] = await userConvo.requestInt("What new value would you like to assign?",numMin=0)
                case "saving throws" | "skills":      #The format is identical.
                    if chosenOption == "skills":
                        identifier = "skill"
                        propertyToEdit = self._skills
                    else:
                        identifier = "saving throw"
                        propertyToEdit = self._savingThrows
                    for skillID, skill in propertyToEdit.items():
                        shownString = skill["display_name"] + " - "
                        shownString += str(self._stats[skill["linked_stat"]] + self._proficiencyValue * skill[
                            "proficiency_multiplier"])  #There's something wonky with type hints. TODO: Fix it?
                        if skill["proficiency_multiplier"] == 1:
                            shownString += " - Proficient"
                        elif skill["proficiency_multiplier"] == 2:
                            shownString += " - Expert"
                        await userConvo.show(shownString)

                    while await userConvo.yesNo("Would you like to edit a "+identifier+"'s proficiency level?"):
                        chosenSkillID = await userConvo.chooseFromDict(propertyToEdit,
                                                                       "Which "+identifier+" would you like to modify?")
                        options = list("none, proficient, expert")
                        chosenProficiencyLevel = await userConvo.chooseFromListOfStrings(options,
                                                                                         "What proficiency level would you like?")
                        propertyToEdit[chosenSkillID]["proficiency_multiplier"] = options.index(chosenProficiencyLevel)
                case "features":
                    if await userConvo.yesNo("Would you like to add a new feature or view/edit an existing one?", "Create new", "Choose existing"):
                        newFeature = dict()
                        newFeature["id"] = "custom_feature"
                        newFeature["display_name"] = await userConvo.requestCustomInput("Give it a name.")
                        newFeature["description"] = await userConvo.requestCustomInput("Give it a description.")
                        self._features.append(newFeature)
                    else:
                        chosenFeature = await userConvo.chooseFromListOfDict(self._features, "Select a feature.")
                        await userConvo.show(chosenFeature["display_name"])
                        await userConvo.show(chosenFeature["description"])
                        if await userConvo.yesNo("Would you like to modify it?"):
                            if await userConvo.yesNo("Would you like to delete it?"):
                                self._features.remove(chosenFeature)
                            else:
                                if await userConvo.yesNo("Would you like to edit its name or description?", "Name", "Description"):
                                    chosenFeature["display_name"] = await userConvo.requestCustomInput("Please input a new name.")
                                else:
                                    chosenFeature["description"] = await userConvo.requestCustomInput("Please input a new description.")
                case "character fluff":
                    fluffOptions = []
                    for key, value in self._fluff.items():
                        fluffOptions.append(key[0].upper() + key[1:] + "\n" + value)
                    fluffOptions = ["Personality","Ideal","Bond","Flaw"]
                    chosenFluffOption = await userConvo.chooseFromListOfStrings(fluffOptions, "Please choose one.")
                case "proficiencies":
                    pass
                case "inventory":
                    pass
                case "spells":
                    #TODO: Check which spellcasting class the user has and ask them which one if multiple.
                    pass
            userFinished = await userConvo.yesNo("Are you finished?")
        pass

    #This function parses the given race data and applies its properties to the character
    async def _applyRaceData(self, userConvo:UserConversation,raceData):
        # Let's add all the data from the main race.
        # Ability score modifiers

        if "ability_score_modifiers" in raceData:
            for key, value in raceData["ability_score_modifiers"].items():
                self._stats[key]["fixed_modifier"] = value
        # Languages
        if "languages" in raceData:
            self._languagesKnown.extend(raceData["languages"])
        # Features
        if "features" in raceData:
            self._features.extend(raceData["features"])

        # Speed, Size
        if "speed" in raceData:
            self._speed = raceData["speed"]
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
        if "spell_slots" in levelData:
            if "spells_available" not in selectedClassLevelData:
                selectedClassLevelData["spells_available"] = dict()

            spellSlotArray = levelData["spell_slots"]
            for spellLevel in range(0, len(spellSlotArray)):
                if str(spellLevel) not in selectedClassLevelData["spells_available"]:
                    selectedClassLevelData["spells_available"][str(spellLevel)] = dict()
                if spellLevel > 0:
                    selectedClassLevelData["spells_available"]["spell_slot_max"] = spellSlotArray[spellLevel-1]

            selectedClassLevelData["max_spell_level"] = len(spellSlotArray)

            selectedClassLevelData["cantrips_known"] = levelData["cantrips_known"]
            while len(selectedClassLevelData["spells_available"]["0"]) < levelData["cantrips_known"]:
                #Character has less cantrips available than he should.
                await self.chooseCantrip(classID, userConvo)


            # If the user is leveling a spellcasting class, prepare additional spells according to level/stat changes.
            await self.prepareSpells(classID, userConvo)
            if classID == "wizard":  #Learns 2 spells per level
                for i in range(2):
                    await self.chooseSpellToLearn(classID, userConvo)
            elif classID == "cleric": #Learns all spells
                spellcastingClassData = self._allClassesLevelData[classID]
                maxSpellLevel = spellcastingClassData["max_spell_level"]
                for spellID in getSpellsByClassAndLevel(classID, maxSpellLevel):
                    self.learnSpell(classID, spellID)


        if "features" in levelData:
            for feature in levelData["features"]:
                if feature["id"] == "asi":  #Changes the description to specify which stats were increased.
                    feature["description"] = await self.applyAbilityScoreImprovement(userConvo)
                self._features.append(feature)

        if "features_choices" in levelData:
            for choiceID, featureChoice in levelData["features_choices"]:
                choiceResults = await _askChoiceBlock(userConvo, featureChoice)
                if choiceID == "subclass":
                    choiceResult = choiceResults[0]  #User cannot take multiple subclasses.
                    selectedClassLevelData["subclass_id"] = choiceResult["subclass_id"]
                    selectedClassLevelData["subclass_name"] = choiceResult["display_name"]
                for chosenFeature in choiceResults:
                    self._features.append(chosenFeature)

        if "features_subclass" in levelData:
            self._features.extend(levelData["features_subclass"][selectedClassLevelData["subclass_id"]])

        if self._characterLevel > 1:
            if await userConvo.yesNo("Would you like to take the average HP or roll?", trueOption="Average", falseOption="Roll"):
                self._maxHPRaw += int(int(self._hpDie[1:])/2+1) #Take half and round up
            else:
                rollResult = await userConvo.requestRollFormula(self._hpDie)
                await userConvo.show("Rolled " + str(rollResult))
                self._maxHPRaw += rollResult
            self._maxHP = self._maxHPRaw + self.getStatModifier("con")*self._characterLevel



        self._proficiencyValue = math.floor((self._characterLevel - 1) / 4) + 2

    async def applyAbilityScoreImprovement(self, userConvo: UserConversation):
        await userConvo.show("Your current stats are:")
        for statID, statData in self._stats.items():
            if statData["fixed_modifier"] != 0:
                await userConvo.show(statData["display_name"] + ": " + str(statData["value"]) + "+" + str(statData["fixed_modifier"]))
            else:
                await userConvo.show(statData["display_name"] + ": " + str(statData["value"]))
        await userConvo.show("Remember: you cannot increase a stat beyond 20 in this way.")
        finalDescription = ""
        oneStatByTwo = await userConvo.yesNo("Would you like to increase a stat by 2 or two stats by 1?","One stat by 2", "Two stats by 1")
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

        return finalDescription

    async def chooseCantrip(self, classID, userConvo: UserConversation):    #Forces the user to choose a cantrip from those available.
        cantripsAvailable = getSpellsByClassAndLevel(classID, 0)    #TODO: SOMETHING IS WRONG HERE
        for cantripKnown in self._allClassesLevelData[classID]["spells_available"]["0"]:
            cantripsAvailable.pop(cantripKnown)
        cantripChosen = await userConvo.chooseFromDict(cantripsAvailable, "Which cantrip would you like to add to your list?")
        self._allClassesLevelData[classID]["spells_available"]["0"][cantripChosen] = {
            "display_name": cantripsAvailable[cantripChosen]["display_name"]
        }

    #TODO: THIS
    async def chooseSpellToLearn(self, classID, userConvo: UserConversation):
        spellcastingClassData = self._allClassesLevelData[classID]
        maxSpellLevel = spellcastingClassData["max_spell_level"]
        chosenSpellLevel = await userConvo.requestInt("From what level would you like to learn a spell from?", 1, maxSpellLevel)
        availableSpells = getSpellsByClassAndLevel(classID, chosenSpellLevel)
        for key in spellcastingClassData["spells_available"][str(chosenSpellLevel)]:
            availableSpells.pop(key) #Remove the ones the character already knows.

        chosenSpell = await userConvo.chooseFromDict(availableSpells, "Which spell would you like to learn?")
        self.learnSpell(classID, chosenSpell)
    async def prepareSpells(self, classID, userConvo: UserConversation):
        spellcastingClassData = self._allClassesLevelData[classID]
        match classID:
            case "cleric":
                maxPreparedSpells = max(1,self.getStatModifier("wis"))
                maxPreparedSpells += spellcastingClassData["levels"]
            case "wizard":
                maxPreparedSpells = max(1,self.getStatModifier("int"))
                maxPreparedSpells += spellcastingClassData["levels"]
            case _: #Do nothing.
                return
        maxSpellLevel = spellcastingClassData["max_spell_level"]
        currentlyPreparedSpells = 0
        for spellLevel, spellLevelData in spellcastingClassData["spells_available"].items():
            if int(spellLevel) > 0:
                for spellID, spellData in spellLevelData.items():
                    if spellData["prepared"]:
                        currentlyPreparedSpells += 1

        doneChanging = False
        while not doneChanging:
            await userConvo.show("Your currently prepared leveled spells are:")
            for spellLevel, spellLevelData in self.getPreparedSpells(classID, minLevel=1).items():
                await userConvo.show("Level " + spellLevel + ":")
                for spellID, spellData in spellLevelData:
                    await userConvo.show(spellData["display_name"])

            if maxPreparedSpells-currentlyPreparedSpells > 0:
                await userConvo.show("You can still prepare " + str(maxPreparedSpells-currentlyPreparedSpells) + " spells.")

            chosenSpellLevel = await userConvo.requestInt("What spell level would you like to change?", numMin=1, numMax=maxSpellLevel)
            preparedSpellsInLevel = 0

            for _ in self.getPreparedSpells(classID, chosenSpellLevel, chosenSpellLevel):
                preparedSpellsInLevel += 1

            prepareOrUnprepare = False
            if preparedSpellsInLevel > 0 and maxPreparedSpells-currentlyPreparedSpells>0:
                #We have both available slots and currently prepared spells.
                prepareOrUnprepare = await userConvo.yesNo("Would you like to prepare a spell or unprepare one?","Prepare","Unprepare")
            elif preparedSpellsInLevel > 0:
                prepareOrUnprepare = False
            elif maxPreparedSpells-currentlyPreparedSpells > 0:
                prepareOrUnprepare = True

            if prepareOrUnprepare:
                #User wants to prepare a spell of that level.
                spellsAvailable = self.getKnownSpells(classID, chosenSpellLevel, chosenSpellLevel)[chosenSpellLevel]
                for key in self.getPreparedSpells(classID, chosenSpellLevel, chosenSpellLevel)[str(chosenSpellLevel)]:
                    spellsAvailable.pop(key)        #Remove all already prepared spells

                chosenSpell = await userConvo.chooseFromDict(spellsAvailable, "Which spell would you like to prepare?")
                spellcastingClassData["spells_available"][chosenSpellLevel][chosenSpell]["prepared"] = True
                currentlyPreparedSpells += 1
            else:
                # User wants to UN-prepare a spell of that level.
                spellsAvailable = self.getPreparedSpells(classID, chosenSpellLevel, chosenSpellLevel)[chosenSpellLevel]
                chosenSpell = await userConvo.chooseFromDict(spellsAvailable, "Which spell would you like to un-prepare?")
                spellcastingClassData["spells_available"][str(chosenSpellLevel)][chosenSpell]["prepared"] = False
                currentlyPreparedSpells -= 1



            doneChanging = await userConvo.yesNo("Are you finished making changes?")


    def learnSpell(self, classID, spellID):
        spellData = systemDataProvider.getSpell(spellID)
        spellData["prepared"] = False
        #Only learn it if you don't know it yet
        if spellID not in self._allClassesLevelData[classID]["spells_available"][spellData["spell_level"]]:
            self._allClassesLevelData[classID]["spells_available"][spellData["spell_level"]][spellID] = spellData
    def getPreparedSpells(self, classID, minLevel=0, maxLevel=9) -> dict:
        knownSpellsByLevel = self.getKnownSpells(classID, minLevel, maxLevel)
        preparedSpellsByLevel = dict()
        for spellLevel, spellLevelData in knownSpellsByLevel:
            for spellID, spellData in spellLevelData:
                if spellData["prepared"]:
                    if spellLevel not in preparedSpellsByLevel:
                        preparedSpellsByLevel[spellLevel] = dict()
                    preparedSpellsByLevel[spellLevel][spellID] = spellData
        return preparedSpellsByLevel

    def getKnownSpells(self, classID, minLevel=0, maxLevel=9):
        knownSpellsByLevel = {}
        if self._allClassesLevelData[classID]["max_spell_level"] < maxLevel:
            maxLevel = self._allClassesLevelData[classID]["max_spell_level"]
        # {
        #   "0": {
        #       "spell_id" : {
        #           "display_name":"",
        #           "prepared": true/false
        #       }
        #   }
        # }

        for spellLevel, spellLevelData in self._allClassesLevelData[classID]["spells_available"].items():
            if minLevel <= int(spellLevel) <= maxLevel:
                for spellID, spellData in spellLevelData:
                    if spellLevel not in knownSpellsByLevel:
                        knownSpellsByLevel[spellLevel] = dict()
                    knownSpellsByLevel[spellLevel][spellID] = spellData
        return knownSpellsByLevel


async def createPCSheet(userConvo: UserConversation) -> PCSheet:
    creatorID = userConvo.getUserID()
    displayName = await userConvo.requestCustomInput("What is the character's name?")
    newSheet = PCSheet(creatorID, displayName)
    await newSheet.characterMancer(userConvo)   #Ask the player aaaaaaaaaaaaaaaaaaaall the necessary questions.
    return newSheet