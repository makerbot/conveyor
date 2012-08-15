#include "tcpaddressTestCase.h"
#include <iostream>

CPPUNIT_TEST_SUITE_REGISTRATION(TcpAddressTestCase);

#include <stdexcept>
#include <conveyor/exceptions.h>

using namespace std;
using namespace conveyor;

void TcpAddressTestCase::setUp() {
	m_good = new TcpAddress("www.makerbot.com", 80);
	m_badhost = new TcpAddress("does.not.exist", 80);
	m_badport = new TcpAddress("www.makerbot.com", 9999);
}

void TcpAddressTestCase::accessors() {
	CPPUNIT_ASSERT_EQUAL(m_good->host(), string("www.makerbot.com"));
	CPPUNIT_ASSERT_EQUAL(m_good->port(), 80);
}

void TcpAddressTestCase::makeConnection() {
	Connection *conn = m_good->createConnection();
	CPPUNIT_ASSERT(conn != NULL);
}

void TcpAddressTestCase::failConnection() {
	CPPUNIT_ASSERT_THROW(m_badhost->createConnection(), HostLookupError);
	CPPUNIT_ASSERT_THROW(m_badport->createConnection(), SocketConnectError);
}
