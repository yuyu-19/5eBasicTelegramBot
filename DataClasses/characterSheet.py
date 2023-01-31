import math

from systemDataProvider import *
from messaging.userConversation import UserConversation

class CharacterSheet:
    def __init__(self, creatorID, displayName):
        self._creatorID = creatorID
        self.display_name:str = displayName
        self._stats:dict[str, dict[str, str|int]] = getDefaultStats()
        self._skills:dict[str, dict[str, str|int]] = getDefaultSkillDict()
        self._proficiencyBonus: int = 0

        self._proficiencies: dict[str, list[str]] = {
            "tool": [],
            "weapon": [],
            "armor": []
        }

        # This is a list of objects. Each object has a display_name and a description, and associated rolls.
        self._features:list[dict[str,str]] = list()
        # They're ordered based on when they were gained.
        self._maxHP = 0

        self._speed:dict[str, int] = {
            "walking": 30,
            "burrowing": 0,
            "climbing": 0,
            "flying": 0,
            "swimming": 0
        }

        self._size = ""
        self._languagesKnown:list[str] = list()
        self._savingThrows:dict[str, dict[str, str|int]] = getDefaultSavingThrows()
    def __getitem__(self, key): #This is just to allow the object to be used for userConvo.chooseFromDict
        match key:
            case "display_name":
                return self.display_name
    def getDisplayData(self):
        return {
            "creator_id":self._creatorID,
            "display_name":self.display_name
        }

    async def _showSummary(self, userConvo:UserConversation):
        outputString = "Character: " + self.display_name
        outputString += "\n" + "Creator ID: " + self._creatorID
        outputString += "\n" + "Max HP: " + str(self._maxHP)
        outputString += "\n" + "Proficiency bonus: " + str(self._proficiencyBonus)
        await userConvo.show(outputString)
    async def _dialogSpeed(self, userConvo: UserConversation):
        await self._displaySpeed(userConvo)
        if await userConvo.yesNo("Would you like to edit your speeds?"):
            chosenSpeed = await userConvo.chooseFromListOfStrings(list(self._speed.keys()),"Which speed would you like to edit?")
            self._speed[chosenSpeed] = await userConvo.requestInt("Input a value.", 0)

    async def _dialogProficiency(self, userConvo: UserConversation):
        await userConvo.show("Here are your current proficiencies:")
        totalProficiencies = 0
        for innerKey in self._proficiencies.keys():
            outputString = ""
            totalProficiencies += len(self._proficiencies[innerKey])
            for proficiency in self._proficiencies[innerKey]:
                outputString += proficiency + ", "
            outputString = outputString[:len(outputString) - 2]
            await userConvo.show("\n" + innerKey[0].upper() + innerKey[1:] + ":" + "\n" + outputString)
        options = ["add", "exit"]
        if totalProficiencies > 0:
            options.insert(1,"remove")

        match await userConvo.chooseFromListOfStrings(options, "Choose an option."):
            case "add":
                chosenType = await userConvo.chooseFromListOfStrings(list(self._proficiencies.keys()), "Please select which type of proficiency would you like to add.")
                self._proficiencies[chosenType].append(await userConvo.requestCustomInput("Please input the new proficiency you'd like to add."))
            case "remove":
                chosenType = await userConvo.chooseFromListOfStrings(list(self._proficiencies.keys()), "Please select which type of proficiency would you like to remove.")
                self._proficiencies[chosenType].remove(await userConvo.chooseFromListOfStrings(self._proficiencies[chosenType], "Please choose a proficiency to remove."))
    async def _displaySpeed(self, userConvo: UserConversation):
        speedString = "Speed:\n"
        for key, value in self._speed.items():
            if value > 0:
                speedString += key + " speed: " + str(value) + "\n"
            elif key == "climbing" or key == "swimming":
                speedString += key + " speed: " + str(math.floor(self._speed["walking"] / 2)) + " (Half of walking speed)\n"
        await userConvo.show(speedString)
    async def _dialogStats(self, userConvo: UserConversation):
        for statID, stat in self._stats.items():
            await userConvo.show(stat["display_name"] + " - " + str(stat["value"]) + " (" +str(self.getStatModifier(statID))+")")
        match await userConvo.chooseFromListOfStrings(["edit", "roll", "exit"], "Choose an option."):
            case "edit":
                chosenStatID = await userConvo.chooseFromDict(self._stats, "Which stat would you like to modify?")
                self._stats[chosenStatID]["value"] = await userConvo.requestInt("What new value would you like to assign?", 0)
            case "roll":
                chosenStatID = await userConvo.chooseFromDict(self._stats, "Which stat would you like to roll?")
                await userConvo.show("You rolled " + str(self.rollStat(chosenStatID)))

    async def _dialogSavesSkills(self, userConvo: UserConversation, isSkill=True):
        if isSkill:
            identifier = "skill"
            propertyToEdit: dict[str, dict[str, str | int]] = self._skills
        else:
            identifier = "saving throw"
            propertyToEdit: dict[str, dict[str, str | int]] = self._savingThrows

        for propertyID, PROPERTY in propertyToEdit.items():
            shownString = PROPERTY["display_name"] + " (" + PROPERTY["linked_stat"] + ")" " - "
            shownString += str(self.getStatModifier(PROPERTY["linked_stat"]) + self._proficiencyBonus * PROPERTY[
                "proficiency_multiplier"])  # There's something wonky with type hints. TODO: Fix it?
            if PROPERTY["proficiency_multiplier"] == 1:
                shownString += " - Proficient"
            elif PROPERTY["proficiency_multiplier"] == 2:
                shownString += " - Expert"
            await userConvo.show(shownString)
        match await userConvo.chooseFromListOfStrings(["edit", "roll", "exit"], "Choose an option."):
            case "edit":
                chosenID = await userConvo.chooseFromDict(propertyToEdit, "Which " + identifier + " would you like to modify?")
                options = ["none", "proficient"]
                if identifier == "skill":
                    options.append("expert")
                chosenProficiencyLevel = await userConvo.chooseFromListOfStrings(options, "What proficiency level would you like?")
                propertyToEdit[chosenID]["proficiency_multiplier"] = options.index(chosenProficiencyLevel)
            case "roll":
                chosenID = await userConvo.chooseFromDict(propertyToEdit, "Which " + identifier + " would you like to roll?")
                if identifier == "skill":
                    await userConvo.show("You rolled " + str(self.rollSkill(chosenID)))
                else:
                    await userConvo.show("You rolled " + str(self.rollSavingThrow(chosenID)))

    async def _dialogFeatures(self, userConvo:UserConversation):
        await self._dialogFeatureLikeObject(userConvo, self._features, "feature")
    #This inner function is so I can re-use it for actions, and other objects that use the same structure as features.
    async def _dialogFeatureLikeObject(self, userConvo:UserConversation, listOfFeatureObjects, typeName):
        featuresWithRolls = list()
        await userConvo.show("Available "+typeName+":")
        for feature in listOfFeatureObjects:
            if "associated_rolls" in feature:
                await userConvo.show(feature["display_name"] +
                                     "\n" + feature["description"] +
                                     "\n" + "Associated rolls:" + str(feature["associated_rolls"]))
                featuresWithRolls.append(feature)
            else:
                await userConvo.show(feature["display_name"] +
                                     "\n" + feature["description"])

        options = ["add", "exit"]
        if len(self._features) > 0:
            options.insert(1,"edit")
            options.insert(2, "delete")
        if len(featuresWithRolls) > 0:
            options.insert(2, "roll")

        chosenFeatureOption = await userConvo.chooseFromListOfStrings(options, "Choose an option.")
        match chosenFeatureOption:
            case "add":
                listOfFeatureObjects.append(await self._requestFeatureOrAction(userConvo))
            case "delete" | "edit" | "roll":
                if chosenFeatureOption == "roll":
                    chosenFeature = await userConvo.chooseFromListOfDict(featuresWithRolls, "Select a "+typeName+".")
                else:
                    chosenFeature = await userConvo.chooseFromListOfDict(listOfFeatureObjects, "Select a "+typeName+".")
                await userConvo.show(chosenFeature["display_name"] + "\n" + chosenFeature["description"])

                match chosenFeatureOption:
                    case "delete":
                        if await userConvo.yesNo("Are you sure you'd like to delete this "+typeName+"?"):
                            listOfFeatureObjects.remove(chosenFeature)
                    case "edit":
                        if await userConvo.yesNo("Would you like to edit its name or description?", "Name", "Description"):
                            chosenFeature["display_name"] = await userConvo.requestCustomInput("Please input a new name.")
                        else:
                            chosenFeature["description"] = await userConvo.requestCustomInput("Please input a new description.")

                        if await userConvo.yesNo("Would you like to change its associated rolls?"):
                            rollOptions = ["add", "exit"]
                            if chosenFeature["associated_rolls"] > 0:
                                rollOptions.insert(1, "remove")
                            match await userConvo.chooseFromListOfStrings(rollOptions, "Please choose an option."):
                                case "add":
                                    chosenFeature["associated_rolls"].append(await userConvo.requestRollFormula("What is the roll formula?"))
                                case "remove":
                                    chosenFeature["associated_rolls"].remove(await userConvo.chooseFromListOfStrings(chosenFeature["associated_rolls"], "Choose which roll to remove."))

                    case "roll":
                        chosenRoll = await userConvo.chooseFromListOfStrings(chosenFeature["associated_rolls"], "Which value would you like to roll?")
                        await userConvo.show("You rolled " + str(rollFormula(chosenRoll)))

    async def _dialogLanguage(self, userConvo:UserConversation):
        outputString = ""
        for language in self._languagesKnown:
            outputString += language + ", "
        outputString = outputString[:len(outputString)-2]
        await userConvo.show("Languages known:\n" + outputString)
        options = ["add","exit"]
        if len(self._languagesKnown) > 0:
            options.insert(1,"remove")
        match await userConvo.chooseFromListOfStrings(options,"Choose an option."):
            case "add":
                availableLanguages = getAllLanguages()
                for language in self._languagesKnown:
                    availableLanguages.remove(language)
                chosenLanguage = await userConvo.chooseFromListOfStrings(availableLanguages, "Please choose a language:")
                self._languagesKnown.append(chosenLanguage)
            case "remove":
                chosenLanguage = await userConvo.chooseFromListOfStrings(self._languagesKnown, "Please choose a language:")
                self._languagesKnown.remove(chosenLanguage)

    @staticmethod
    async def _requestFeatureOrAction(userConvo: UserConversation) -> dict:
        newFeature = dict()
        newFeature["id"] = "custom_feature"
        newFeature["display_name"] = await userConvo.requestCustomInput("Give it a name.")
        newFeature["description"] = await userConvo.requestCustomInput("Give it a description.")

        if await userConvo.yesNo("Does it  have a roll associated with it?"):
            newFeature["associated_rolls"] = list()
            newFeature["associated_rolls"].append(await userConvo.requestRollFormula("What is the roll formula?"))
            while await userConvo.yesNo("Would you like to add another roll?"):
                newFeature["associated_rolls"].append(
                    await userConvo.requestRollFormula("What is the roll formula?"))
        return newFeature
    def rollStat(self, statID: str) -> int:
        #print(self.getStatModifier(statID))
        return rollFormula("d20")+self.getStatModifier(statID)
    def rollSkill(self, skillID):
        #print(self._skills[skillID]["proficiency_multiplier"]*self._proficiencyValue+self.getStatModifier(self._skills[skillID]["linked_stat"]))
        return rollFormula("d20") +self._skills[skillID]["proficiency_multiplier"]*self._proficiencyBonus+self.getStatModifier(self._skills[skillID]["linked_stat"])
    def rollSavingThrow(self, saveID):
        #print( self._savingThrows[saveID]["proficiency_multiplier"] * self._proficiencyValue + self.getStatModifier(self._savingThrows[saveID]["linked_stat"]))
        return rollFormula("d20") + self._savingThrows[saveID]["proficiency_multiplier"] * self._proficiencyBonus + self.getStatModifier(self._savingThrows[saveID]["linked_stat"])
    def getEffectiveStatValue(self, statID):
        return self._stats[statID]["value"] + self._stats[statID]["fixed_modifier"]

    def getStatModifier(self, statID):
        return math.floor(self.getEffectiveStatValue(statID)/2)-5

    def startUserConversation(self, userConvo: UserConversation):
        pass

async def createCharacterSheet(userConvo: UserConversation) -> CharacterSheet:
    creatorID = userConvo.getUserID()
    displayName = await userConvo.requestCustomInput("What is the character's name?")
    return CharacterSheet(creatorID, displayName)