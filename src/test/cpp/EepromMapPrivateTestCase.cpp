#include "SampleTestCase.h"
#include <fstream>
#include <QString>
#include <QStringList>
#include <string>
#include <vector>
#include <jsoncpp/json/reader.h>
#include <jsoncpp/json/value.h>


#include "EepromMapPrivateTestCase.h"
#include "../../main/cpp/eeprommapprivate.cpp"


namespace conveyor
{

CPPUNIT_TEST_SUITE_REGISTRATION(EepromMapPrivateTestCase);


EepromMapPrivate* EepromMapPrivateTestCase::createEepromMap(void)
{
  Json::Value root;
  Json::Reader reader; 
  reader.parse(this->eeprom_json, root);
  EepromMapPrivate* map = new EepromMapPrivate(root);
  return map;
}

void EepromMapPrivateTestCase::testSplitPathNoSubMap(void)
{
  EepromMapPrivate* eepromMap = this->createEepromMap();
  QString path = QString("MACHINE_NAME");
  QStringList expectedPath = QStringList(QString("MACHINE_NAME"));
  QStringList gotPath = eepromMap->splitPath(path);
  CPPUNIT_ASSERT(expectedPath == gotPath);
}

void EepromMapPrivateTestCase::testSplitPathSubMap(void)
{
  EepromMapPrivate* eepromMap = this->createEepromMap();
  QString path = QString("ACCELERATION_SETTINGS/DEFAULTS_FLAG");
  QStringList expectedPath = (QStringList() << "ACCELERATION_SETTINGS" << "DEFAULTS_FLAG");
  QStringList gotPath = eepromMap->splitPath(path);
  CPPUNIT_ASSERT(expectedPath == gotPath);
}

void EepromMapPrivateTestCase::testGetEntryTopLevelEntry(void)
{
  EepromMapPrivate * eepromMap = this->createEepromMap();
  Json::Value root;
  Json::Reader reader; 
  reader.parse(this->eeprom_json, root);
  QStringList path = QStringList("MACHINE_NAME");
  Json::Value expectedMap = root["eeprom_map"]["MACHINE_NAME"];
  Json::Value gotMap = (*eepromMap->getEntry(path));
  CPPUNIT_ASSERT(expectedMap == gotMap);
}

void EepromMapPrivateTestCase::testGetEntryWithSubMap(void)
{
  EepromMapPrivate * eepromMap = this->createEepromMap();
  Json::Value root;
  Json::Reader reader; 
  reader.parse(this->eeprom_json, root);
  QStringList path = (QStringList() << "ACCELERATION_SETTINGS" << "ACTIVE_OFFSET");
  Json::Value expectedMap = root["eeprom_map"]["ACCELERATION_SETTINGS"]["sub_map"]["ACTIVE_OFFSET"];
  Json::Value gotMap = (*eepromMap->getEntry(path));
  CPPUNIT_ASSERT(expectedMap == gotMap);
}

void EepromMapPrivateTestCase::testGetEepromMap(void)
{
  EepromMapPrivate* eepromMap = this->createEepromMap();
  Json::Value root;
  Json::Reader reader; 
  reader.parse(this->eeprom_json, root);
  Json::Value expectedMap = root;
  Json::Value gotMap = eepromMap->getEepromMap();
  CPPUNIT_ASSERT(expectedMap == gotMap);
}

void EepromMapPrivateTestCase::testSetString(void)
{
  EepromMapPrivate* eepromMap = this->createEepromMap();
  Json::Value the_map = eepromMap->getEepromMap();
  Json::Value the_value = the_map["eeprom_map"]["MACHINE_NAME"]["value"];
  Json::Value the_name = the_value[0];
  std::string currentNameInMap = the_name.asString();

  std::string currentName = "The Replicator";
  CPPUNIT_ASSERT(currentName == currentNameInMap);

  //Change the name
  QString newName = QString("the_awesomecator");
  std::vector<QString> newValues;
  newValues.push_back(newName);  
  //The Path
  QString path = QString("MACHINE_NAME");
  eepromMap->setString(path, newValues);
  Json::Value gotMap = eepromMap->getEepromMap();
  Json::Value gotValues = gotMap["eeprom_map"]["MACHINE_NAME"]["value"];
  Json::Value gotName = gotValues[0];
  QString gotString = QString(gotName.asCString());
  CPPUNIT_ASSERT(newName == gotString);
}

void EepromMapPrivateTestCase::testSetFloat(void)
{
  EepromMapPrivate * eepromMap = this->createEepromMap();
  Json::Value the_map = eepromMap->getEepromMap();
  Json::Value oldDTerm  = the_map["eeprom_map"]["T0_DATA_BASE"]["sub_map"]["EXTRUDER_PID_BASE"]["sub_map"]["D_TERM_OFFSET"]["value"];
  float currentDTerm = oldDTerm[0].asFloat();
  float expectedDTerm = 36.0;
  CPPUNIT_ASSERT_EQUAL(currentDTerm, expectedDTerm);

  float newDTerm = 3.33;
  std::vector<float> newValues;
  newValues.push_back(newDTerm);
  QString path = QString("T0_DATA_BASE/EXTRUDER_PID_BASE/D_TERM");
  eepromMap->setFloat(path, newValues);
  Json::Value gotDTerms = eepromMap->getEepromMap()["eeprom_map"]["T0_DATA_BASE"]["sub_map"]["EXTRUDER_PID_BASE"]["sub_map"]["D_TERM"]["value"];
  float gotDTerm = gotDTerms[0].asFloat();
  CPPUNIT_ASSERT_EQUAL(newDTerm, gotDTerm);
}

void EepromMapPrivateTestCase::testSetInt(void)
{
  EepromMapPrivate * eepromMap = this->createEepromMap();
  //Check that T0_DATA_BASE/BACKOFF_FORWARD_TIME starts out correctly
  Json::Value oldTimeValues = eepromMap->getEepromMap()["eeprom_map"]["T0_DATA_BASE"]["sub_map"]["BACKOFF_FORWARD_TIME"]["value"];
  int currentBackoffTime = oldTimeValues[0].asInt();
  int expectedBackoffTime = 500;
  CPPUNIT_ASSERT_EQUAL(currentBackoffTime, expectedBackoffTime);
  
  //Change T0_DATA_BASE/BACKOFF_FORWARD_TIME 
  int newBackoffTime = 123;
  std::vector<int> newValues;
  newValues.push_back(newBackoffTime);
  QString path = QString("T0_DATA_BASE/BACKOFF_FORWARD_TIME");
  eepromMap->setInt(path, newValues);
  Json::Value gotTimeValues = eepromMap->getEepromMap()["eeprom_map"]["T0_DATA_BASE"]["sub_map"]["BACKOFF_FORWARD_TIME"]["value"];
  int gotBackoffTime = gotTimeValues[0].asInt();
  CPPUNIT_ASSERT_EQUAL(newBackoffTime, gotBackoffTime);
}

void EepromMapPrivateTestCase::testGetString(void)
{
  EepromMapPrivate* eepromMap = this->createEepromMap();
  Json::Value nameValues = eepromMap->getEepromMap()["eeprom_map"]["MACHINE_NAME"]["value"];
  Json::Value expectedValue = nameValues[0];
  QString expectedName = QString(expectedValue.asCString()); 
  QString path = QString("MACHINE_NAME");
  std::vector<QString> * gotValues = eepromMap->getString(path);
  QString gotName = (*gotValues)[0];
  CPPUNIT_ASSERT(expectedName == gotName);
}

void EepromMapPrivateTestCase::testGetFloat(void)
{
  EepromMapPrivate * eepromMap = this->createEepromMap();
  Json::Value dTerm = eepromMap->getEepromMap()["eeprom_map"]["T0_DATA_BASE"]["sub_map"]["EXTRUDER_PID_BASE"]["sub_map"]["D_TERM_OFFSET"]["value"];
  float expectedDTerm = dTerm[0].asFloat();
  QString path = QString("T0_DATA_BASE/EXTRUDER_PID_BASE/D_TERM_OFFSET");
  std::vector<float> * gotValues = eepromMap->getFloat(path);
  float gotDTerm = (*gotValues)[0];
  CPPUNIT_ASSERT(expectedDTerm == gotDTerm);
}


void EepromMapPrivateTestCase::testGetInt(void)
{
  EepromMapPrivate * eepromMap = this->createEepromMap();
  Json::Value backoffForwardTimeValues = eepromMap->getEepromMap()["eeprom_map"]["T0_DATA_BASE"]["sub_map"]["BACKOFF_FORWARD_TIME"]["value"];
  int expectedBackoffForwardTime = backoffForwardTimeValues[0].asInt();
  QString path = QString("T0_DATA_BASE/BACKOFF_FORWARD_TIME");
  std::vector<int> * gotValues = eepromMap->getInt(path);
  int gotBackoffForwardTime = (*gotValues)[0];
  CPPUNIT_ASSERT_EQUAL(expectedBackoffForwardTime, gotBackoffForwardTime);
}

//Dont scroll down further, huge json file enclosed!!!




void EepromMapPrivateTestCase::setUp(void)
{
 this->eeprom_json = "{\"eeprom_map\": {\"ACCELERATION_SETTINGS\": {\"eeprom_map\": \"acceleration_eeprom_offsets\", \"sub_map\": {\"ACTIVE_OFFSET\": {\"type\": \"B\", \"value\": [0], \"offset\": \"0x00\"}, \"DEFAULTS_FLAG\": {\"type\": \"B\", \"value\": [128], \"offset\": \"0x1A\"}, \"MINIMUM_SPEED\": {\"type\": \"H\", \"value\": [15], \"offset\": \"0x18\"}, \"AXIS_JERK_OFFSET\": {\"offset\": \"0x0E\", \"type\": \"HHHHH\", \"value\": [20.0, 20.0, 1.0, 2.0, 2.0], \"floating_point\": \"True\"}, \"ACCELERATION_RATE_OFFSET\": {\"type\": \"H\", \"value\": [3000], \"offset\": \"0x02\"}, \"AXIS_RATES_OFFSET\": {\"type\": \"HHHHH\", \"value\": [3000, 3000, 1000, 3000, 3000], \"offset\": \"0x04\"}}, \"offset\": \"0x016E\"}, \"T0_DATA_BASE\": {\"eeprom_map\": \"toolhead_eeprom_offsets\", \"sub_map\": {\"EXTRA_FEATURES\": {\"type\": \"H\", \"value\": [65535], \"offset\": \"0x0016\"}, \"HBP_PID_BASE\": {\"eeprom_map\": \"pid_eeprom_offsets\", \"sub_map\": {\"D_TERM_OFFSET\": {\"offset\": \"4\", \"type\": \"H\", \"value\": [36.0], \"floating_point\": \"True\"}, \"P_TERM_OFFSET\": {\"offset\": \"0\", \"type\": \"H\", \"value\": [7.0], \"floating_point\": \"True\"}, \"I_TERM_OFFSET\": {\"offset\": \"2\", \"type\": \"H\", \"value\": [0.33], \"floating_point\": \"True\"}}, \"offset\": \"0x0010\"}, \"FEATURES\": {\"type\": \"H\", \"value\": [65287], \"offset\": \"0x0000\"}, \"BACKOFF_REVERSE_TIME\": {\"type\": \"H\", \"value\": [500], \"offset\": \"0x0004\"}, \"BACKOFF_STOP_TIME\": {\"type\": \"H\", \"value\": [5], \"offset\": \"0x0002\"}, \"BACKOFF_FORWARD_TIME\": {\"type\": \"H\", \"value\": [500], \"offset\": \"0x0006\"}, \"BACKOFF_TRIGGER_TIME\": {\"type\": \"H\", \"value\": [300], \"offset\": \"0x0008\"}, \"EXTRUDER_PID_BASE\": {\"eeprom_map\": \"pid_eeprom_offsets\", \"sub_map\": {\"D_TERM_OFFSET\": {\"offset\": \"4\", \"type\": \"H\", \"value\": [36.0], \"floating_point\": \"True\"}, \"P_TERM_OFFSET\": {\"offset\": \"0\", \"type\": \"H\", \"value\": [7.0], \"floating_point\": \"True\"}, \"I_TERM_OFFSET\": {\"offset\": \"2\", \"type\": \"H\", \"value\": [0.33], \"floating_point\": \"True\"}}, \"offset\": \"0x000A\"}, \"SLAVE_ID\": {\"type\": \"B\", \"value\": [50], \"offset\": \"0x0018\"}, \"COOLING_FAN_SETTINGS\": {\"eeprom_map\": \"cooler_eeprom_offsets\", \"sub_map\": {\"ENABLE_OFFSET\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0\"}, \"SETPOINT_C_OFFSET\": {\"type\": \"B\", \"value\": [50], \"offset\": \"1\"}}, \"offset\": \"0x001A\"}}, \"tool_index\": \"0\", \"offset\": \"0x0100\"}, \"INTERNAL_VERSION\": {\"type\": \"H\", \"value\": [65535], \"offset\": \"0x0048\"}, \"PREHEAT_SETTINGS\": {\"eeprom_map\": \"preheat_eeprom_offsets\", \"sub_map\": {\"PREHEAT_RIGHT_OFFSET\": {\"type\": \"H\", \"value\": [220], \"offset\": \"0x00\"}, \"PREHEAT_ON_OFF_OFFSET\": {\"type\": \"B\", \"value\": [5], \"offset\": \"0x06\"}, \"PREHEAT_PLATFORM_OFFSET\": {\"type\": \"H\", \"value\": [110], \"offset\": \"0x04\"}, \"PREHEAT_LEFT_OFFSET\": {\"type\": \"H\", \"value\": [220], \"offset\": \"0x02\"}}, \"offset\": \"0x0158\"}, \"TOOL_COUNT\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0x0042\"}, \"TOTAL_BUILD_TIME\": {\"eeprom_map\": \"build_time_offsets\", \"sub_map\": {\"MINUTES_OFFSET\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0x02\"}, \"HOURS_OFFSET\": {\"type\": \"H\", \"value\": [0], \"offset\": \"0x00\"}}, \"offset\": \"0x01A0\"}, \"AXIS_INVERSION\": {\"type\": \"B\", \"value\": [23], \"offset\": \"0x0002\"}, \"FILAMENT_HELP_SETTINGS\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0x0160\"}, \"VERSION_HIGH\": {\"type\": \"B\", \"value\": [5], \"offset\": \"0x0001\"}, \"THERM_TABLE\": {\"eeprom_map\": \"therm_eeprom_offsets\", \"sub_map\": {\"THERM_DATA_OFFSET\": {\"type\": \"H\", \"value\": [13862, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878, 13878], \"mult\": \"40\", \"offset\": \"0x10\"}, \"THERM_BETA_OFFSET\": {\"type\": \"i\", \"value\": [4067], \"offset\": \"0x08\"}, \"THERM_R0_OFFSET\": {\"type\": \"i\", \"value\": [100000], \"offset\": \"0x00\"}, \"THERM_T0_OFFSET\": {\"type\": \"i\", \"value\": [25], \"offset\": \"0x04\"}}, \"offset\": \"0x0074\"}, \"LED_STRIP_SETTINGS\": {\"eeprom_map\": \"blink_eeprom_offsets\", \"sub_map\": {\"LED_HEAT_OFFSET\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0x02\"}, \"CUSTOM_COLOR_OFFSET\": {\"type\": \"BBB\", \"value\": [255, 0, 0], \"offset\": \"0x04\"}, \"BASIC_COLOR_OFFSET\": {\"type\": \"B\", \"value\": [0], \"offset\": \"0x00\"}}, \"offset\": \"0x0140\"}, \"AXIS_HOME_POSITIONS_STEPS\": {\"type\": \"iiiii\", \"value\": [14309, 6778, 0, 0, 0], \"offset\": \"0x000E\"}, \"VERSION_LOW\": {\"type\": \"B\", \"value\": [5], \"offset\": \"0x0000\"}, \"ENDSTOP_INVERSION\": {\"type\": \"B\", \"value\": [159], \"offset\": \"0x0004\"}, \"T1_DATA_BASE\": {\"eeprom_map\": \"toolhead_eeprom_offsets\", \"sub_map\": {\"EXTRA_FEATURES\": {\"type\": \"H\", \"value\": [65535], \"offset\": \"0x0016\"}, \"HBP_PID_BASE\": {\"eeprom_map\": \"pid_eeprom_offsets\", \"sub_map\": {\"D_TERM_OFFSET\": {\"offset\": \"4\", \"type\": \"H\", \"value\": [36.0], \"floating_point\": \"True\"}, \"P_TERM_OFFSET\": {\"offset\": \"0\", \"type\": \"H\", \"value\": [7.0], \"floating_point\": \"True\"}, \"I_TERM_OFFSET\": {\"offset\": \"2\", \"type\": \"H\", \"value\": [0.33], \"floating_point\": \"True\"}}, \"offset\": \"0x0010\"}, \"FEATURES\": {\"type\": \"H\", \"value\": [65336], \"offset\": \"0x0000\"}, \"BACKOFF_REVERSE_TIME\": {\"type\": \"H\", \"value\": [500], \"offset\": \"0x0004\"}, \"BACKOFF_STOP_TIME\": {\"type\": \"H\", \"value\": [5], \"offset\": \"0x0002\"}, \"BACKOFF_FORWARD_TIME\": {\"type\": \"H\", \"value\": [500], \"offset\": \"0x0006\"}, \"BACKOFF_TRIGGER_TIME\": {\"type\": \"H\", \"value\": [300], \"offset\": \"0x0008\"}, \"EXTRUDER_PID_BASE\": {\"eeprom_map\": \"pid_eeprom_offsets\", \"sub_map\": {\"D_TERM_OFFSET\": {\"offset\": \"4\", \"type\": \"H\", \"value\": [36.0], \"floating_point\": \"True\"}, \"P_TERM_OFFSET\": {\"offset\": \"0\", \"type\": \"H\", \"value\": [7.0], \"floating_point\": \"True\"}, \"I_TERM_OFFSET\": {\"offset\": \"2\", \"type\": \"H\", \"value\": [0.33], \"floating_point\": \"True\"}}, \"offset\": \"0x000A\"}, \"SLAVE_ID\": {\"type\": \"B\", \"value\": [50], \"offset\": \"0x0018\"}, \"COOLING_FAN_SETTINGS\": {\"eeprom_map\": \"cooler_eeprom_offsets\", \"sub_map\": {\"ENABLE_OFFSET\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0\"}, \"SETPOINT_C_OFFSET\": {\"type\": \"B\", \"value\": [50], \"offset\": \"1\"}}, \"offset\": \"0x001A\"}}, \"tool_index\": \"1\", \"offset\": \"0x011C\"}, \"VID_PID_INFO\": {\"type\": \"HH\", \"value\": [9153, 46084], \"offset\": \"0x0044\"}, \"BUZZ_SETTINGS\": {\"eeprom_map\": \"buzz_eeprom_offsets\", \"sub_map\": {\"BASIC_BUZZ_OFFSET\": {\"type\": \"HH\", \"value\": [123, 65535], \"offset\": \"0x00\"}, \"DONE_BUZZ_OFFSET\": {\"type\": \"HH\", \"value\": [65535, 65535], \"offset\": \"0x08\"}, \"ERROR_BUZZ_OFFSET\": {\"type\": \"HH\", \"value\": [500, 65535], \"offset\": \"0x04\"}}, \"offset\": \"0x014A\"}, \"MACHINE_NAME\": {\"length\": \"16\", \"type\": \"s\", \"value\": [\"The Replicator\"], \"offset\": \"0x0022\"}, \"DIGI_POT_SETTINGS\": {\"type\": \"BBBBB\", \"value\": [118, 118, 40, 118, 118], \"offset\": \"0x0006\"}, \"BOT_STATUS_BYTES\": {\"type\": \"BB\", \"value\": [255, 255], \"offset\": \"0x018A\"}, \"UUID\": {\"type\": \"B\", \"value\": [255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255], \"mult\": \"16\", \"offset\": \"0x01A4\"}, \"AXIS_HOME_DIRECTION\": {\"type\": \"B\", \"value\": [27], \"offset\": \"0x000C\"}, \"AXIS_LENGTHS\": {\"type\": \"IIIII\", \"value\": [10685, 6966, 60000, 9627520, 9627520], \"offset\": \"0x018C\"}, \"FIRST_BOOT_FLAG\": {\"type\": \"B\", \"value\": [1], \"offset\": \"0x0156\"}, \"COMMIT_VERSION\": {\"type\": \"H\", \"value\": [65535], \"offset\": \"0x004A\"}, \"TOOLHEAD_OFFSET_SETTINGS\": {\"type\": \"iii\", \"value\": [31066, 0, 0], \"offset\": \"0x0162\"}}}";
}

void EepromMapPrivateTestCase::tearDown(void)
{
}
}
