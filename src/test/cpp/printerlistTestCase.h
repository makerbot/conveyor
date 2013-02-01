#ifndef PRINTERLIST_TEST_CASE_H
#define PRINTERLIST_TEST_CASE_H

#include <cppunit/extensions/HelperMacros.h>

class PrinterListTestCase : public CPPUNIT_NS::TestFixture
{
    CPPUNIT_TEST_SUITE(PrinterListTestCase);
	
	CPPUNIT_TEST(printersConnectedTest);

	CPPUNIT_TEST_SUITE_END();

public:

    void setUp();

    void printersConnectedTest();

    conveyor::Conveyor * m_conveyor;
};

#endif
