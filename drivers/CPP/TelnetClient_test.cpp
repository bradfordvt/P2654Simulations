/*
 * TelnetClient_test.cpp
 *
 *  Created on: Mar 22, 2020
 *      Author: bvt
 */

#include "TelnetClient.hpp"

#include <iostream>
#include <string>
#include <list>
#include <cppunit/TestCase.h>
#include <cppunit/TestFixture.h>
#include <cppunit/ui/text/TextTestRunner.h>
#include <cppunit/extensions/HelperMacros.h>
#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/TestResult.h>
#include <cppunit/TestResultCollector.h>
#include <cppunit/TestRunner.h>
#include <cppunit/BriefTestProgressListener.h>
#include <cppunit/CompilerOutputter.h>
#include <cppunit/XmlOutputter.h>
#include <netinet/in.h>
#include <time.h>


using namespace CppUnit;
using namespace std;

//-----------------------------------------------------------------------------

namespace telnetclient {

class TestTelnetClient : public CppUnit::TestFixture
{
    CPPUNIT_TEST_SUITE(TestTelnetClient);
    // CPPUNIT_TEST(test_tc001);
    // CPPUNIT_TEST(test_tc002);
    CPPUNIT_TEST(test_tc003);
    CPPUNIT_TEST_SUITE_END();

public:
    void setUp(void);
    void tearDown(void);

protected:
    void test_tc001(void);
    void test_tc002(void);
    void test_tc003(void);

private:

    TelnetClient *mTCTestObj;
};

//-----------------------------------------------------------------------------

void
TestTelnetClient::test_tc001(void)
{
	try {
		const char* host = "127.0.0.1";
		int port = 5023;
		char resp[512];
		mTCTestObj->open(host, port);
		char buffer[2048];
		const char *rsp = mTCTestObj->read_all();
		printf("%s", rsp);
		mTCTestObj->close();
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestTelnetClient::test_tc002(void)
{
	try {
		const char* host = "127.0.0.1";
		int port = 5023;
		char resp[512];
		mTCTestObj->open(host, port);
		char buffer[2048];
		const char *rsp = mTCTestObj->read_some();
		printf("%s", rsp);
		mTCTestObj->write("EXIT\r\n");
		rsp = mTCTestObj->read_until("Goodbye");
		printf("%s", rsp);
		mTCTestObj->close();
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestTelnetClient::test_tc003(void)
{
	try {
		const char* host = "127.0.0.1";
		int port = 5023;
		char resp[512];
		mTCTestObj->open(host, port);
		char buffer[2048];
		sleep(1);
		const char *rsp = mTCTestObj->read_until("P2654> ");
		printf("%s", rsp);
		mTCTestObj->write("STARTSIM SPITest\n");
		sleep(0.1);
		rsp = mTCTestObj->read_until("OK\r\n");
		printf("%s", rsp);
		mTCTestObj->write("STOPSIM\n");
		sleep(0.1);
		rsp = mTCTestObj->read_until("OK\r\n");
		printf("%s", rsp);
		mTCTestObj->write("EXIT\r\n");
		sleep(0.1);
		rsp = mTCTestObj->read_until("Goodbye");
		printf("%s", rsp);
		mTCTestObj->close();
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void TestTelnetClient::setUp(void)
{
	try {
    	mTCTestObj = new TelnetClient();
    } catch(std::exception e) {
        printf("%s", e.what());
    } catch(...) {
        printf("Exception detected!");
    }
}

void TestTelnetClient::tearDown(void)
{
    delete mTCTestObj;
}

} /* namespace telnetclient */

using namespace telnetclient;
//-----------------------------------------------------------------------------

CPPUNIT_TEST_SUITE_REGISTRATION( TestTelnetClient );

int main(int argc, char* argv[])
{
	try {
		// informs test-listener about testresults
		CPPUNIT_NS::TestResult testresult;

		// register listener for collecting the test-results
		CPPUNIT_NS::TestResultCollector collectedresults;
		testresult.addListener (&collectedresults);

		// register listener for per-test progress output
		CPPUNIT_NS::BriefTestProgressListener progress;
		testresult.addListener (&progress);

		// insert test-suite at test-runner by registry
		CPPUNIT_NS::TestRunner testrunner;
		testrunner.addTest (CPPUNIT_NS::TestFactoryRegistry::getRegistry().makeTest ());
		testrunner.run(testresult);

		// output results in compiler-format
		CPPUNIT_NS::CompilerOutputter compileroutputter(&collectedresults, std::cerr);
		compileroutputter.write ();

		// Output XML for Jenkins CPPunit plugin
		ofstream xmlFileOut("cppTestTelnetClientResults.xml");
		XmlOutputter xmlOut(&collectedresults, xmlFileOut);
		xmlOut.write();

		// return 0 if tests were successful
		return collectedresults.wasSuccessful() ? 0 : 1;
	} catch(std::exception e) {
		printf("%s", e.what());
		return -1;
	}
	return 0;
}
