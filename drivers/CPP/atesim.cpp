#include <atesim.hpp>
#include <time.h>
#include<algorithm>
#include <inttypes.h>

void ATETelnetClient::connect(const char* ip, int port) {
	sleep(1);
    try {
    	tn_inst.open(ip, port);
    } catch(TelnetClient::IOError e) {
    	tn_inst.close();
    	sleep(1);
    	tn_inst.open(ip, port);
    }
}

ATE::ATE(const char* ip, int port) : ip(ip), port(port), tn_inst() {
    memset(resp, 0, sizeof(resp));
    value = 0L;
}

ATE::~ATE() {
	tn_inst.close();
}

bool ATE::connect(const char* board) {
    /* Start up the simserver application in the background */
    /* Create the TelnetClient interface to the simserver */
    /* Connect to the simserver */
    tn_inst.connect(ip.c_str(), port);
    /* Send command to start up the simulation of the prescribed board */
    char buffer[50];
    sleep(0.5);
    sprintf(buffer, "STARTSIM %s\r\n", board);
    tn_inst.write(buffer);
    sleep(1);
    const char* rsp;
    rsp = tn_inst.read_until("OK\r\n");
    int rlen = strlen(rsp);
    if(rlen > 0) {
        strncpy(resp, rsp, std::min(rlen, 511));
        memset(&resp[std::min(rlen, 511)], 0, 512 - std::min(rlen, 511));
        return true;
    }
    memset(resp, 0, sizeof(resp));
    return false;
}

bool ATE::write(std::uint32_t adr, std::uint32_t data) {
    char buffer[50];
    sprintf(buffer, "MW 0x%08" PRIx32 " 0x%08" PRIx32 "\r\n", adr, data);
    tn_inst.write(buffer);
    sleep(0.005);
    const char* rsp;
    rsp = tn_inst.read_until("OK\r\n");
    int rlen = strlen(rsp);
    if(rlen > 0) {
        strncpy(resp, rsp, std::min(rlen, 511));
        memset(&resp[std::min(rlen, 511)], 0, 512 - std::min(rlen, 511));
        return true;
    }
    memset(resp, 0, sizeof(resp));
    return false;
}

bool ATE::read(std::uint32_t adr) {
    char buffer[50];
    sprintf(buffer, "MR 0x%0" PRIx32 "\r\n", adr);
    tn_inst.write(buffer);
    sleep(0.005);
    const char* rsp;
    rsp = tn_inst.read_until("OK\r\n");
    int rlen = strlen(rsp);
    if(rlen > 0) {
        strncpy(resp, rsp, std::min(rlen, 511));
        memset(&resp[std::min(rlen, 511)], 0, 512 - std::min(rlen, 511));
        char* chars_array = strtok(resp, " ");
        value = strtoul (chars_array, NULL, 16);
        return true;
    }
    memset(resp, 0, sizeof(resp));
    return false;
}

bool ATE::terminate() {
    tn_inst.write("STOPSIM\r\n");
    sleep(0.005);
    const char* rsp;
    rsp = tn_inst.read_until("OK\r\n");
    int rlen = strlen(rsp);
    if(rlen > 0) {
        strncpy(resp, rsp, std::min(rlen, 511));
        memset(&resp[std::min(rlen, 511)], 0, 512 - std::min(rlen, 511));
        if(strstr(resp, "Simulation has stopped.") != NULL) {
            return true;
        }
        else {
            return false;
        }
    }
    memset(resp, 0, sizeof(resp));
    return false;
}

bool ATE::close() {
    tn_inst.write("EXIT\r\n");
    sleep(0.005);
    const char* rsp;
    rsp = tn_inst.read_some();
    tn_inst.close();
    int rlen = strlen(rsp);
    if(rlen > 0) {
        strncpy(resp, rsp, std::min(rlen, 511));
        memset(&resp[std::min(rlen, 511)], 0, 512 - std::min(rlen, 511));
        if(strstr(resp, "Goodbye") != NULL) {
            return true;
        }
        else {
            return false;
        }
    }
    memset(resp, 0, sizeof(resp));
    return false;
}

void JTAGController::__write_vector_segment(std::uint32_t adr, byte data) {
    std::uint32_t wb_addr = 0x00001000 + adr;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)data & 0x000000FF);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

