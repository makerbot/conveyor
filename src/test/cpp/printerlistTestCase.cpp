#include "printerlistTestCase.h"

#include <iostream>

CPPUNIT_TEST_SUITE_REGISTRATION(PrinterListTestCase);

void
PrinterListTestCase::setUp()
{
    // this never gets deleted.
    m_conveyor = conveyor::Conveyor::connectToDaemon(
                conveyor::Address::defaultAddress());
}

void
PrinterListTestCase::printersConnectedTest()
{
    std::cout << "Testing that a printers request does not throw an exception:";
    try
    {
        m_conveyor->printers();
    }
    catch(...)
    {
        CPPUNIT_ASSERT(false);
    }
    CPPUNIT_ASSERT(true);
}
