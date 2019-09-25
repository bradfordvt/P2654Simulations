# P2654Simulation Project
The P2654Simulation project was created to
provide a platform for experimenting with
architectural concepts for both the IEEE P2654
*Standard for System Test Access Management
(STAM) to Enable Use of Sub-System Test
Capabilities at Higher Architectural
Levels* proposed
standard and the IEEE P1687.1 *Standard for
the Application of Interfaces and Controllers
to Access 1687 IJTAG Networks Embedded Within
Semiconductor Devices*.

Details for the IEEE P2654 group may be found
[here](https://standards.ieee.org/project/2654.html).

Details for the IEEE 1687.1 group may be found
[here](https://standards.ieee.org/project/1687_1.html). 

This project is a "*Work In Progress (WIP)*"
project that is undergoing a lot of change
and restructuring to figure out the best layout
to support the different perspectives required
by both of the working groups.

The code written for this project is licensed
using the GNU license as shown in the LICENSE.txt
file in the root directory.  Other projects
may be leveraged by this project to provide
modeling of interface buses, such as, AXI4, Avalon,
and Wishbone for use in porting the simulations
to FPGA designs for further testing.  Those
modules will be licensed using their respective
licensing models.
 
This project consists of both hardware designs,
provided as myHDL models (Verilog and VHDL are
possible to be generated from these myHDL
models) as well as software to interact with
these models as if the models were real
system hardware, but running as a simulation.
This allows for the construction of various
use cases with the hardware models and then
experiment with software architectures to
control these models in-system.

The dependencies required to run these simulations
may be found in the requirements.txt file.

The hardware models are described in the **hdl**
sub-directory of the project.  These will be
described in a separate section of this README.

Each of the hardware models that need to be
supported by IEEE Std 1687 retargeters must
have a corresponding Internal Connectivity
Language (ICL) description of its structure.
The corresponding ICL will be located in the
**icl** sub-directory following the same
directory structure of the hdl model.

The documentation about this project may be found
in the **docs** sub-directory.

## Hardware Definition Language Models (hdl)
The hardware models are decomposed of modular
parts.  Each partition of a system is broken
down into its smaller modules based on the
module type.  A board is assembled with devices.
Devices consist of controllers, instruments,
cores, and interfaces that have host and
client side elements.  Devices also require
interfaces at the board level to interconnect
devices together.
### boards
This directory contains the top level designs
for various board use case scenarios for use
in testing ideas for the IEEE P2654 proposed
standard.
### clients
This directory is to be used to model specialized
client interfaces that are reusable elements
for device or core designs.
### common
The core directory is used to contain common
logic blocks that are reusable for many types
of designs.
### controllers
This directory is to be used to model
specialized controller logic that is used
to interface to device pin or board edge
interfaces (e.g., JTAG controller, I2C Controller,
SPI Controller).  These controllers provide
an interface from software tools to the hardware
simulation environment.
### devices
The devices directory defines the various
forms of devices that may be found assembled
on a circuit board.  Each device type will
have its own sub-directory to contain all
the logic files required to describe it.
#### bridges
These devices are a family of devices that
bridge one protocol to another protocol.
For example, SPI to I2C or JTAG to I2C.
##### *tpsp*
The TPSP device class represents the interface
between a 2-pin Serial Protocol and the JTAG
IEEE Std 1149.1 Protocol.  It was presented
by Martin Keim from Mentor Graphics to help
model the retargeting between two different
protocol domains by looking at the signal
states as a series of cycles instead of just
the raw data.  The TPSP logic looks like the
following logic diagram:

![TPSP Logic Diagram](./docs/images/TPSP.png)

The TPSP protocol description may be found below
and consists of 3 cycles on the serial port
(TMS, TDI, TDO) corresponding to a single
cycle on the JTAGInterface side.

![TPSP Protocol Description](./docs/images/TPSPProtocol.png)

```python
@block
def TPSP(path, name, spclk, reset_n, spio_in, spio_en, spio_out,
             jtag_interface, tdi, tdo, tdo_en,
             power_usage_register, thermal_register, monitor=False):
    """
    Logic to create an instance of the 2-Pin Serial Port
    :param path: Dot path of the parent of this instance
    :param name: String containing the instance name to be printed in diagnostic messages
    :param spclk: Clock signal used to change state and tick the delay times for delay states
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param spio_in: Data Input Signal
    :param spio_en: Control Signal to enable the SPIO_OUT to the SPIO bus
    :param spio_out: Data Output Signal
    :param jtag_interface: JTAGInterface object defining the JTAG signals used by this controller
    :param tdi: Test Data Input signal of the jtag_interface for this device
    :param tdo: Test Data Output signal of the jtag_interface for this device
    :param tdo_en: Test Data Output Enable input signal for the jtag_interface for this device
    :param power_usage_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param thermal_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% themal usage
            that changes over time depending on the operation being performed.  The temperature monitor
            would monitor this value and report the temperature the system is producing.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
#### use_cases
##### *rearick*
This class represents the use case device
Jeff Rearick from AMD proposed as the test
design for IEEE P1687.1 to benchmark against
as we study the various issues and solutions
identified for the standard.  The device consists
of the following elements:

![Jeff Rearick Use Case Diagram](./docs/images/JeffUseCaseDiagram.png)

### hosts
This directory is to be used to model specialized
host interfaces that are reusable elements
for device or core designs.
#### *jtaghost*
This directory contains the modules making up
the host interface to the IEEE Std 1149.1 interface
of a board or device accessible from software
tools.
##### *JTAGHost*
Top level entity the software would connect
to via register access from a memory mapped bus
like Wishbone or AXI4.  This is a WIP module.
##### *JTAGCtrlMaster*
This class is a JTAG host block adapted from the OpenCores.org
jtag_master project that was originally implemented in VHDL.
Some logic had to be changed due to multiple driver errors
detected by the conversion audits when converting the myHDL
to Verilog or VHDL.  In the JTAG_Ctrl_Master.py file there are some
utility methods for test benches that provide for performing
ScanIR and ScanDR operations over the JTAG interface to a client
DUT.  The TDI and TDO vectors for these methods are arrays of
integers whose size must be less than 2**data_width defined
for the instance.  The design uses a Block RAM for storing the
vector data and capturing the responses in the same buffer
by overwriting the scanned out bits with the capture bits
during the scan process.  The interface to the instrument
uses a synchronous clock to latch the data written to the
memory data bus as well as command signals to start the
scan.  The host software needs to define the the type of
scan operation or use the provided utility methods.  Control
of this instrument must be performed by a generator method
running as part of the simulation (see the testbench method
in JTAG_Ctrl_Master.py as an example).
The interface code snippet may be found here:

```python
def write_vector(clk, waddr, din, wr, addr, data):
    """
    Non-convertable code
    This code is used to simplify writing of test benches
    :param control_interface: Interface to this device
    :param addr: Address of memory buffer to store the next segment of the vector into (size of data_width)
    :param data: The contents to be written into the memory buffer of the master (size of data_width)
    :return:
    """
    yield clk.negedge
    waddr.next = addr
    din.next = data
    wr.next = bool(1)
    yield clk.posedge
    yield clk.negedge
    wr.next = bool(0)
    yield clk.posedge
    waddr.next = 0


def read_vector(clk, raddr, wr, read_data, dout, addr):
    """
    Non-convertable code
    This code is used to simplify writing of test benches
    :param addr: Address of memory buffer to fetch the next segment of the vector from (size of data_width)
    :return:
    """
    yield clk.negedge
    raddr.next = addr
    wr.next = bool(0)
    yield clk.posedge
    read_data.next = dout
    yield clk.negedge
    yield clk.posedge
    raddr.next = 0


def get_read_data(read_data):
    """
    Returns the value fetched by the read_vector call
    :return:
    """
    return read_data


def scan_vector(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start, state_end, busy,
                tdi_vector, count, tdo_vector, start, end, addr_width=10, data_width=8):
    """
    Scan the vector to the TAP with the IR data and capture the response in tdo_vector
    :param tdi_vector: Array of integers for the data to be shifted out (tdi_vector[0] is first integer sent)
    :param count: number of bits to shift
    :param tdo_vector: Array of integers for the data to be captured into (tdo_vector[0] is first integer captured)
    :param start: SHIFTIR or SHIFTDR
    :param end: RUN_TEST_IDLE
    :return:
    """
    # Fill the JTAGCtrlMaster data buffer memory with tdi data
    num_full_words = int(count // data_width)
    remainder = count % data_width
    addr = intbv(0)[addr_width:]
    for i in range(num_full_words):
        data = intbv(tdi_vector[i])[data_width:]
        yield write_vector(clk, waddr, din, wr, addr, data)
        addr = addr + 1
    # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
    if remainder > 0:
        data = intbv(tdi_vector[num_full_words])[data_width:]
        yield write_vector(clk, waddr, din, wr, addr, data)
    # Now start the scan operation
    bit_count.next = intbv(count)[addr_width:]
    shift_strobe.next = bool(1)
    state_start.next = start
    state_end.next = end
    yield busy.posedge
    shift_strobe.next = bool(0)
    yield busy.negedge
    # Scan completed, now fetch the captured data
    addr = intbv(0)[addr_width:]
    for i in range(num_full_words):
        yield read_vector(clk, raddr, wr, read_data, dout, addr)
        data = get_read_data(read_data)
        tdo_vector[i] = int(data)
        addr = addr + 1
    # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
    if remainder > 0:
        yield read_vector(clk, raddr, wr, read_data, dout, addr)
        data = get_read_data(read_data)
        tdo_vector[num_full_words] = int(data)


def scan_ir(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start, state_end, busy,
            tdi_vector, count, tdo_vector, addr_width=10, data_width=8):
    """
    Scan the vector to the TAP with the IR data and capture the response in tdo_vector
    :param tdi_vector: Signal(intbv(0)[count:]) Data to be shifted out
    :param count: number of bits to shift
    :param tdo_vector: Signal(intbv(0)[count]) Data to be captured
    :return:
    """
    start = SHIFT_IR
    end = RUN_TEST_IDLE
    yield scan_vector(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start,
                      state_end, busy,
                      tdi_vector, count, tdo_vector, start, end,
                      addr_width=addr_width, data_width=data_width)


def scan_dr(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start, state_end, busy,
            tdi_vector, count, tdo_vector, addr_width=10, data_width=8):
    """
    Scan the vector to the TAP with the DR data and capture the response in tdo_vector
    :param tdi_vector: Signal(intbv(0)[count:]) Data to be shifted out
    :param count: number of bits to shift
    :param tdo_vector: Signal(intbv(0)[count]) Data to be captured
    :return:
    """
    start = SHIFT_DR
    end = RUN_TEST_IDLE
    yield scan_vector(clk, waddr, raddr, wr, din, dout, read_data, bit_count, shift_strobe, state_start,
                      state_end, busy,
                      tdi_vector, count, tdo_vector, start, end,
                      addr_width=addr_width, data_width=data_width)
```

The example test bench showing how to use these utility methods
is shown below:

```python
@block
def JTAGCtrlMaster_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    addr_width=10
    data_width=8
    control_interface = JTAGCtrlMasterInterface(addr_width=addr_width, data_width=data_width)
    ir_tdi_vector = [Signal(intbv(0x55)[data_width:]), Signal(intbv(0x19)[data_width:])]
    ir_tdo_vector = [Signal(intbv(0)[data_width:]), Signal(intbv(0)[data_width:])]
    dr_tdi_vector = [Signal(intbv(0xA5)[data_width:]), Signal(intbv(0x66)[data_width:])]
    dr_tdo_vector = [Signal(intbv(0)[data_width:]), Signal(intbv(0)[data_width:])]
    count = 15

    jcm_inst = JTAGCtrlMaster('DEMO', 'JCM0',
                              control_interface,
                              monitor=monitor)

    @instance
    def clkgen():
        while True:
            control_interface.clk.next = not control_interface.clk
            yield delay(period // 2)

    @always_seq(control_interface.clk.posedge, reset=control_interface.reset_n)
    def loopback():
        control_interface.tdo.next = control_interface.tdi

    @instance
    def stimulus():
        """
        Scan an IR followed by a scan of a DR
        :return:
        """
        H = bool(1)
        L = bool(0)
        # Reset the instrument
        control_interface.reset_n.next = bool(0)
        yield delay(2)
        control_interface.reset_n.next = bool(1)
        yield delay(50)
        # Scan the IR
        # yield scan_ir(control_interface.clk, control_interface.addr, control_interface.addr, control_interface.wr,
        #               control_interface.din, control_interface.dout, control_interface.read_data,
        #               control_interface.bit_count, control_interface.shift_strobe,
        #               control_interface.state_start, control_interface.state_end, control_interface.busy,
        #               ir_tdi_vector, count, ir_tdo_vector,
        #               addr_width=addr_width, data_width=data_width)

        start = SHIFT_IR
        end = RUN_TEST_IDLE
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        num_full_words = int(count // data_width)
        remainder = count % data_width
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            data = ir_tdi_vector[i]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            addr += 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = ir_tdi_vector[num_full_words]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

        # Now start the scan operation
        control_interface.bit_count.next = intbv(count)[addr_width:]
        control_interface.shift_strobe.next = bool(1)
        control_interface.state_start.next = start
        control_interface.state_end.next = end
        yield control_interface.busy.posedge
        control_interface.shift_strobe.next = bool(0)
        yield control_interface.busy.negedge
        # Scan completed, now fetch the captured data
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            rdata = int(control_interface.dout)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            # data = control_interface.read_data
            # ir_tdo_vector[i] = int(data)
            ir_tdo_vector[i] = rdata
            addr += 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            rdata = int(control_interface.dout)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            # data = control_interface.read_data
            ir_tdo_vector[num_full_words] = rdata

        print("ir_tdo_vector = ", ir_tdo_vector)
        assert(ir_tdo_vector[0] == 0x55)  # Captured TDO value returned to ir_tdo_vector
        assert(ir_tdo_vector[1] == 0x19)  # Captured TDO value returned to ir_tdo_vector
        # yield scan_dr(control_interface.clk, control_interface.addr, control_interface.addr, control_interface.wr,
        #               control_interface.din, control_interface.dout, control_interface.read_data,
        #               control_interface.bit_count, control_interface.shift_strobe,
        #               control_interface.state_start, control_interface.state_end, control_interface.busy,
        #               dr_tdi_vector, count, dr_tdo_vector,
        #               addr_width=addr_width, data_width=data_width)
        start = SHIFT_DR
        end = RUN_TEST_IDLE
        # Fill the JTAGCtrlMaster data buffer memory with tdi data
        num_full_words = int(count // data_width)
        remainder = count % data_width
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            data = dr_tdi_vector[i]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            addr += 1
        # Now write out the remaining bits that may be a partial word in size, but a full word needs to be written
        if remainder > 0:
            data = dr_tdi_vector[num_full_words]
            # yield write_vector(clk, waddr, din, wr, addr, data)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.din.next = data
            control_interface.wr.next = bool(1)
            yield control_interface.clk.posedge
            yield control_interface.clk.negedge
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

        # Now start the scan operation
        control_interface.bit_count.next = intbv(count)[addr_width:]
        control_interface.shift_strobe.next = bool(1)
        control_interface.state_start.next = start
        control_interface.state_end.next = end
        yield control_interface.busy.posedge
        control_interface.shift_strobe.next = bool(0)
        yield control_interface.busy.negedge
        # Scan completed, now fetch the captured data
        addr = intbv(0)[addr_width:]
        for i in range(num_full_words):
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            rdata = int(control_interface.dout)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            #data = control_interface.read_data
            # print("control_interface.read_data = ", control_interface.read_data)
            print("rdata0 = ", rdata)
            dr_tdo_vector[i] = rdata
            addr += 1
        # Now read out the remaining bits that may be a partial word in size, but a full word needs to be read
        if remainder > 0:
            # yield read_vector(clk, raddr, wr, read_data, dout, addr)
            yield control_interface.clk.negedge
            control_interface.addr.next = addr
            control_interface.wr.next = bool(0)
            yield control_interface.clk.posedge
            # control_interface.read_data.next = control_interface.dout
            # print("control_interface.read_data = ", control_interface.read_data)
            rdata = int(control_interface.dout)
            print("data1 = ", rdata)
            yield control_interface.clk.negedge
            yield control_interface.clk.posedge
            control_interface.addr.next = 0

            # data = get_read_data(read_data)
            # data = control_interface.read_data
            dr_tdo_vector[num_full_words] = rdata
        print("dr_tdo_vector = ", dr_tdo_vector)
        assert(dr_tdo_vector[0] == 0xA5)  # Captured TDO value returned to dr_tdo_vector
        assert(dr_tdo_vector[1] == 0x66)  # Captured TDO value returned to dr_tdo_vector
        raise StopSimulation()

    return jcm_inst, clkgen, stimulus, loopback
```

##### *JTAGShiftBlock*
This class describes the shift cycle hardware
to read the values to be shifted out from a
FIFO interface and to store the values captured
from the DUT into a FIFO output memory via
a FIFO bus interface. The user would store data
to be scanned in the send buffer and then command
the JTAGHost to send the data.  The JTAGHost
would place the captured data in the receive
buffer for the user to read out.  This is a
WIP module.
### instruments
This directory contains the models for various
instruments to be used during the simulations.
These instruments make up the elements identified
in the various use cases found by the working
groups.
#### *clock_freq_counter*
The clock_freq_counter is used to measure the frequency
of a clock input using a master clock as the basis for
comparison.  The instrument compares the number of samples
of the test clock to a fininte number of reference ticks
to determine the frequency of the input clock being tested.
```python
@block
def clock_freq_counter(path, name, clk, reset_n, i_clk_test, o_clock_freq, monitor=False):
    """
    Clock Frequency Counter
    Variables and processes with prefix r1_ are with clk reference domain
    Variables and processes with prefix r2_ are with i_clk_test domain
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param clk: Reference Clock
    :param reset_n: Reset signal to reset the logic
    :param i_clk_test: The clock to be tested
    :param o_clock_freq: Signal(intbv(0)[16:]) The count of ticks on i_clk_test
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
#### *clock_generator*
The clock generator is composed of to entities: clock_tick and
mod_m_counter.  This instrument is based on the work outlined
[here](https://buildmedia.readthedocs.org/media/pdf/fpga-designs-with-myhdl/latest/fpga-designs-with-myhdl.pdf).
The clock_tick entity delegates most of the work to the mod_m_counter
to create the programmable clock frequency for the generator.
```python
@block
def clock_tick(path, name, clk, reset_n, clk_pulse, M=5, N=3, monitor=False):
    """
    Clock pulse generator
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param clk: Reference Clock
    :param reset_n: Reset signal to reset the logic
    :param clk_pulse: Output clock pulse
    :param M: Max count
    :param N: minimum bits required to represent M
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
```python
@block
def mod_m_counter(path, name, clk, reset_n, complete_tick, count, M=5, N=3, monitor=False):
    """
    Modulo M counter
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param clk: Reference Clock
    :param reset_n: Reset signal to reset the logic
    :param complete_tick: Output clock
    :param count: The internal counter value
    :param M: Max count
    :param N: minimum bits required to represent M
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
#### *comparator*
The comparator class is used to simulate the temperature
comparator instrument of the Rearick use case.
The inputs are the temperature from the thermometer
instrument, a register to set the low threshold, a
register to set the high threshold, and a status register
of 2 bits indicating a temperature undertemp and overtemp
conditions.
```python
@block
def comparator(path, name, clock, reset_n, temperature,
               low_register, high_register,
               status_register, monitor=False):
    """

    :param path: Dot path of the path of this instance
    :param name: Instance name for debug logger (path instance)
    :param clock: Clock signal used to change state
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param temperature: Register where output value of temperature
    :param low_register: Low temperature setting for good range
    :param high_register: High temperature setting for good range
    :param status_register: Status of comparison Signal(intbv(0)[8:])
            Bit0: 1=Temperature fell below low value, 0=Temperature at or above low value
            Bit1: 1=Temperature above high value, 0=Temperature at or below high value
            Bits2-7: Reserved (default to 0)
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
#### *LED*
The LED class provides the simulation of the LED indicator
for the Rearick use case.  This class simulates the state of
an LED while also opening a Tkinter based display
of an LED that shows up either off or on and will
change state of the display to reflect the current
state of the LED.
```python
class LED:
    """

    """
    def __init__(self, parent, name,  di):
        """

        :param parent:
        :param name:
        :param di:
        """
```
#### *noise_maker*
The noise_maker model represents a fictional
instrument used to inject noise on the power supply
to cause over and under voltage conditions at will.
The noise is calculated as the product of the
num_toggles and num_stages arguments.  noise is updated
on every positive edge of ck.
```python
@block
def noise_maker(path, name, num_toggles, num_stages, ck, noise, monitor=False):
    """
    Instrument to inject noise into the power supply rail to alter the value of the supply.
    Algorithm is to cause num_toggles * num_stages cycles per ck tick.
    Since a PLL is not available in the simulation environment, the noise output is used to capture the number of
    cycles that have been sent per ck period.
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param num_toggles: Number of toggles to perform per stage.  Signal(intbv(0, min=0, max=MAX_TOGGLES))
    :param num_stages: Number of stages to perform per clock cycle.  Signal(intbv(0, min=0, max=MAX_STAGES))
    :param ck: Clock signal to define the window to apply the noise in.
    :param noise: Signal providing the noise generated by this maker to the power supply monitor
                Signal(intbv(0, min=0, max=MAX_TOGGLES*MAX_STAGES)
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: list of generators for the noise_maker logic for simulation.
    """
```
#### *power_supply_monitor*
The power_supply_monitor model represents a fictional
power supply monitoring instrument that is monitoring the
power consumption of the mbist instruments and whether
noise is present on the power rail.

For now, the power monitor will indicate an under voltage
condition if the percent of power consumed by the mbist
instruments is greater than 70 percent average of all mbist
instruments.  An under voltage will also be given if
VDD - noise < VDD - (delta/2). An over voltage will be indicated
if VDD + noise > VDD + (delta/2).
```python
@block
def power_supply_monitor(path, name, reference, delta, fast_ck, over, under,
                         noise, pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
                         monitor=False):
    """
    Instrument to monitor the power supply stability over time to determine of the voltage is in range, over range,
    or under range.  Normal operating conditions is where under == 0 and over == 0.
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param reference: Reference value of what the power supply voltage should be as a Signal(intbv(0)[16:]) type.
                        This signal is to be set by the user via an instrument register.
                        Setting the reference value to zero (0) will reset the under and over signals.
    :param delta: The amount of mV variance allowed around the voltage reference as a Signal(intbv(0)[8:]) type.
                        This signal is to be set by the user via an instrument register.
    :param fast_ck: Sampling clock for when to sample the voltage value of VDD. Signal(bool(0)) type.
    :param over: Signal to indicate the monitor detected the voltage exceeded the delta setting. Signal(bool(0)) type.
    :param under: Signal to indicate the monitor detected the voltage fell below the delta setting.
                    Signal(bool(0)) type.
    :param noise: Signal input from noise_maker for clock noise injected into the power supply VDD.
                    Signal(intbv(0, min=0, max=(MAX_TOGGLES * MAX_STAGES)) type.
    :param pu_mbist1: Power Usage value coming from the mbist1 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist2: Power Usage value coming from the mbist2 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist3: Power Usage value coming from the mbist3 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist4: Power Usage value coming from the mbist4 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param pu_mbist5: Power Usage value coming from the mbist5 instrument. Signal(intbv(0, min=0, max=101)) type.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: list of generators for the power_supply_monitor logic for simulation.
    """
``` 
#### *simulatedmbist*
The simulatedmbist model represents a fictional
Memory BIST entity inside a device that tests
a block of memory inside the device.  The
model does not actually test a memory block,
but instead simulates the time taken and
the power and temperature profiles the instrument
would have on a device.

(Place picture of instrument here)
```python
@block
def simulatedmbist(path, name, clock, reset_n, control_register, cr_latch, status_register, power_usage_register,
                   thermal_register, initialize_delay=10, test_delay=30, analyze_delay=20, monitor=False):
    """
    Constructor to create an instance of the MBIST Simulated Instrument
    :param path: Dot path of the parent of this instance
    :param name: String containing the instance name to be printed in diagnostic messages
    :param clock: Clock signal used to change state and tick the delay times for delay states
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param control_register[0:7]: Parallel register to control the operation of the instrument
            Bit0: 1=Start the BIST operation, 0=NOP for status scans
            Bit1: 1=Stop the BIST operation and abort, 0=Do not abort the test
            Bit2: 1=Inject error during test_delay state, 0=Do not inject error during test_delay state
            Bit3: 1=Inject error during analyze_delay state, 0=Do not inject error during analyze_delay state
            Bit4: 1=Double the initialize_delay time to use at start, 0=Use the specified initialize_delay
            Bit5: 1=Double the test_delay time to use at start, 0=Use the specified test_delay
            Bit6: 1=Double the analyze_delay time to use at start, 0=Use the specified analyze_delay
            Bit7: Reserved (Defaults to 0)
    :param cr_latch: Latch trigger to update value of control_register
    :param status_register[0:7]: Parallel register to publish the status of the instrument operation
            Bit0: 1=Test passed, 0=Test failed
            Bit1: 1=MBIST test is running, 0=MBIST test is not running
            Bit2: 1=Test aborted due to unknown error, 0=Test did not abort
            Bit3: 1=Error during test state detected, 0=No error detected during test state
            Bit4: 1=Error during analyze state detected, 0=No error detected during analyze state
            Bit5: Reserved.  Added so status_register can be capture register and control_register as update
            Bit6: Reserved.  Added so status_register can be capture register and control_register as update
            Bit7: Reserved. (Defaults to 0)
    :param power_usage_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param thermal_register: Signal(intbv(0, min=0, max=101)) signal representing 0 - 100% thermal usage
            that changes over time depending on the operation being performed.  The temperature monitor
            would monitor this value and report the temperature the system is producing.
    :param initialize_delay: Keyword argument to specify the number of clock ticks to spin in initialize state
    :param test_delay: Keyword argument to specify the number of clock ticks to spin in the test state
    :param analyze_delay: Keyword argument to specify the number of clock ticks to spin in the analyze state
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
#### *thermometer*
The thermometer class is used to simulate a temperature sensor
monitoring the temperature generated by the MBIST
instruments as the MBIST tests are applied.
```python
@block
def thermometer(parent, name, clock, reset_n, temperature,
                thermal_register1, thermal_register2, thermal_register3,
                thermal_register4, thermal_register5, monitor=False):
    """

    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param clock: Clock signal used to change state
    :param reset_n: Reset signal for state machine. 0=Reset, 1=No reset
    :param temperature: Register where output value of temperature
    :param thermal_register1: Proportion of total temperature of MBIST1
    :param thermal_register2: Proportion of total temperature of MBIST2
    :param thermal_register3: Proportion of total temperature of MBIST3
    :param thermal_register4: Proportion of total temperature of MBIST4
    :param thermal_register5: Proportion of total temperature of MBIST5
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
### standards
The standards directory contains reusable
models for specific standards that are needed
to model other elements of a device.  Each
standard has its own directory containing the
reusable modules for that standard.
#### p1687dot1
This directory contains examples of P1687.1
transform engines and DPIC interfaces for testing
different ideas surrounding the standard.
#### s1149dot1
This directory contains the following models
used to provide reusable components/designs
for devices adhering to the IEEE Std 1149.1
standard for access to embedded instrumentation.
##### *JTAGInterface*
The JTAGInterface provides a class containing
the bused interface signals of the device pin
interface.  It does not contain the TDI and
TDO signals as they need to be individually
connected serially between devices.
```python
class JTAGInterface:
    def __init__(self):
        self.TCK = Signal(bool(0))
        self.TMS = Signal(bool(1))
        self.TRST = Signal(bool(1))
```
##### *JTAGState*
The JTAGState class provides a convenient method
for capturing the state information from the
Std1149_1_TAP for diagnostic purposes.  The
state is a 4 bit value indicating what state
the TAP State Machine is in during execution.
The following states and corresponding values
are shown below:

|Controller STATE | DCBA Hex Value|
|:---:|:---:|
|   EXIT2DR    |       0      |
|   EXIT1DR    |       1      |
|   SHIFTDR    |       2      |
|   PAUSEDR    |       3      |
|   SELECTIR   |       4      |
|   UPDATEDR   |       5      |
|   CAPTUREDR  |       6      |
|   SELECTDR   |       7      |
|   EXIT2IR    |       8      |
|   EXIT1IR    |       9      |
|   SHIFTIR    |       A      |
|   PAUSEIR    |       B      |
| RUNTEST/IDLE |       C      |
|   UPDATEIR   |       D      |
|   CAPTUREIR  |       E      |
|    RESET     |       F      |

The value inside the class is accessible to
view or print out the current state of the
associated Std1149_1_TAP the class instance
is attached to.

```python
class JTAGState:
    def __init__(self):
        self.value = Signal(intbv(15, min=0, max=16))
```
##### *Std1149_1_TAP*
This module implements the IEEE Std 1149.1
TAP Controller that interfaces the device
pins with the internal scan logic as per the
1149.1 standard.  It takes as ports an
instance of the JTAGInterface class to describe
the pin interface of the device, an instance
of the JTAGState class to monitor the state
status of the TAP Controller, and an instance
of the TAPInterface class that describes the
signals used to interface with the scan logic
inside the device.
```python
@block
def Std1149_1_TAP(path, name, jtag_interface, state, tap_interface, monitor=False):
    """
    TAP Controller logic
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param jtag_interface: JTAGInterface object defining the JTAG signals used by this controller
    :param state: Monitor signal state with this 4 bit encoding
    :param tap_interface: TAPInterface object defining the TAP signals managed by this controller
    :return:
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *TAPInterface*
This class defines the bused interface signals
used to control the scan logic inside the device
that is used to implement the Instruction
Register and Data Registers providing access
to the logic inside the device.
```python
class TAPInterface:
    def __init__(self):
        self.Reset = Signal(bool(0))
        self.Enable = Signal(bool(0))
        self.ShiftIR = Signal(bool(0))
        self.CaptureIR = Signal(bool(0))
        self.ClockIR = Signal(bool(0))
        self.UpdateIR = Signal(bool(0))
        self.ShiftDR = Signal(bool(0))
        self.CaptureDR = Signal(bool(0))
        self.ClockDR = Signal(bool(0))
        self.UpdateDR = Signal(bool(0))
        self.UpdateDRState = Signal(bool(0))
        self.Select = Signal(bool(0))
```
##### *TDR*
The TDR class implements the logic for a Test
Data Register following the convention of
the IEEE Std 1149.1 standard.  This register
provides access to the read and write side of
parallel registers of an embedded instrument
or pin interfaces, such as the Boundary Scan
Register used to test the continuity between
devices.
```python
@block
def TDR(path, name, D, Q, scan_in, tap_interface, local_reset, scan_out, tdr_width=9, monitor=False):
    """
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param D: tdr_width bit wide Signal D = Signal(intbv(0)[tdr_width:])
    :param Q: tdr_width bit wide Signal Q = Signal(intbv(0)[tdr_width:])
    :param scan_in: Input signal for data scanned into TDR
    :param tap_interface: TAPInterface object containing:
        CaptureDR: Signal used to enable the capture of D
        ShiftDR: Signal used to shift the data out ScanOut from the TDR
        UpdateDR: Signal used to latch the TDR to Q
        Select: Signal used to activate the TDR
        Reset: Signal used to reset the Q of the TDR
        tap_interface.ClockDR: Test tap_interface.ClockDR used to synchronize the TDR to the TAP
    :param local_reset: Active low Signal used by the internal hardware to reset the TDR
    :param scan_out: Output signal where data is scanned from the TDR
    :param tdr_width: The number of bits contained in this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *TIR*
The TIR class implements the logic for the
Test Instruction Register used to select the
desired TDR to be accessed during a SHIFTDR
state sequence.
```python
@block
def TIR(path, name, D, Q, scan_in, tap_interface, local_reset, scan_out, tir_width=9, monitor=False):
    """
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param D: tir_width bit wide Signal D = Signal(intbv(0)[tir_width:])
    :param Q: tir_width bit wide Signal Q = Signal(intbv(0)[tir_width:])
    :param scan_in: Input signal for data scanned into TIR
    :param tap_interface: TAPInterface object containing:
        CaptureIR: Signal used to enable the capture of D
        ShiftIR: Signal used to shift the data out ScanOut from the TIR
        UpdateIR: Signal used to latch the TIR to Q
        Select: Signal used to activate the TIR
        Reset: Signal used to reset the Q of the TIR
        tap_interface.ClockIR: Test tap_interface.ClockIR used to synchronize the TIR to the TAP
    :param local_reset: Active low Signal used by the internal hardware to reset the TIR
    :param scan_out: Output signal where data is scanned from the TIR
    :param tir_width: The number of bits contained in this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
#### s1500
This directory contains the following models
used to provide reusable components/designs
for devices adhering to the IEEE Std 1500
standard for access to embedded instrumentation.
##### *selwir*
This entity represents the Select Wrapper Instruction Register
logic for a 1500 design.
```python
@block
def SELWIR(path, name, si, ijtag_interface, so, select_wir, monitor=False):
    """
    Creates a Select WIR register with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: ScanInPort
    :param ijtag_interface: IJTAGInterface defining the control signals for this register
    :param so: ScanOutPort
    :param select_wir: Select WIR signal to be controlled by this register
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *wby*
This entity represents the Wrapper BYPASS register of the design.
```python
@block
def wby(path, name, wsi, wsp_interface, select, wby_wso, width=1, monitor=False):
    """
    This class implements the logic for the WBY (Wrapper BYPASS Register) of IEEE Std 1500 standard.
    IEEE Std 1500 Wrapper BYPASS Register (WBY) Logic adhering to Figure 15 of the standard
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param wsi: Wrapper Scan In Signal
    :param wsp_interface: Wrapper Scan Port instance
    :param select: Select Signal for WBY from WIR (select and wsp_interface.ShiftWB are used to create
            the ShiftWBY signal)
    :param wby_wso: Wrapper BYPASS Scan Out Signal
    :param width: The number of scan bits implemented by this WBY
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *wdrmux*
This entity represents the Wrapper Data Register MUX that controls
what data register is connected between WSI and WSO as defined
by the current instruction in the SELWIR register.
```python
@block
def WDRmux(path, name,
             wby_out, mbist1_out, mbist2_out, mbist3_out,
             wr_select_list, dr_select_list,
             so, monitor=False):
    """
    MUX to control what WDR is connected to so
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param wby_out: Signal Out from WBY register
    :param mbist1_out: Signal Out from MBIST1 register
    :param mbist2_out: Signal Out from MBIST2 register
    :param mbist3_out: Signal Out from MBIST3 register
    :param wr_select_list: [Signal(bool(0) for _ in range(len(wr_list)] to use as 1500 wrapper instruction signals
    :param dr_select_list: [Signal(bool(0) for _ in range(len(user_list)] to use as user instruction signals
    :param so: Signal out from WDRs to WIRMux
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *wir*
This entity is the Wrapper Instruction Register logic for the
Rearick use case for the data registers defined by the use case.
```python
@block
def wir(path, name, wsi, wsp, wso, wr_list, user_list, wr_select_list, dr_select_list, monitor=False):
    """
    Wrapper Instruction Register Logic
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param wsi: Wrapper Scan In Port
    :param wsp: Wrapper Scan Port instance
    :param wso: Wrapper Scan Out Port
    :param wr_list: A list of strings defining the Wrapper 1500 instructions as per the standard
    :param user_list: A list of strings defining the instructions for the user defined data registers
    :param wr_select_list: Signal(intbv(0)[len(wr_list):]) to use as 1500 wrapper instruction signals
    :param dr_select_list: Signal(intbv(0)[len(user_list):]) to use as user instruction signals
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *wirmux*
This entity defines the MUX that is used to select when the WIR
is connected between WSI and WSO or if the data register path
should be selected.
```python
@block
def WIRmux(path, name, wdr_out, wir_out, select_wir, so, monitor=False):
    """
    MUX to control what WDR is connected to so
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param wdr_out: Signal Out from WDRmux logic
    :param wir_out: Signal Out from WIR register
    :param select_wir: Select Signal for WIR register
    :param so: Signal out from WIRMux
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *wsp*
This interface implements the Wrapper Serial Port (WSP) interface of IEEE Std 1500 standard.
```python
class wsp:
    """
    This class implements the Wrapper Serial Port (WSP) interface of IEEE Std 1500 standard.
    """
    def __init__(self):
        self.AUXCKn = Signal(bool(0))
        self.WRCK = Signal(bool(0))
        self.WRSTN = Signal(bool(1))
        self.TransferDR = Signal(bool(0))
        self.UpdateWR = Signal(bool(0))
        self.ShiftWR = Signal(bool(0))
        self.CaptureWR = Signal(bool(0))
        self.SelectWIR = Signal(bool(0))
        # Do not add the serial in and out to this interface as these get daisy chained and not bussed.
        # self.WSI = Signal(bool(0))
        # self.WSO = Signal(bool(0))
```
#### s1687
This directory contains the following models
used to provide reusable components/designs
for devices adhering to the IEEE Std 1687
standard for access to embedded instrumentation.
##### *IJTAGInterface*
The IJTAGInterface provides a class
containing the bused interface signals of
the 1687 host to client interface. It does
not contain the SI and SO signals as they
need to be individually connected serially
between 1687 network elements.
```python
class IJTAGInterface:
    def __init__(self):
        self.SELECT = Signal(bool(0))
        self.CAPTURE = Signal(bool(0))
        self.SHIFT = Signal(bool(0))
        self.UPDATE = Signal(bool(0))
        self.RESET = Signal(bool(0))
        self.CLOCK = Signal(bool(0))
```
##### *sib_mux_post*
The sib_mux_post class describes the design
of the 1687 Segment Insertion Bit (SIB) where
the included sub-network is inserted after
the SIB control bit in the scan vector.
This design adheres to the example in the
Figure F.10 of the standard as shown below: 

![sib_mux_post logic diagram](./docs/images/sib_mux_post.png)

The class provides the client interface from
the network to the host interface (from side)
to the sub-network (to side) using 2 separate
IJTAGInterface instances: one for the from (network)
side and one for the to (instrument) side.
```python
@block
def sib_mux_post(path, name, si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so, monitor=False):
    """
    This code implements the logic from Figure F.10 in the IEEE Std 1687 standard.
    Segment-Insertion-Bit (SIB) to allow the overall scan chain to be of variable length.
    Creates a Module SIB for IEEE 1687 with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: Scan Input from host interface
    :param from_ijtag_interface: IJTAGInterface defining the control signals for this register "from" side
    :param so: Scan Output to host interface from SIB
    :param to_si: Scan Input to instrument interface
    :param to_ijtag_interface: IJTAGInterface defining the control signals for this register "to" side
    :param from_so: Scan Output from instrument interface
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *sib_mux_pre*
The sib_mux_pre class describes the design
of the 1687 Segment Insertion Bit (SIB) where
the included sub-network is inserted before
the SIB control bit in the scan vector.
This design adheres to the example in the
Figure F.12 of the standard as shown below: 

![sib_mux_pre logic diagram](./docs/images/sib_mux_pre.png)

The class provides the client interface from
the network to the host interface (from side)
to the sub-network (to side) using 2 separate
IJTAGInterface instances: one for the from (network)
side and one for the to (instrument) side.
```python
@block
def sib_mux_pre(path, name, si, from_ijtag_interface, so, to_si, to_ijtag_interface, from_so, monitor=False):
    """
    This class implements the logic from Figure F.12 in the IEEE Std 1687 standard.
    Segment-Insertion-Bit (SIB) to allow the overall scan chain to be of variable length.
    Creates a Module SIB for IEEE 1687 with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: Scan Input from host interface
    :param from_ijtag_interface: IJTAGInterface defining the control signals for this register "from" side
    :param so: Scan Output to host interface from SIB
    :param to_si: Scan Input to instrument interface
    :param to_ijtag_interface: IJTAGInterface defining the control signals for this register "to" side
    :param from_so: Scan Output from instrument interface
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
##### *SReg*
The SReg class describes the generic scan
register as described in Figure F.2 of the
standard with the distinction of supporting
a user defined number of bits instead of just
a single bit.

![SReg logic diagram](./docs/images/SReg.png)

The class provides a client interface to the
1687 network as well as handles to capture
and update parallel registers.
```python
@block
def SReg(path, name, si, ijtag_interface, so, di, do, dr_width=9, monitor=False):
    """
    Creates a Module SReg for IEEE 1687 with the following interface:
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logging (path instance)
    :param si: ScanInPort
    :param ijtag_interface: IJTAGInterface defining the control signals for this register
    :param so: ScanOutPort
    :param di: DataInPort Signal(intbv(0)[dr_width:])
    :param do: DataOutPort Signal(intbv(0)[dr_width:])
    :param dr_width: The width of the DI/DO interfaces and size of the SR
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    """
```
### tests
This directory contains the test cases used
for regression testing of the hdl models.
Each model will have its corresponding directory
as shown in the hdl branch.  These directories
align the test code with the model code.