byte JTAGController::__read_vector_segment(std::uint32_t adr) {
    std::uint32_t wb_addr = 0x00001000 + adr;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value();
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void JTAGController::__set_bit_count(std::uint16_t count) {
    std::uint32_t wb_addr = 0x00001000 + 0x402;
    bool ret = ate_inst.write(wb_addr, count & 0x0000FFFF);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

void JTAGController::__set_state_start(std::uint8_t start) {
    std::uint32_t wb_addr = 0x00001000 + 0x400;
    bool ret = ate_inst.write(wb_addr, start & 0x0000000F);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

void JTAGController::__set_state_end(std::uint8_t end) {
    std::uint32_t wb_addr = 0x00001000 + 0x401;
    bool ret = ate_inst.write(wb_addr, end & 0x0000000F);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

void JTAGController::__set_control_register(std::uint8_t value) {
    std::uint32_t wb_addr = 0x00001000 + 0x403;
    bool ret = ate_inst.write(wb_addr, value & 0x00000001);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

std::uint8_t JTAGController::__get_status_register() {
    std::uint32_t wb_addr = 0x00001000 + 0x404;
    if(ate_inst.read(wb_addr) & 0x1) {
        return ate_inst.get_value();
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

byte_array JTAGController::__scan_vector(byte_array& tdi_vector, int count, std::uint8_t start, std::uint8_t end) {
    /* Fill the JTAGCtrlMaster data buffer memory with tdi data */
    int data_width = 8;
    int addr_width = 10;
    int num_full_words = int(count / data_width);
    byte_array tdo_vector;
    tdo_vector.reserve((count + data_width - 1) / data_width);
    /*
    byte_array tdo_vector = byte_array((count + data_width - 1) / data_width, 0);
    byte_array::iterator it;
    it = tdo_vector.begin();
    */
    int remainder = count % data_width;
    uint32_t addr = 0;
    int i;
    byte data;
    for(i = 0; i < num_full_words; i++) {
        data = tdi_vector[i];
        __write_vector_segment(addr, data);
        addr += 1;
    }
    /* Now write out the remaining bits that may be a partial word in size, but a full word needs to be written */
    if(remainder > 0) {
        data = tdi_vector[num_full_words];
        __write_vector_segment(addr, data);
    }
    /* Now start the scan operation */
    __set_bit_count(count);
    __set_state_start(start);
    __set_state_end(end);
    __set_control_register(0x1);  // Start the scan
    std::uint8_t status = __get_status_register();
    while(status != 0) {
        status = __get_status_register();
    }
    __set_control_register(0x0);  // Stop the scan/Reset for next scan cycle trigger
    /* Scan completed, now fetch the captured data */
    addr = 0;
    for(i = 0; i < num_full_words; i++) {
        data = __read_vector_segment(addr);
        tdo_vector.push_back(data);
        addr += 1;
    }
    /* Now read out the remaining bits that may be a partial word in size, but a full word needs to be read */
    if(remainder > 0) {
        data = __read_vector_segment(addr);
        tdo_vector.push_back(data);
    }
    return tdo_vector;
}

byte_array JTAGController::ba_scan_ir(byte_array& tdi_vector, int count) {
    std::uint8_t start = JTAGStates::SHIFT_IR;
    std::uint8_t end = JTAGStates::RUN_TEST_IDLE;
    return __scan_vector(tdi_vector, count, start, end);
}

byte_array JTAGController::ba_scan_dr(byte_array& tdi_vector, int count) {
    std::uint8_t start = JTAGStates::SHIFT_DR;
    std::uint8_t end = JTAGStates::RUN_TEST_IDLE;
    return __scan_vector(tdi_vector, count, start, end);
}

std::string JTAGController::scan_ir(int count, std::string tdi_string) {
    if(tdi_string.length() % 2) {
        tdi_string = std::string("0") + tdi_string;
    }
    int allocated_bytes = tdi_string.length() / 2;
    // Allocate the vector space for the byte data and initialize to 0
    byte_array tdi_vector(allocated_bytes, 0);

    // Now process hex digits
    int hexdigits = tdi_string.length();
    int i = allocated_bytes*2 - hexdigits;
    for(int j = 0; j < hexdigits; j++, i++) {
        if(i % 2 == 0) {
            tdi_vector[i/2] = tdi_vector[i/2] | (__hex(tdi_string[j]) << 4);
        }
        else {
            tdi_vector[i/2] = tdi_vector[i/2] | __hex(tdi_string[j]);
        }
    }
    // Now reverse the order of the bytes to place the rightmost bits in the first byte position
    reverse(tdi_vector.begin(), tdi_vector.end());

    byte_array tdo_vector = ba_scan_ir(tdi_vector, count);
    if(tdo_vector.size() > 0) {
        reverse(tdo_vector.begin(), tdo_vector.end());
    }
    std::string tdo_string;
    for(i = 0; i < tdo_vector.size(); i++) {
        tdo_string.append(__hex_to_char(tdo_vector[i]));
    }
    if(tdo_string.length() * 4 > count) {
    	tdo_string.erase(0, 1);
    }
    return tdo_string;
}

std::string JTAGController::scan_dr(int count, std::string tdi_string) {
    if(tdi_string.length() % 2) {
        tdi_string = std::string("0") + tdi_string;
    }
    int allocated_bytes = tdi_string.length() / 2;
    // Allocate the vector space for the byte data and initialize to 0
    byte_array tdi_vector(allocated_bytes, 0);

    // Now process hex digits
    int hexdigits = tdi_string.length();
    int i = allocated_bytes*2 - hexdigits;
    for(int j = 0; j < hexdigits; j++, i++) {
        if(i % 2 == 0) {
            tdi_vector[i/2] = tdi_vector[i/2] | (__hex(tdi_string[j]) << 4);
        }
        else {
            tdi_vector[i/2] = tdi_vector[i/2] | __hex(tdi_string[j]);
        }
    }
    // Now reverse the order of the bytes to place the rightmost bits in the first byte position
    reverse(tdi_vector.begin(), tdi_vector.end());

    byte_array tdo_vector = ba_scan_dr(tdi_vector, count);
    if(tdo_vector.size() > 0) {
        reverse(tdo_vector.begin(), tdo_vector.end());
    }
    std::string tdo_string;
    for(i = 0; i < tdo_vector.size(); i++) {
        tdo_string.append(__hex_to_char(tdo_vector[i]));
    }
    if(tdo_string.length() * 4 > count) {
    	tdo_string.erase(0, 1);
    }
    return tdo_string;
}

void JTAGController::runtest(int ticks) {
    std::uint8_t start = JTAGStates::RUN_TEST_IDLE;
    std::uint8_t end = JTAGStates::RUN_TEST_IDLE;
    int blocks = ticks / 1024;
    int rem = ticks % 1024;
    for(int i = 0; i < blocks; i++) {
        /* Now start the scan operation */
        __set_bit_count(1024);
        __set_state_start(start);
        __set_state_end(end);
        __set_control_register(0x1);  // Start the scan
        std::uint8_t status = __get_status_register();
        while(status != 0) {
            status = __get_status_register();
        }
        __set_control_register(0x0);  // Stop the scan/Reset for next scan cycle trigger
    }
    /* Now start the scan operation */
    __set_bit_count(1024);
    __set_state_start(start);
    __set_state_end(end);
    __set_control_register(0x1);  // Start the scan
    std::uint8_t status = __get_status_register();
    while(status != 0) {
        status = __get_status_register();
    }
    __set_control_register(0x0);  // Stop the scan/Reset for next scan cycle trigger
}

byte JTAGController::__hex(char ch) {
    if(ch >= 'A' && ch <= 'Z') {
        return (ch - 'A') + 10;
    }
    if(ch >= '0' && ch <= '9') {
        return ch - '0';
    }
    return 0;
}

const char* JTAGController::__hex_to_char(byte data) {
    static char buffer[3];
    int i;
    for(i = 0; i < 2; i++) {
        int d = i % 2 ? data & 0xF : data >> 4;
        switch(d) {
            case 0:
                buffer[i] = '0';
                break;
            case 1:
                buffer[i] = '1';
                break;
            case 2:
                buffer[i] = '2';
                break;
            case 3:
                buffer[i] = '3';
                break;
            case 4:
                buffer[i] = '4';
                break;
            case 5:
                buffer[i] = '5';
                break;
            case 6:
                buffer[i] = '6';
                break;
            case 7:
                buffer[i] = '7';
                break;
            case 8:
                buffer[i] = '8';
                break;
            case 9:
                buffer[i] = '9';
                break;
            case 10:
                buffer[i] = 'A';
                break;
            case 11:
                buffer[i] = 'B';
                break;
            case 12:
                buffer[i] = 'C';
                break;
            case 13:
                buffer[i] = 'D';
                break;
            case 14:
                buffer[i] = 'E';
                break;
            case 15:
                buffer[i] = 'F';
                break;
        }
    }
    buffer[2] = '\0';
    return buffer;
}

void I2CController::__write_transmit_register(byte value) {
    std::uint32_t wb_addr = 0x00001C00 + 0;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)value & 0x000000FF);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

byte I2CController::__read_transmit_register() {
    std::uint32_t wb_addr = 0x00001C00 + 0;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value() & 0xFF;
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void I2CController::__write_receive_register(byte value) {
    std::uint32_t wb_addr = 0x00001C00 + 1;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)value & 0x000000FF);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

byte I2CController::__read_receive_register() {
    std::uint32_t wb_addr = 0x00001C00 + 1;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value() & 0xFF;
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void I2CController::__write_control_register(byte value) {
    std::uint32_t wb_addr = 0x00001C00 + 2;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)value & 0x000000FF);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

byte I2CController::__read_control_register() {
    std::uint32_t wb_addr = 0x00001C00 + 2;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value() & 0xFF;
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void I2CController::__write_status_register(byte value) {
    std::uint32_t wb_addr = 0x00001C00 + 3;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)value & 0x000000FF);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

byte I2CController::__read_status_register() {
    std::uint32_t wb_addr = 0x00001C00 + 3;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value() & 0xFF;
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void I2CController::i2c_write_reg(byte dev_address, byte reg_address, byte value) {
    // Write out device address
    __write_transmit_register((dev_address << 1) & 0xFE);
    __write_control_register(0x0B);  // START & WRITE & EXECUTE
    byte status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out the register index
    __write_transmit_register(reg_address);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out the data byte
    __write_transmit_register(value);
    __write_control_register(0x13);  // WRITE & EXECUTE & STOP
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
}

byte I2CController::i2c_read_reg(byte dev_address, byte reg_address) {
    // write out device address
    __write_transmit_register((dev_address << 1) & 0xFE);
    __write_control_register(0x0B);  // START & WRITE & EXECUTE
    byte status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out the register index
    __write_transmit_register(reg_address);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out device address with read
    __write_transmit_register((dev_address << 1) | 1);
    __write_control_register(0x0B);  // START & WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // read byte from slave
    __write_control_register(0x15);  // EXECUTE & MASTER_ACK & STOP
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    return __read_receive_register();
}

bool I2CController::i2c_multibyte_write(byte dev_address, byte reg_address, uint32_t data) {
    // i2c address
    __write_transmit_register((dev_address << 1) & 0xFE);
    __write_control_register(0x0B);  // START & WRITE & EXECUTE
    byte status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out the register index
    __write_transmit_register(reg_address);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // data[31:24]
    __write_transmit_register((data >> 24) & 0xFF);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // data[23:16]
    __write_transmit_register((data >> 16) & 0xFF);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // data[15:8]
    __write_transmit_register((data >> 8) & 0xFF);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // data[7:0]
    __write_transmit_register(data & 0xFF);
    __write_control_register(0x13);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    return true;
}

uint32_t I2CController::i2c_multibyte_read(byte dev_address, byte reg_address) {
    uint32_t retval = 0;
    // write out device address
    __write_transmit_register((dev_address << 1) & 0xFE);
    __write_control_register(0x0B);  // START & WRITE & EXECUTE
    byte status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out the register index
    __write_transmit_register(reg_address);
    __write_control_register(0x03);  // WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // write out device address with read
    __write_transmit_register((dev_address << 1) | 1);
    __write_control_register(0x0B);  // START & WRITE & EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    // read byte from slave data[31:24]
    __write_control_register(0x01);  // EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    byte value = __read_receive_register();
    retval = (value << 24) & 0xFF000000;

    // read byte from slave data[23:16]
    __write_control_register(0x01);  // EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    value = __read_receive_register();
    retval = retval | ((value << 16) & 0x00FF0000);

    //read byte from slave data[15:8]
    __write_control_register(0x01);  // EXECUTE
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    value = __read_receive_register();
    retval = retval | ((value << 8) & 0x0000FF00);

    // read byte from slave data[7:0]
    __write_control_register(0x15);  // EXECUTE & MASTER_ACK & STOP
    status = __read_status_register();
    while(status & 0x01) { // busy set
        status = __read_status_register();
    }
    // check for ack error
    if(status & 0x02) {
        throw AcknowledgeError("Acknowledge error detected during device address transmission.");
    }
    value = __read_receive_register();
    retval = retval | (value & 0x000000FF);
    return retval;
}

void SPIController::__spi_write_transmit_register(uint32_t value) {
    std::uint32_t wb_addr = 0x00001C00 + 0x30;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)value);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

uint32_t SPIController::__spi_read_transmit_register() {
    std::uint32_t wb_addr = 0x00001C00 + 0x30;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value();
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void SPIController::__spi_write_receive_register(uint32_t value) {
    std::uint32_t wb_addr = 0x00001C00 + 0x31;
    bool ret = ate_inst.write(wb_addr, (std::uint32_t)value);
    if(ret == false) {
        throw AcknowledgeError(std::string("Write Error: ") + ate_inst.get_last_response());
    }
}

uint32_t SPIController::__spi_read_receive_register() {
    std::uint32_t wb_addr = 0x00001C00 + 0x31;
    if(ate_inst.read(wb_addr)) {
        return ate_inst.get_value();
    }
    else {
        fprintf(stderr, "%s", ate_inst.get_error());
        return -1;
    }
}

void SPIController::spi_write(uint32_t value) {
    __spi_write_transmit_register(value);
}

uint32_t SPIController::spi_read() {
    return __spi_read_receive_register();
}
