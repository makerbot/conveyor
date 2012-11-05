#ifndef EEPROM_MAP_PRIVATE_TEST_CASE_H
#define EEPROM_MAP_PRIVATE_TEST_CASE_H

#include <cppunit/extensions/HelperMacros.h>

#include "../../main/cpp/eeprommapprivate.h"

namespace conveyor
{
class EepromMapPrivateTestCase : public CPPUNIT_NS::TestFixture
{
	CPPUNIT_TEST_SUITE(EepromMapPrivateTestCase);
	
	CPPUNIT_TEST(testSplitPathNoSubMap);
  CPPUNIT_TEST(testSplitPathSubMap);
  CPPUNIT_TEST(testGetEepromMap);
  CPPUNIT_TEST(testSetString);
  CPPUNIT_TEST(testSetInt);
  CPPUNIT_TEST(testSetFloat);
  CPPUNIT_TEST(testGetString);
  CPPUNIT_TEST(testGetInt);
  CPPUNIT_TEST(testGetEntryTopLevelEntry);
  CPPUNIT_TEST(testGetEntryWithSubMap);
  CPPUNIT_TEST(testGetFloat);

	CPPUNIT_TEST_SUITE_END();

public:
	void setUp(void);
  void tearDown(void);
  
  void testSplitPathNoSubMap(void);
  void testSplitPathSubMap(void);
  void testGetEntryTopLevelEntry(void);
  void testGetEntryWithSubMap(void);
  void testGetEepromMap(void);
  void testSetString(void);
  void testSetInt(void);
  void testSetFloat(void);
  void testGetString(void);
  void testGetInt(void);
  void testGetFloat(void);

private:
  EepromMapPrivate* createEepromMap(void);
  std::string eeprom_json;

};
}
#endif
