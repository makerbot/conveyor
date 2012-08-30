#ifndef EEPROM_MAP_TEST_CASE_H
#define EEPROM_MAP_TEST_CASE_H

#include <cppunit/extensions/HelperMacros.h>

#include "../../main/cpp/eeprommapprivate.h"

namespace conveyor
{
class EepromMapPrivateTestCase : public CPPUNIT_NS::TestFixture
{
	CPPUNIT_TEST_SUITE(EepromMapPrivateTestCase);
	
	CPPUNIT_TEST(testSplitPathNoSubMap);
  CPPUNIT_TEST(testSplitPathSubMap);
  CPPUNIT_TEST(testGetSubMapTopLevelEntry);
  CPPUNIT_TEST(testGetSubMapWithSubMap);
  CPPUNIT_TEST(testGetEepromMap);
  CPPUNIT_TEST(testSetString);
  CPPUNIT_TEST(testSetInt);
  CPPUNIT_TEST(testGetString);
  CPPUNIT_TEST(testGetInt);

	CPPUNIT_TEST_SUITE_END();

public:
	void setUp(void);
  void tearDown(void);
  
  void testSplitPathNoSubMap(void);
  void testSplitPathSubMap(void);
  void testGetSubMapTopLevelEntry(void);
  void testGetSubMapWithSubMap(void);
  void testGetEepromMap(void);
  void testSetString(void);
  void testSetInt(void);
  void testGetString(void);
  void testGetInt(void);

private:
  EepromMapPrivate eepromMap;    
};
}
#endif
