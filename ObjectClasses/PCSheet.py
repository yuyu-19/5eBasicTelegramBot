import SystemDataProvider
from ObjectClasses.characterSheet import CharacterSheet


class PCSheet(CharacterSheet):
    def __init__(self, userID, classID):
        #Remember that proficiency is (floor((character_level-1)/4)+2) for players
        super().__init__(userID)
        self._skills = SystemDataProvider.getDefaultSkills()

        self._armorProficiencies = []
        self._weaponProficiencies = []
        self._languagesKnown = []
        self._hpDie = ""

        for skillID, skill in self._skills:
            skill["proficiency_multiplier"] = 0

        #Remember to ask the user which skills they want proficiency in!

        self._characterLevel = 0
        classData = SystemDataProvider.getClassData(classID)
        self._hpDie = classData["hit_die"]

        for savingThrow in classData["saving_throws"]:
            self._savingThrows[savingThrow]["proficiency_multiplier"] = 1

        self.levelUp(classID)

    def setSkillProficiency(self, skillID):
        self._skills[skillID]["proficiency_multiplier"] = 1
    def setSkillExpertise(self, skillID):
        self._skills[skillID]["proficiency_multiplier"] = 2


    def levelUp(self, classID):
        #Remember to add HP roll or average, etc etc
        levelFeatures = SystemDataProvider.getClassLevelFeatures(classID, self._characterLevel+1)


        self._characterLevel += 1
