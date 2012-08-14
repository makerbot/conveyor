#include "SampleTestCase.h"
#include <iostream>

CPPUNIT_TEST_SUITE_REGISTRATION(SampleTestCase);


using namespace std;

void SampleTestCase::setUp() {
	cout << "setup" << endl;
}

void SampleTestCase::sampleTest() {
	cout << "sampleTest" << endl;
	CPPUNIT_ASSERT(true);
}
void SampleTestCase::otherTest() {
	cout << "otherTest" << endl;
	CPPUNIT_ASSERT(true);
}
