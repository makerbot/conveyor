#ifndef SAMPLE_TEST_CASE_H
#define SAMPLE_TEST_CASE_H

#include <cppunit/extensions/HelperMacros.h>

class SampleTestCase : public CPPUNIT_NS::TestFixture
{
	CPPUNIT_TEST_SUITE(SampleTestCase);
	
	CPPUNIT_TEST(sampleTest);
	CPPUNIT_TEST(otherTest);

	CPPUNIT_TEST_SUITE_END();

public:

	void setUp();


	void sampleTest();
	void otherTest();
};

#endif
