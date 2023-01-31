from __future__ import annotations

import math

import systemDataProvider
from DataClasses.characterSheet import CharacterSheet
from systemDataProvider import *
from messaging.userConversation import UserConversation

class MonsterSheet(CharacterSheet):
    @staticmethod
    async def monsterSheetFactory(userConvo: UserConversation) -> MonsterSheet:
        newSheet = MonsterSheet(userConvo.getUserID(), await userConvo.requestCustomInput("Please input the character's name."))
        await userConvo.show("Created an empty sheet. Please edit its values as you see fit.")
        await newSheet.startUserConversation(userConvo)
        return newSheet

    def __init__(self, creatorID, displayName):
        super().__init__(creatorID,displayName)
        self._actions:dict[str, list[dict[str, str|dict]]] = {
            "normal": list(),
            "legendary": list(),
            "lair": list()
        }
        self._characterLevel = 1        #This is for use with cantrips.
        self._spellsKnown:dict[str, list[Spell]] = dict()

        for i in range(0,10):   #Initialize the spell levels
            self._spellsKnown[str(i)] = list()

        self._AC = 0
        self._type = ""
        self._tags = list()
        self._XPAward = 0

    async def startUserConversation(self, userConvo: UserConversation):
        userFinished = False
        rootOptions = ["stats", "skills", "saving throws", "speed",
                       "language","size","max_hp","display_name","features",
                       "character_level_for_cantrips","proficiency_bonus",
                       "proficiencies", "actions", "spells", "ac", "type", "tags", "xp"]
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
                case "proficiencies":
                    await self._dialogProficiency(userConvo)
                case "actions": #Actions have the same structure as features.
                    chosenType = await userConvo.chooseFromListOfStrings(list(self._actions.keys()), "Which type of actions would you like to edit?")
                    await self._dialogFeatureLikeObject(userConvo, self._actions[chosenType], chosenType + " action")
                case "spells":
                    await self._dialogSpells(userConvo)
                case "ac":
                    await userConvo.show("Current AC: " + str(self._AC))
                    if await userConvo.yesNo("Would you like to change the AC?"):
                        self._AC = await userConvo.requestInt("Please input the new AC.")
                case "type":
                    await userConvo.show("Current type: " + self._type)
                    if await userConvo.yesNo("Would you like to change the type?"):
                        self._type = await userConvo.requestCustomInput("Please input the new type.")
                case "tags":
                    if len(self._tags) > 0:
                        outputString = ""
                        for tag in self._tags:
                            outputString += tag + ", "
                        outputString = outputString[:len(outputString)-2]
                        await userConvo.show("Current tags:\n" + outputString)
                    if await userConvo.yesNo("Would you like to change the tags?"):
                        if len(self._tags) == 0 or await userConvo.yesNo("Would you like to add one or remove one?", trueOption="add", falseOption="remove"):
                            self._tags.append(await userConvo.requestCustomInput("Please input the new tag."))
                        else:
                            self._tags.remove(await userConvo.chooseFromListOfStrings(self._tags,"Please choose which tag to remove."))
                case "xp":
                    await userConvo.show("Current XP reward: " + str(self._XPAward))
                    if await userConvo.yesNo("Would you like to it?"):
                        self._XPAward = await userConvo.requestInt("Please input the new value.")
                case "language":
                    await self._dialogLanguage(userConvo)
                case "size":
                    await userConvo.show("Current size category: " + self._size)
                    if await userConvo.yesNo("Would you like to change it?"):
                        self._size = await userConvo.requestCustomInput("Please input the new value.")
                case "max_hp":
                    await userConvo.show("Current max HP: " + str(self._maxHP))
                    if await userConvo.yesNo("Would you like to change it?"):
                        self._maxHP = await userConvo.requestInt("Please input the new value.")
                case "display_name":
                    await userConvo.show("Current display name: " + self.display_name)
                    if await userConvo.yesNo("Would you like to change it?"):
                        self.display_name = await userConvo.requestCustomInput("Please input the new value.")
                case "character_level_for_cantrips":
                    await userConvo.show("Current character level: " + str(self._characterLevel))
                    if await userConvo.yesNo("Would you like to change it?"):
                        self._characterLevel = await userConvo.requestInt("Please input the new value.")
                case "proficiency_bonus":
                    await userConvo.show("Current proficiency bonus: " + str(self._proficiencyBonus))
                    if await userConvo.yesNo("Would you like to change it?"):
                        self._proficiencyBonus = await userConvo.requestInt("Please input the new value.")

    async def _dialogSpells(self, userConvo):
        spellsWithRollsByLevel = dict()
        total = 0
        for key, value in self._spellsKnown.items():
            total += len(value)
        if total > 0:
            for levelNumber, levelSpells in self._spellsKnown.items():
                if len(levelSpells) > 0:
                    outputString = "\nSpell level " + levelNumber + "\n"
                    for spell in levelSpells:
                        outputString += spell.display_name + ", "
                        if spell.hasRolls():
                            if levelNumber not in spellsWithRollsByLevel:
                                spellsWithRollsByLevel[levelNumber] = list()
                            spellsWithRollsByLevel[levelNumber].append(spell)
                    outputString = outputString[:len(outputString) - 2]
                    await userConvo.show(outputString)
        options = ["view", "add", "remove", "exit"]
        if total == 0:
            options.remove("remove")
            options.remove("view")
        if len(spellsWithRollsByLevel) > 0:
            options.insert(1,"roll")
        match await userConvo.chooseFromListOfStrings(options,"Choose an option."):
            case "view":
                chosenLevel = await userConvo.chooseFromListOfStrings(list(self._spellsKnown.keys()), "What level spell would you like to view?")
                chosenSpell: Spell = await userConvo.chooseFromListOfDict(self._spellsKnown[chosenLevel], "Choose a spell to view.")
                await chosenSpell.displayData(userConvo, self._characterLevel)
            case "add":
                chosenLevel = await userConvo.requestInt("What level spell would you like to add?", 0,9)
                eligibleSpells = systemDataProvider.getSpellsByLevel(chosenLevel)
                if str(chosenLevel) not in self._spellsKnown:
                    self._spellsKnown[str(chosenLevel)] = list()
                for spell in self._spellsKnown[str(chosenLevel)]:
                    eligibleSpells.pop(spell.id)
                if len(eligibleSpells) == 0:
                    await userConvo.show("You've already learned all spells of that level!")
                else:
                    chosenSpellID = await userConvo.chooseFromDict(eligibleSpells, "Choose which spell to add.")
                    self._spellsKnown[str(chosenLevel)].append(systemDataProvider.getSpell(chosenSpellID))
            case "remove":
                chosenLevel = await userConvo.requestInt("What level spell would you like to remove?", 0, 9)
                if len(self._spellsKnown[str(chosenLevel)]) == 0:
                    await userConvo.show("The monster doesn't know any spells of that level!")
                else:
                    chosenSpell: Spell = await userConvo.chooseFromListOfDict(self._spellsKnown[str(chosenLevel)], "Choose which spell to remove.")
                    self._spellsKnown[str(chosenLevel)].remove(chosenSpell)
            case "roll":
                chosenLevel = await userConvo.chooseFromListOfStrings(list(spellsWithRollsByLevel.keys()), "What level spell would you like to roll dice for?")
                chosenSpell: Spell = await userConvo.chooseFromListOfDict(spellsWithRollsByLevel[chosenLevel], "Choose a spell to roll dice for.")
                await chosenSpell.rollSpell(userConvo, characterLevel=self._characterLevel)


