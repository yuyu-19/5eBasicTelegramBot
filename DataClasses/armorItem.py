from __future__ import annotations

import DataClasses.genericItem
from DataClasses.genericItem import GenericItem
from messaging.userConversation import UserConversation




class ArmorItem(GenericItem):
    @staticmethod
    async def armorFactory(userConvo: UserConversation, maxPrice=float("inf")) -> ArmorItem:
        newArmorData = await GenericItem.baseItemFactory(userConvo, maxPrice)
        armorTypes = ["heavy", "medium", "light"]
        newArmorData["armor_type"] = await userConvo.chooseFromListOfStrings(armorTypes, "What type of armor is it?")
        newArmorData["base_AC"] = await userConvo.requestInt("What is it's base armor class?", 0)
        if await userConvo.yesNo("Does it have a strength requirement?"):
            newArmorData["str_req"] = await userConvo.requestInt("What is it?")
        else:
            newArmorData["str_req"] = 0
        newArmorData["stealth_disad"] = await userConvo.yesNo("Does it impose disadvantage on stealth checks?")

        if await userConvo.yesNo("Does the armor have a roll associated with it?"):
            newArmorData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))
            while await userConvo.yesNo("Would you like to add another roll?"):
                newArmorData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))
        return ArmorItem(newArmorData)



    def __init__(self, armorData):
        super().__init__(armorData)
        self.type = "armor"
        self.armor_type = armorData["armor_type"]
        self.base_AC = armorData["base_AC"]
        self.str_req = armorData["str_req"]
        self.stealth_disad = armorData["stealth_disad"]
        self.equipped = False

    def calculateAC(self, dexterityModifier) -> int:
        match self.armor_type:
            case "heavy":
                return self.base_AC
            case "medium":
                return self.base_AC + min(dexterityModifier, 2) #Limit it to 2
            case "light":
                return self.base_AC + dexterityModifier

    def isSlowedDown(self, strengthStat:int) -> bool:
        if self.armor_type == "heavy":
            if strengthStat < self.str_req:
                return True
        return False


    def _get_display_data(self) -> str:
        outputString = super()._get_display_data() + "\n"
        outputString += "This is a " + self.armor_type + " armor." + "\n"
        outputString += "The armor has a base AC of " + str(self.base_AC) + "\n"
        if self.str_req > 0:
            outputString += "The armor has a strength requirement of " + str(self.str_req)+ "\n"
        if self.stealth_disad:
            outputString += "The armor imposes disadvantage on stealth checks."
        return outputString

    async def requestEdit(self, userConvo: UserConversation):
        options = ["price","display_name","description","weight","associated_rolls", "proficient", "attack_stats", "attack_bonus"]
        userFinished = False
        while not userFinished:
            selectedOption = await userConvo.chooseFromListOfStrings(options, "Select which property to edit.")

            if selectedOption in ["price","display_name","description","weight"]:
                setattr(self, selectedOption,await userConvo.requestCustomInput("Please input the new value."))
            else:
                match selectedOption:
                    case "stealth_disad":
                        self.stealth_disad = await userConvo.yesNo("Does the armor impose disadvantage on stealth checks?")
                    case "base_AC":
                        self.base_AC = await userConvo.requestInt("What is the armor's base AC?")
                    case "str_req":
                        self.str_req = await userConvo.requestInt("What is the armor's strength requirement?")
                    case "armor_type":
                        self.armor_type = await userConvo.chooseFromListOfStrings(["heavy", "medium", "light"], "What is the armor's type?")
                    case "associated_rolls":
                        rollOptions = ["add", "exit"]
                        if len(self.associated_rolls) > 0:
                            rollOptions.insert(1, "remove")
                        match await userConvo.chooseFromListOfStrings(rollOptions, "Please choose an option."):
                            case "add":
                                self.associated_rolls.append(await GenericItem.askItemRollData(userConvo))
                            case "remove":
                                self.associated_rolls.remove(await userConvo.chooseFromListOfDict(self.associated_rolls, "Choose which roll to remove."))
            userFinished = await userConvo.yesNo("Are you finished editing the item?")