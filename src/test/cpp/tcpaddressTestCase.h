#ifndef TCPADDRESS_TEST_CASE_H
#define TCPADDRESS_TEST_CASE_H

#include <cppunit/extensions/HelperMacros.h>
#include <conveyor/tcpaddress.h>

class TcpAddressTestCase : public CPPUNIT_NS::TestFixture
{
	CPPUNIT_TEST_SUITE(TcpAddressTestCase);
	
	CPPUNIT_TEST(accessors);
	CPPUNIT_TEST(makeConnection);
	CPPUNIT_TEST(failConnection);

	CPPUNIT_TEST_SUITE_END();

public:

	void setUp();

	void accessors();
	void makeConnection();
	void failConnection();

private:
	conveyor::TcpAddress *m_good;
	conveyor::TcpAddress *m_badhost;
	conveyor::TcpAddress *m_badport;
};

#endif
