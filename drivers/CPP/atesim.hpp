#include <cstdint>
#include <string>
#include <vector>
#include <cstddef>
#include <TelnetClient.hpp>

typedef uint8_t byte;
typedef std::vector<byte> byte_array;

using namespace telnetclient;

class ATETelnetClient {
public:
    ATETelnetClient(): timeout(60), ip("127.0.0.1"), port(5023), tn_inst() { tn_inst.set_debug_level(1); };
    ~ATETelnetClient() { };
    void connect(const char* ip, int port);
    const char* read_until(const char* expect) { return tn_inst.read_until(expect, 60); };
    const char* read_until(std::string expect) { return tn_inst.read_until(expect.c_str(), 60); };
    const char* read_all() { return tn_inst.read_all(); };
    const char* read_some() { return tn_inst.read_some(); };
    void write(const char* s) { tn_inst.write(s); };
    void write(std::string s) { tn_inst.write(s.c_str()); };
    void close() { tn_inst.close(); };
private:
    int timeout;
    std::string ip;
    int port;
    TelnetClient tn_inst;
};

class ATE {
public:
    ATE(const char* ip, int port);
    ~ATE();
    bool connect(const char* board);
    bool write(std::uint32_t adr, std::uint32_t data);
    bool read(std::uint32_t adr);
    std::uint32_t get_value() { return value; };
    const char* get_error() { return error; };
    bool terminate();
    bool close();
    const char* get_last_response() { return resp; };
private:
    ATETelnetClient tn_inst;
    std::string ip;
    int port;
    char resp[512];
    std::uint32_t value;
    char error[512];
};

class AcknowledgeError:  public std::exception
{
    std::string what_message;
public:
    AcknowledgeError(const char* message) : what_message(message) { };
    AcknowledgeError(std::string message) : what_message(message.c_str()) { };
    const char* what()
    {
        return what_message.c_str();
    }
};

class GPIOController {
public:
    GPIOController(ATE& ate) : ate_inst(ate) { };
    ~GPIOController() { };
    bool write(std::uint32_t val);
    bool read( );
    std::uint32_t get_value();
    const char* get_error();
private:
    ATE& ate_inst;
};

class JTAGController {
public:
    enum JTAGStates {
        TEST_LOGIC_RESET=0,
        RUN_TEST_IDLE,
        SELECT_DR,
        CAPTURE_DR,
        SHIFT_DR,
        EXIT1_DR,
        PAUSE_DR,
        EXIT2_DR,
        UPDATE_DR,
        SELECT_IR,
        CAPTURE_IR,
        SHIFT_IR,
        EXIT1_IR,
        PAUSE_IR,
        EXIT2_IR,
        UPDATE_IR
    };
    JTAGController(ATE& ate) : ate_inst(ate) { };
    ~JTAGController() { };
    byte_array ba_scan_ir(byte_array& tdi_vector, int count);
    byte_array ba_scan_dr(byte_array& tdi_vector, int count);
    std::string scan_ir(int count, std::string tdi_string);
    std::string scan_dr(int count, std::string tdi_string);
    void runtest(int ticks);
private:
    void __write_vector_segment(std::uint32_t adr, byte data);
    byte __read_vector_segment(std::uint32_t adr);
    void __set_bit_count(std::uint16_t count);
    void __set_state_start(std::uint8_t start);
    void __set_state_end(std::uint8_t end);
    void __set_control_register(std::uint8_t value);
    std::uint8_t __get_status_register();
    byte_array __scan_vector(byte_array& tdi_vector, int count, std::uint8_t start, std::uint8_t end);
    byte __hex(char ch);
    const char* __hex_to_char(byte data);
    ATE& ate_inst;
    std::string tdo_string;
    byte_array tdo_vector;
};

class JTAGController2 {
public:
    enum JTAGStates {
        SI_EXIT2_DR=0,
        SI_EXIT1_DR,
        SI_SHIFT_DR,
        SI_PAUSE_DR,
        SI_SELECT_IR,
        SI_UPDATE_DR,
        SI_CAPTURE_DR,
        SI_SELECT_DR,
        SI_EXIT2_IR,
        SI_EXIT1_IR,
        SI_SHIFT_IR,
        SI_PAUSE_IR,
        SI_RUN_TEST_IDLE,
        SI_UPDATE_IR,
        SI_CAPTURE_IR,
        SI_TEST_LOGIC_RESET
    };

    enum Commands {
        NONE=0,
        SCAN=1,
        RESET=2,
        STATE=3,
        COMMAND_MAX=4
    };

    JTAGController2(ATE& ate) : ate_inst(ate) { };
    ~JTAGController2() { };
    byte_array ba_scan_ir(byte_array& tdi_vector, int count);
    byte_array ba_scan_dr(byte_array& tdi_vector, int count);
    std::string scan_ir(int count, std::string tdi_string);
    std::string scan_dr(int count, std::string tdi_string);
    void runtest(int ticks);
private:
    void __write_vector_segment(std::uint32_t adr, byte data);
    byte __read_vector_segment(std::uint32_t adr);
    void __set_chain_length(std::uint16_t count);
    void __set_state_start(std::uint8_t start);
    void __set_state_end(std::uint8_t end);
    void __set_command(std::uint8_t command);
    void __set_control_register(std::uint8_t value);
    std::uint8_t __get_status_register();
    byte_array __scan_vector(byte_array& tdi_vector, int count, std::uint8_t start, std::uint8_t end);
    byte __hex(char ch);
    const char* __hex_to_char(byte data);
    ATE& ate_inst;
    std::string tdo_string;
    byte_array tdo_vector;
};

class I2CController {
public:
    I2CController(ATE& ate) : ate_inst(ate) { };
    ~I2CController() { };
    void i2c_write_reg(byte dev_address, byte reg_address, byte value);
    byte i2c_read_reg(byte dev_address, byte reg_address);
    bool i2c_multibyte_write(byte dev_address, byte reg_address, uint32_t data);
    uint32_t i2c_multibyte_read(byte dev_address, byte reg_address);
private:
    void __write_transmit_register(byte value);
    byte __read_transmit_register();
    void __write_receive_register(byte value);
    byte __read_receive_register();
    void __write_control_register(byte value);
    byte __read_control_register();
    void __write_status_register(byte value);
    byte __read_status_register();
    ATE& ate_inst;
};

class SPIController {
public:
    SPIController(ATE& ate) : ate_inst(ate) { };
    ~SPIController() { };
    void spi_write(uint32_t value);
    uint32_t spi_read();
private:
    void __spi_write_transmit_register(uint32_t value);
    uint32_t __spi_read_transmit_register();
    void __spi_write_receive_register(uint32_t value);
    uint32_t __spi_read_receive_register();
    ATE& ate_inst;
};
