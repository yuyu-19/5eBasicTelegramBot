import json
import os
import re


#TODO: EDIT THE ROLLS SO THEY FOLLOW THE SAME STRUCTURE AS THE ITEM ONES.

def main():
    textFile = open(r"C:\Users\lugia19\Desktop 2\New Text Document.txt")
    textLines = textFile.readlines()
    currentIndex = 0
    currentSpellID = ""
    currentProperty = ""
    allSpells = {}
    spellData = {}
    for line in textLines:
        line = line.replace("\n","").replace("â€™","'")
        if ("-level" in line or "cantrip" in line) and "casting time" in textLines[currentIndex+1].lower():
            #We've found a new spell.
            currentSpellID = textLines[currentIndex-1].lower().replace(" ","_").replace("'","").replace("\n","")
            spellData["display_name"] = textLines[currentIndex-1].replace("\n","")
            spellData["roll_data"] = list()
            if "cantrip" in line:
                spellData["spell_level"] = 0
            else:
                spellData["spell_level"] = int(line[0])

        if currentProperty == "duration":
            currentProperty = "description"
        if currentProperty != "description":
            if "casting time" in line.lower():
                currentProperty = "cast_time"
            if "range" in line.lower():
                currentProperty = "range"
            if "components" in line.lower():
                currentProperty = "components"
            if "duration" in line.lower():
                currentProperty = "duration"

        if "at higher levels" in line.lower() or "spell's damage increases by" in line.lower():
            currentProperty = "higher_levels_description"

        if currentProperty != "":
            if currentProperty not in spellData:
                spellData[currentProperty] = ""
            if line[len(line)-1] == "-":    #Description line ends in a hyphen
                spellData[currentProperty] += line[0:len(line)-1]
            else:
                spellData[currentProperty] += line.replace("\n","") + " "
            if re.search(r"\d+d\d+",line) and currentProperty == "description":
                rollValue = re.search(r"\d+d\d+",line).group(0)
                spellData["roll_data"].append({
                    "base_roll": rollValue
                })

            if (currentIndex+3 < len(textLines) and "casting time" in textLines[currentIndex+3].lower()) or currentIndex == len(textLines)-1: #This means we've reached the end of the current spell
                currentProperty = "" #Stop adding to the object.

                if spellData["spell_level"] == 0 and "higher_levels_description" in spellData:
                    spellData["roll_data"][0]["cantrip_damage_scaling"] = {}
                    #level (2d12), 11th level (3d12), and 17th level
                    description = str(spellData["higher_levels_description"])
                    index = description.index("damage increases by")
                    while description.find("level", index+1) != -1:
                        index = description.find("level", index+1)
                        index2 = index - 3
                        index = description.rfind(" ", 0, index-2)+1
                        levelNumber = description[index:index2]
                        print(levelNumber)
                        index = description.find("(", index+1)+1
                        index2 = description.find(")", index + 1)
                        damage = description[index:index2]
                        print(damage)
                        spellData["roll_data"][0]["cantrip_damage_scaling"][levelNumber] = damage
                elif spellData["spell_level"] > 0 and "higher_levels_description" in spellData:
                    description = str(spellData["higher_levels_description"])
                    x = re.search("(\dd\d\d?) for (each|every two) slot level",description)
                    if x is not None:
                        rollData = spellData["roll_data"][0]
                        rollData["scaling_amount"] = x.group(1)
                        if x.group(2) == "each":
                            rollData["additional_levels_required"] = 1
                        else:
                            match x.group(2).replace("every ",""): #Pretty sure nothing over 2 exists but I'll do 3 and 4 just to be safe
                                case "two":
                                    rollData["additional_levels_required"] = 2
                                case "three":
                                    rollData["additional_levels_required"] = 3
                                case "four":
                                    rollData["additional_levels_required"] = 4

                allSpells[currentSpellID] = spellData
                spellData = {}


        currentIndex += 1
    json.dump(allSpells,open("allSpellsNew.json","w"),indent=4)
    print("DONE")


if __name__ == "__main__":
    main()
