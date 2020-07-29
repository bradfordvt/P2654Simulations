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
// #include <netinet/in.h>

#ifdef __MINGW32__
#define sleep(seconds) Sleep((seconds)*1000)
#elif _MSC_VER >= 1900
#define sleep(seconds) Sleep((seconds)*1000)
#include "pch.h"
#endif


#include "atesim.hpp"

using namespace CppUnit;
using namespace std;

//-----------------------------------------------------------------------------

class TestSimService : public CppUnit::TestFixture
{
    CPPUNIT_TEST_SUITE(TestSimService);
    CPPUNIT_TEST(test_simservicetelnetlib001);
    CPPUNIT_TEST(test_simservicetelnetlib002);
    CPPUNIT_TEST(test_simservicetelnetlib003);
    CPPUNIT_TEST(test_simservicetelnetlib004);
    CPPUNIT_TEST(test_simservicetelnetlib005);
    CPPUNIT_TEST(test_simservicetelnetclient001);
    CPPUNIT_TEST(test_simserviceATE001);
    CPPUNIT_TEST(test_simserviceATE002);
    CPPUNIT_TEST(test_simserviceATE003);
    CPPUNIT_TEST(test_simserviceATE004);
    CPPUNIT_TEST(test_simserviceATE005);
    CPPUNIT_TEST_SUITE_END();

public:
    void setUp(void);
    void tearDown(void);

protected:
    void test_simservicetelnetlib001(void);
    void test_simservicetelnetlib002(void);
    void test_simservicetelnetlib003(void);
    void test_simservicetelnetlib004(void);
    void test_simservicetelnetlib005(void);
    void test_simservicetelnetclient001(void);
    void test_simserviceATE001(void);
    void test_simserviceATE002(void);
    void test_simserviceATE003(void);
    void test_simserviceATE004(void);
    void test_simserviceATE005(void);

private:

    TelnetClient *mTCTestObj;
    ATETelnetClient *mATETCTestObj;
    ATE *mATETestObj;
    JTAGController *mJTAGControllerTestObj;
    I2CController *mI2CControllerTestObj;
    SPIController *mSPIControllerTestObj;
};

//-----------------------------------------------------------------------------

