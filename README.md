# 5eBasicTelegramBot

This bot is an implementation of the 5e SRD.

It is messaging system-agnostic. It contains an implementation of the userConversation interface for Telegram and a simple console input, but it could easily be extended to support other platforms.
The flow of its functions is as follows:
- A userConversation object is created
- Control is handed off to the UserData object for the current user, which allows the user to select and existing campaign, create one or join one.
- Once a campaign has been selected, control is given to the campaignData object, which allows the user to create PCs or Monsters (if they're a DM).

It allows the user to link accounts between platforms to access data across them.

It offers the ability for players to create characters in a guided manner, abiding by the rules listed in the SRD.

It offers the choice of:
- Premade backgrounds
- Classes (Sadly due to the amount of manual work required I was only able to fully implement the Wizard class, but the systems are in place to handle all classes).
- All the spells from the SRD
- Guided creation of items


All the data is saved in a database using python's pickle library, in the path specified in the config file.
A sample config file is included.

The main classes of the project are as follows:

# Utility and messaging classes
- Main - Initializes the config and the selected MessagingProvider.
- userConversation - This is the interface to communicate with the user. Two implementations are present, consoleConversation and telegramConversation.
- telegramConversation - The userConversation implementation for Telegram. It uses the telegram-python-bot library, creating events when waiting on user input. Multi-user functionality is achieved through the use of asyncio.
- consoleConversation - The userConversation implementation for the console. It uses the async input library.
- systemDataProvider - Contains methods that allow other classes to access data regarding the system (5e in this case).
- database - Handles storing and loading all data. Currently uses the pickle library, but could easily be swapped for SQL if required.

# Data classes
- userData - Contains the user's joined and created campaigns.
- campaignData - Contains all the characters for the campaign, both PCs and Monsters.

# Sheet classes
- characterSheet - This is the abstract class for character sheets. It contains methods and data that are shared between both Monsters and PCs.
- PCSheet - This class allows the user to create a PC based on the data given by the systemDataProvider.
- MonsterSheet - This class allows a DM to create a wholly custom monster.

# Item classes
- GenericItem - This is the class for "generic" items which do not fall under any specific category.
- WeaponItem - This class is for weapons. It contains weapon-specific data, such as whether the user is proficient with it.
- Armor - This class is for armor. It contains armor-specific data, such as the armor type, AC, and strength requirement.

# Other data classes used by Sheet classes
- spellData - Contains all data for a spell, including helper methods for rolling dice and upcasting.

