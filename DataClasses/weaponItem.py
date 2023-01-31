from __future__ import annotations

import DataClasses.genericItem
import systemDataProvider
from DataClasses.genericItem import GenericItem
from messaging.userConversation import UserConversation



class WeaponItem(GenericItem):
    @staticmethod
    async def weaponFactory(userConvo: UserConversation, maxPrice=float("inf")) -> WeaponItem:
        newWeaponData = await GenericItem.baseItemFactory(userConvo, maxPrice)

        await userConvo.show("Please input the data related to the weapon's attack roll.")
        newWeaponData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))
        await userConvo.show("Please input the data related to the weapon's damage roll.")
        newWeaponData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))
        while await userConvo.yesNo("Would you like to add another roll?"):
            newWeaponData["associated_rolls"].append(await GenericItem.askItemRollData(userConvo))
        return WeaponItem(newWeaponData)

    def __init__(self, weaponData):
        super().__init__(weaponData)
        self.type = "weapon"

    async def requestEdit(self, userConvo: UserConversation):
        options = ["price","display_name","description","weight","associated_rolls"]
        userFinished = False
        while not userFinished:
            selectedOption = await userConvo.chooseFromListOfStrings(options, "Select which property to edit.")
            await userConvo.show(str(getattr(self, selectedOption)))
            if selectedOption in ["price","display_name","description","weight"]:
                setattr(self, selectedOption,await userConvo.requestCustomInput("Please input the new value."))
            else:
                match selectedOption:
                    case "associated_rolls":
                        rollOptions = ["add", "exit"]
                        if len(self.associated_rolls) > 2:
                            rollOptions.insert(1, "remove")
                        match await userConvo.chooseFromListOfStrings(rollOptions, "Please choose an option."):
                            case "add":
                                self.associated_rolls.append(GenericItem.askItemRollData(userConvo))
                            case "remove":
                                self.associated_rolls.remove(await userConvo.chooseFromListOfDict(self.associated_rolls, "Choose which roll to remove."))
            userFinished = await userConvo.yesNo("Are you finished editing the item?")