void
TestSimService::test_simservicetelnetlib001(void)
{
	try {
        const char* host = "127.0.0.1";
        int port = 5023;
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mTCTestObj = new TelnetClient();
        mTCTestObj->set_debug_level(1);
        mTCTestObj->open(host, port);
		sleep(1);
		rsp = mTCTestObj->read_until("P2654> ", 60);
		printf("%s", rsp);
        printf("Before EXIT()\n");
        fflush(stderr);
		mTCTestObj->write("EXIT\n", 5);
		sleep(5);
		rsp = mTCTestObj->read_until("Goodbye", 60);
		printf("%s\n", rsp);
		mTCTestObj->close();
		delete mTCTestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simservicetelnetlib002(void)
{
	try {
        const char* host = "127.0.0.1";
        int port = 5023;
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mTCTestObj = new TelnetClient();
        mTCTestObj->set_debug_level(1);
        mTCTestObj->open(host, port);
		sleep(1);
		rsp = mTCTestObj->read_until("P2654> ", 60);
		printf("%s", rsp);
        sleep(1);
        printf("Before STARTSIM()\n");
        fflush(stderr);
        mTCTestObj->write("STARTSIM SPITest\n");
        sleep(8);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s", rsp);
        printf("Before STOPSIM()\n");
        fflush(stderr);
		mTCTestObj->write("STOPSIM\n");
		sleep(2);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
        printf("Before EXIT()\n");
        fflush(stderr);
		mTCTestObj->write("EXIT\n");
		sleep(5);
		rsp = mTCTestObj->read_until("Goodbye", 60);
		printf("%s\n", rsp);
		mTCTestObj->close();
		delete mTCTestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simservicetelnetlib003(void)
{
	try {
        const char* host = "127.0.0.1";
        int port = 5023;
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mTCTestObj = new TelnetClient();
        mTCTestObj->set_debug_level(1);
        mTCTestObj->open(host, port);
		sleep(8);
		rsp = mTCTestObj->read_until("P2654> ", 60);
		printf("%s", rsp);
        sleep(1);
        printf("Before STARTSIM()\n");
        fflush(stderr);
        mTCTestObj->write("STARTSIM SPITest\n");
        sleep(8);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before STOPSIM()\n");
        fflush(stderr);
		mTCTestObj->write("STOPSIM\n");
		sleep(2);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before EXIT()\n");
        fflush(stderr);
		mTCTestObj->write("EXIT\n");
		sleep(5);
		rsp = mTCTestObj->read_until("Goodbye", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
		mTCTestObj->close();
		delete mTCTestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simservicetelnetlib004(void)
{
	try {
        const char* host = "127.0.0.1";
        int port = 5023;
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mTCTestObj = new TelnetClient();
        mTCTestObj->set_debug_level(1);
        mTCTestObj->open(host, port);
		sleep(8);
		rsp = mTCTestObj->read_until("P2654> ", 60);
		printf("%s", rsp);
        sleep(1);
        printf("Before STARTSIM()\n");
        fflush(stderr);
        mTCTestObj->write("STARTSIM SPITest\n");
        sleep(8);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before STOPSIM()\n");
        fflush(stderr);
		mTCTestObj->write("STOPSIM\n");
		sleep(2);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before EXIT()\n");
        fflush(stderr);
		mTCTestObj->write("EXIT\n");
		sleep(5);
		rsp = mTCTestObj->read_until("Goodbye", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
		mTCTestObj->close();
		delete mTCTestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simservicetelnetlib005(void)
{
	try {
        const char* host = "127.0.0.1";
        int port = 5023;
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mTCTestObj = new TelnetClient();
        mTCTestObj->set_debug_level(1);
        mTCTestObj->open(host, port);
		sleep(8);
		rsp = mTCTestObj->read_until("P2654> ", 60);
		printf("%s", rsp);
        sleep(1);
        printf("Before STARTSIM()\n");
        fflush(stderr);
        mTCTestObj->write("STARTSIM SPITest\n");
        sleep(8);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before STOPSIM()\n");
        fflush(stderr);
		mTCTestObj->write("STOPSIM\n");
		sleep(2);
		rsp = mTCTestObj->read_until("OK\r\n", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before EXIT()\n");
        fflush(stderr);
		mTCTestObj->write("EXIT\n");
		sleep(5);
		rsp = mTCTestObj->read_until("Goodbye", 60);
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
		mTCTestObj->close();
		delete mTCTestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simservicetelnetclient001(void)
{
	try {
        const char* host = "127.0.0.1";
        int port = 5023;
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mATETCTestObj = new ATETelnetClient();
        mATETCTestObj->connect(host, port);
        printf("Before STARTSIM()\n");
        fflush(stderr);
        mATETCTestObj->write("STARTSIM SPITest\n");
        sleep(8);
		rsp = mATETCTestObj->read_until("OK\r\n");
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before STOPSIM()\n");
        fflush(stderr);
        mATETCTestObj->write("STOPSIM\n");
		sleep(2);
		rsp = mATETCTestObj->read_until("OK\r\n");
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
        printf("Before EXIT()\n");
        fflush(stderr);
        mATETCTestObj->write("EXIT\n");
		sleep(5);
		rsp = mATETCTestObj->read_until("Goodbye");
		printf("%s\n", rsp);
		CPPUNIT_ASSERT(strlen(rsp) > 0);
		mATETCTestObj->close();
		delete mATETCTestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simserviceATE001(void)
{
	try {
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mATETestObj = new ATE("127.0.0.1", 5023);
        sleep(1);
        const char* board = "SPITest";
        CPPUNIT_ASSERT(mATETestObj->connect(board));
        CPPUNIT_ASSERT(mATETestObj->terminate());
		mATETestObj->close();
		delete mATETestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simserviceATE002(void)
{
	try {
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mATETestObj = new ATE("127.0.0.1", 5023);
        sleep(1);
        const char* board = "SPITest";
        CPPUNIT_ASSERT(mATETestObj->connect(board));
		// GPIO Test
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000000));
		CPPUNIT_ASSERT(mATETestObj->read(0x00001800));
		CPPUNIT_ASSERT(mATETestObj->get_value() == 0x00000000);
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000015));
		CPPUNIT_ASSERT(mATETestObj->read(0x00001800));
		CPPUNIT_ASSERT(mATETestObj->get_value() == 0x00150015);
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x0000000A));
		CPPUNIT_ASSERT(mATETestObj->read(0x00001800));
		CPPUNIT_ASSERT(mATETestObj->get_value() == 0x000A000A);
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000000));
		CPPUNIT_ASSERT(mATETestObj->read(0x00001800));
		CPPUNIT_ASSERT(mATETestObj->get_value() == 0x00000000);
		sleep(0.05);
        CPPUNIT_ASSERT(mATETestObj->terminate());
		mATETestObj->close();
		delete mATETestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simserviceATE003(void)
{
	try {
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mATETestObj = new ATE("127.0.0.1", 5023);
        sleep(1);
        const char* board = "SPITest";
        CPPUNIT_ASSERT(mATETestObj->connect(board));
		mJTAGControllerTestObj = new JTAGController(*mATETestObj);
		// JTAG Test
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000001));  // Turn on WHITE LED to indicate scan start
		std::string tdo = mJTAGControllerTestObj->scan_ir(8, std::string("55"));
		CPPUNIT_ASSERT(tdo == "55");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000002));  // Turn on RED LED to indicate scan start
		tdo = mJTAGControllerTestObj->scan_ir(12, std::string("0A55"));
		CPPUNIT_ASSERT(tdo == "A55");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000004));  // Turn on GREEN LED to indicate scan start
		tdo = mJTAGControllerTestObj->scan_ir(12, std::string("5AA"));
		CPPUNIT_ASSERT(tdo == "5AA");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000008));  // Turn on YELLOW LED to indicate scan start
		tdo = mJTAGControllerTestObj->scan_dr(8, std::string("55"));
		CPPUNIT_ASSERT(tdo == "55");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000010));  // Turn on BLUE LED to indicate scan start
		tdo = mJTAGControllerTestObj->scan_dr(12, std::string("AAA"));
		CPPUNIT_ASSERT(tdo == "AAA");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000011));  // Turn on BLUE & WHITE LEDs to indicate scan start
		tdo = mJTAGControllerTestObj->scan_dr(12, std::string("A55"));
		CPPUNIT_ASSERT(tdo == "A55");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000012));  // Turn on BLUE & RED LEDs to indicate scan start
		tdo = mJTAGControllerTestObj->scan_dr(12, std::string("5AA"));
		CPPUNIT_ASSERT(tdo == "5AA");
		CPPUNIT_ASSERT(mATETestObj->write(0x00001800, 0x00000014));  // Turn on BLUE & GREEN LEDs to indicate scan start
		tdo = mJTAGControllerTestObj->scan_dr(16 * 4, std::string("0123456789ABCDEF"));
		CPPUNIT_ASSERT(tdo == "0123456789ABCDEF");
		sleep(0.05);
        CPPUNIT_ASSERT(mATETestObj->terminate());
		mATETestObj->close();
		delete mJTAGControllerTestObj;
		delete mATETestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simserviceATE004(void)
{
	try {
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mATETestObj = new ATE("127.0.0.1", 5023);
        sleep(0.05);
        const char* board = "SPITest";
        CPPUNIT_ASSERT(mATETestObj->connect(board));
		mI2CControllerTestObj = new I2CController(*mATETestObj);
		// I2C Test
		// I2C Test set i2c master clock scale reg PRER = (48MHz / (5 * 400KHz) ) - 1
		mI2CControllerTestObj->i2c_write_reg(0x3C, 0x01, 0xA5);
		CPPUNIT_ASSERT(mI2CControllerTestObj->i2c_read_reg(0x3C, 0x01) == 0xA5);

		mI2CControllerTestObj->i2c_multibyte_write(0x3C, 0, 0x89abcdef);
		CPPUNIT_ASSERT(mI2CControllerTestObj->i2c_multibyte_read(0x3C, 0) == 0x89abcdef);
		CPPUNIT_ASSERT(mI2CControllerTestObj->i2c_multibyte_read(0x3C, 4) == 0x12345678);
		sleep(0.05);
        CPPUNIT_ASSERT(mATETestObj->terminate());
		mATETestObj->close();
		delete mI2CControllerTestObj;
		delete mATETestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void
TestSimService::test_simserviceATE005(void)
{
	try {
        char resp[512];
        const char* rsp;
        char buffer[2048];
        mATETestObj = new ATE("127.0.0.1", 5023);
        sleep(1);
        const char* board = "SPITest";
        CPPUNIT_ASSERT(mATETestObj->connect(board));
		mSPIControllerTestObj = new SPIController(*mATETestObj);
		// SPI Test
		mSPIControllerTestObj->spi_write(0x01345678);
		mSPIControllerTestObj->spi_write(0x00BADEDA);
		CPPUNIT_ASSERT(mSPIControllerTestObj->spi_read() == 0x01345678);
		mSPIControllerTestObj->spi_write(0x02BEEFED);
		CPPUNIT_ASSERT(mSPIControllerTestObj->spi_read() == 0x00BADEDA);
		mSPIControllerTestObj->spi_write(0x01345678);
		CPPUNIT_ASSERT(mSPIControllerTestObj->spi_read() == 0x02BEEFED);
		sleep(0.05);
        CPPUNIT_ASSERT(mATETestObj->terminate());
		mATETestObj->close();
		delete mSPIControllerTestObj;
		delete mATETestObj;
	} catch(TelnetClient::IOError e) {
		printf("ERROR: %s\n", e.what());
		CPPUNIT_ASSERT(0 != 0);
	}
}

void TestSimService::setUp(void)
{
	/*
try {
    mTCTestObj = new TelnetClient("127.0.0.1", 5023);
    mATETCTestObj = new ATETelnetClient();
    mATETestObj = new ATE("127.0.0.1", 5023);
    mJTAGControllerTestObj = new JTAGController(*mATETestObj);
    mI2CControllerTestObj = new I2CController(*mATETestObj);
    mSPIControllerTestObj = new SPIController(*mATETestObj);
    } catch(std::exception e) {
        printf("%s", e.what());
    } catch(...) {
        printf("Exception detected!");
    }
    */
}

void TestSimService::tearDown(void)
{
	/*
    delete mTCTestObj;
    delete mATETCTestObj;
    delete mJTAGControllerTestObj;
    delete mI2CControllerTestObj;
    delete mSPIControllerTestObj;
    delete mATETestObj;
    */
}

//-----------------------------------------------------------------------------

CPPUNIT_TEST_SUITE_REGISTRATION( TestSimService );

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
    ofstream xmlFileOut("cppTestSimServiceResults.xml");
    XmlOutputter xmlOut(&collectedresults, xmlFileOut);
    xmlOut.write();

    // return 0 if tests were successful
    return collectedresults.wasSuccessful() ? 0 : 1;
} catch(std::exception e) {
    printf("%s\n", e.what());
}
}
