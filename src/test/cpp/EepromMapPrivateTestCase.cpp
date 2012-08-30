#include "SampleTestCase.h"
#include <fstream>
#include <QString>
#include <QStringList>
#include <vector>
#include <json/reader.h>
#include <json/value.h>


#include "EepromMapPrivateTestCase.h"
#include "../../main/cpp/eeprommapprivate.cpp"




namespace conveyor
{

CPPUNIT_TEST_SUITE_REGISTRATION(EepromMapPrivateTestCase);

void EepromMapPrivateTestCase::setUp(void)
{
  std::ifstream t("test_eeprom_map.json");
  std::string str((std::istreambuf_iterator<char>(t)),
                  std::istreambuf_iterator<char>());
  Json::Value root;
  Json::Reader reader; 
  reader.parse(str, root);
  this->eepromMap = EepromMapPrivate(root);
}

void EepromMapPrivateTestCase::tearDown(void)
{
}

void EepromMapPrivateTestCase::testSplitPathNoSubMap(void)
{
  QString path = QString("MACHINE_NAME");
  QStringList expectedPath = QStringList(QString("MACHINE_NAME"));
  QStringList gotPath = this->eepromMap.splitPath(path);
  CPPUNIT_ASSERT(expectedPath == gotPath);
}

void EepromMapPrivateTestCase::testSplitPathSubMap(void)
{
  QString path = QString("ACCELERATION_SETTINGS/DEFAULTS_FLAG");
  QStringList expectedPath = (QStringList() << "ACCELERATION_SETTINGS" << "DEFAULTS_FLAG");
  QStringList gotPath = this->eepromMap.splitPath(path);
  CPPUNIT_ASSERT(expectedPath == gotPath);
}

void EepromMapPrivateTestCase::testGetSubMapTopLevelEntry(void)
{
  std::ifstream t("test_eeprom_map.json");
  std::string str((std::istreambuf_iterator<char>(t)),
                  std::istreambuf_iterator<char>());
  Json::Value root;
  Json::Reader reader; 
  reader.parse(str, root);
  QStringList path = QStringList("MACHINE_NAME");
  Json::Value expectedMap = root;
  Json::Value gotMap = this->eepromMap.getSubMap(path);
  CPPUNIT_ASSERT(expectedMap == gotMap);
}

void EepromMapPrivateTestCase::testGetSubMapWithSubMap(void)
{
  std::ifstream t("test_eeprom_map.json");
  std::string str((std::istreambuf_iterator<char>(t)),
                  std::istreambuf_iterator<char>());
  Json::Value root;
  Json::Reader reader; 
  reader.parse(str, root);
  char* subMap = "ACCELERATION_SETTINGS";
  QStringList path = (QStringList() << subMap << "ACTIVE_OFFSET");
  Json::Value expectedMap = root[subMap];
  Json::Value gotMap = this->eepromMap.getSubMap(path);
  CPPUNIT_ASSERT(expectedMap == gotMap);
}

void EepromMapPrivateTestCase::testGetEepromMap(void)
{
  std::ifstream t("test_eeprom_map.json");
  std::string str((std::istreambuf_iterator<char>(t)),
                  std::istreambuf_iterator<char>());
  Json::Value root;
  Json::Reader reader; 
  reader.parse(str, root);
  Json::Value expectedMap = root;
  Json::Value gotMap = this->eepromMap.getEepromMap();
  CPPUNIT_ASSERT(expectedMap == gotMap);
}

void EepromMapPrivateTestCase::testSetString(void)
{
  //Check that MACHINE_NAME starts out correctly
  Json::Value nameValues = this->eepromMap.getEepromMap()["MACHINE_NAME"]["value"];
  QString currentNameInMap = QString(nameValues[0].asCString());
  QString currentName = QString("The Replicator");
  CPPUNIT_ASSERT(currentName == currentNameInMap);

  //Change the name
  QString newName = QString("the_awesomecator");
  std::vector<QString> newValues;
  newValues.push_back(newName);  
  QString path = QString("MACHINE_NAME");
  this->eepromMap.setString(path, newValues);
  Json::Value gotValues = this->eepromMap.getEepromMap()["MACHINE_NAME"]["value"];
  QString gotNewName = QString(gotValues[0].asCString());
  CPPUNIT_ASSERT(newName == gotNewName);
}

void EepromMapPrivateTestCase::testSetInt(void)
{
  //Check that T0_DATA_BASE/BACKOFF_FORWARD_TIME starts out correctly
  Json::Value timeValues = this->eepromMap.getEepromMap()["MACHINE_NAME"]["value"];
  int currentBackoffTime = timeValues[0].asInt();
  int expectedBackoffTime = 500;
  CPPUNIT_ASSERT_EQUAL(currentBackoffTime, expectedBackoffTime);
  
  //Change T0_DATA_BASE/BACKOFF_FORWARD_TIME 
  int newBackoffTime = 123;
  std::vector<int> newValues;
  newValues.push_back(newBackoffTime);
  QString path = QString("T0_DATA_BASE/BACKOFF_FORWARD_TIME");
  this->eepromMap.setInt(path, newValues);
  Json::Value gotTimeValues = this->eepromMap.getEepromMap()["MACHINE_NAME"]["value"];
  int gotBackoffTime = timeValues[0].asInt();
  CPPUNIT_ASSERT_EQUAL(newBackoffTime, gotBackoffTime);
}

void EepromMapPrivateTestCase::testGetString(void)
{
  Json::Value nameValues = this->eepromMap.getEepromMap()["MACHINE_NAME"]["value"];
  QString expectedName = QString(nameValues[0].asCString());
  QString path = QString("MACHINE_NAME");
  std::vector<QString> gotValues = this->eepromMap.getString(path);
  QString gotName = gotValues[0];
  CPPUNIT_ASSERT(expectedName == gotName);
}

void EepromMapPrivateTestCase::testGetInt(void)
{
  Json::Value backoffForwardTimeValues = this->eepromMap.getEepromMap()["T0_DATA_BASE"]["sub_map"]["BACKOFF_FORWARD_TIME"]["value"];
  int expectedBackoffForwardTime = backoffForwardTimeValues[0].asInt();
  QString path = QString("T0_DATA_BASE/BACKOFF_FORWARD_TIME");
  std::vector<int> gotValues = this->eepromMap.getInt(path);
  int gotBackoffForwardTime = gotValues[0];
  CPPUNIT_ASSERT_EQUAL(expectedBackoffForwardTime, gotBackoffForwardTime);
}
}
