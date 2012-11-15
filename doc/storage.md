# Storage

conveyor needs storage for:

  * firmware
  * machines

conveyor stores data in a folder with a platform-specific location:

  * OSX: /Library/com.makerbot.conveyor/
  * Ubuntu: /var/lib/conveyor/
  * Windows: C:\Program Files\MakerBot\conveyor\

Under the platform-specific folder conveyor uses the same sub-folder layout for all three supported platforms:

  * <prefix>/
      * firmware/
          * <version>/
              * eeprom.json
              * firmware.hex
      * machines/
          * machine.sqlite

Firmware is stored in further sub-folders, one folder for each version of firmware.
Each firmware version folder has two files: the JSON map for the EEPROM and the firmware binary.

Machine information is stored in a SQLite database.
SQLite is included in Python starting with version 2.5 so it does not introduce any new dependencies.
