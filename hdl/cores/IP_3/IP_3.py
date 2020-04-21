"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

IP Logic for IP_3 core of the Rearick Use Case Model
"""
from myhdl import *
from hdl.standards.s1687.IJTAGInterface import IJTAGInterface
from hdl.standards.s1687.sib_mux_post import sib_mux_post
from hdl.standards.s1687.SReg import SReg
from hdl.standards.s1500.wsp import wsp
from hdl.standards.s1500.selwir import SELWIR
from hdl.standards.s1500.wir import wir
from hdl.standards.s1500.wby import wby
from hdl.standards.s1500.WSReg import WSReg
from hdl.standards.s1500.wdrmux import WDRmux
from hdl.standards.s1500.wirmux import WIRmux
from hdl.instruments.power_supply_monitor.power_supply_monitor import power_supply_monitor
from hdl.instruments.noise_maker.noise_maker import noise_maker
from hdl.instruments.noise_maker.noise_maker import MAX_STAGES, MAX_TOGGLES
from hdl.instruments.simulatedmbist.simulatedmbist import simulatedmbist
from hdl.instruments.thermometer.thermometer import thermometer
from hdl.instruments.thermometer.thermometer import AMBIENT, OVERTEMP
from hdl.instruments.comparator.comparator import comparator
from hdl.instruments.led.led import LED
import os
import os.path

period = 20  # clk frequency = 50 MHz


@block
def IP_3(path, name, ijtag_si, ijtag_so, from_ijtag_interface,
         fast_ck, ck,
         pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
         monitor=False):
    """
    Logic core IP_3 for Rearick use case model.  This IP defines the 1687 network topology for the IP_3 network.
    :param path: Dot path of the parent of this instance
    :param name: Instance name for debug logger (path instance)
    :param ijtag_si: The ScanInterface SI for this 1687 network.
    :param ijtag_so: The ScanInterface SO for this 1687 network.
    :param from_ijtag_interface: The ScanInterface signals of SELECT, CAPTURE, SHIFT, UPDATE, RESET, and CLOCK
                    for this 1687 network.
    :param fast_ck: Sampling clock for when to sample the voltage value of VDD. Signal(bool(0)) type.
    :param ck: Clock signal to define the window to apply the noise in.
    :param pu_mbist1: Signal(intbv(0, min=0, max=101)) signal from MBIST1 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist2: Signal(intbv(0, min=0, max=101)) signal from MBIST2 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist3: Signal(intbv(0, min=0, max=101)) signal from MBIST3 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist4: Signal(intbv(0, min=0, max=101)) signal from MBIST4 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param pu_mbist5: Signal(intbv(0, min=0, max=101)) signal from MBIST5 representing 0 - 100% power usage
            that changes over time depending on the operation being performed.  The power monitor would
            monitor this value and report how much total power in the system is being used.
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: list of generators for the IP_3 logic for simulation.
    """
    sib1_to_ijtag_interface = IJTAGInterface()
    sib1_to_sib2_so = Signal(bool(0))
    sib2_to_sib3_so = Signal(bool(0))
    sib1_to_si = Signal(bool(0))
    sib1_from_so = Signal(bool(0))
    selwir_to_wdr_so = Signal(bool(0))
    select_wir = Signal(bool(1))
    wsp_interface = wsp()
    wr_list = ['WS_BYPASS', 'WS_EXTEST', 'WS_INTEST']
    user_list = ['MBIST1', 'MBIST2', 'MBIST3']
    wr_select_list = Signal(intbv(0)[len(wr_list):])
    dr_select_list = Signal(intbv(0)[len(user_list):])
    wby_wso = Signal(bool(0))
    mbist1_out = Signal(bool(0))
    mbist2_out = Signal(bool(0))
    mbist3_out = Signal(bool(0))
    wir_so = Signal(bool(0))
    wdr_so = Signal(bool(0))
    reset1_n = ResetSignal(1, 0, True)
    reset2_n = ResetSignal(1, 0, True)
    reset3_n = ResetSignal(1, 0, True)
    cr1 = Signal(intbv(0)[8:])
    cr2 = Signal(intbv(0)[8:])
    cr3 = Signal(intbv(0)[8:])
    sr1 = Signal(intbv(0)[8:])
    sr2 = Signal(intbv(0)[8:])
    sr3 = Signal(intbv(0)[8:])
    cr_latch1 = Signal(bool(0))
    thermal_register1 = Signal(intbv(0, min=0, max=101))
    thermal_register2 = Signal(intbv(0, min=0, max=101))
    thermal_register3 = Signal(intbv(0, min=0, max=101))
    thermal_register4 = Signal(intbv(0, min=0, max=101))
    thermal_register5 = Signal(intbv(0, min=0, max=101))
    select_wby = Signal(bool(0))
    select_mbist1 = Signal(bool(0))
    select_mbist2 = Signal(bool(0))
    select_mbist3 = Signal(bool(0))

    sib1_inst = sib_mux_post(path + "." + name, "SIB1", ijtag_si, from_ijtag_interface, sib1_to_sib2_so,
                             sib1_to_si, sib1_to_ijtag_interface, sib1_from_so, monitor=monitor)
    selwir_inst = SELWIR(path + "." + name, "SELWIR", sib1_to_si, sib1_to_ijtag_interface, selwir_to_wdr_so,
                         select_wir, monitor=False)
    wir_inst = wir(path + "." + name, "WIR", selwir_to_wdr_so, wsp_interface, wir_so, wr_list, user_list,
                   wr_select_list, dr_select_list, monitor=False)
    wdrmux_inst = WDRmux(path + "." + name, "WDRMux", wby_wso, mbist1_out, mbist2_out, mbist3_out,
                         wr_select_list, dr_select_list, wdr_so, monitor=False)
    wirmux_inst = WIRmux(path + "." + name, "WIRMux", wdr_so, wir_so, select_wir, sib1_from_so, monitor=False)
    wby_inst = wby(path + "." + name, "WBY", selwir_to_wdr_so, wsp_interface,
                   select_wby, wby_wso, monitor=False)
    mbist1_inst = WSReg(path + "." + name, 'MBIST_WSReg1', selwir_to_wdr_so, wsp_interface,
                        select_mbist1, mbist1_out, sr1, cr1, dr_width=8, monitor=False)
    mbist2_inst = WSReg(path + "." + name, 'MBIST_WSReg2', selwir_to_wdr_so, wsp_interface,
                        select_mbist2, mbist2_out, sr2, cr2, dr_width=8, monitor=False)
    mbist3_inst = WSReg(path + "." + name, 'MBIST_WSReg3', selwir_to_wdr_so, wsp_interface,
                        select_mbist3, mbist3_out,sr3, cr3, dr_width=8, monitor=False)
    simbist1_inst = simulatedmbist(path + "." + name, 'SMBIST1', sib1_to_ijtag_interface.CLOCK, reset1_n,
                                   cr1, cr_latch1, sr1, pu_mbist1, thermal_register1,
                                   initialize_delay=10, test_delay=40,
                                   analyze_delay=30,
                                   monitor=monitor)
    simbist2_inst = simulatedmbist(path + "." + name, 'SMBIST2', sib1_to_ijtag_interface.CLOCK, reset1_n,
                                   cr2, cr_latch1, sr2, pu_mbist2, thermal_register2,
                                   initialize_delay=10, test_delay=40,
                                   analyze_delay=30,
                                   monitor=monitor)
    simbist3_inst = simulatedmbist(path + "." + name, 'SMBIST3', sib1_to_ijtag_interface.CLOCK, reset1_n,
                                   cr3, cr_latch1, sr3, pu_mbist3, thermal_register3,
                                   initialize_delay=10, test_delay=40,
                                   analyze_delay=30,
                                   monitor=monitor)

    sib2_to_ijtag_interface = IJTAGInterface()
    sib2_to_si = Signal(bool(0))
    sib2_from_so = Signal(bool(0))
    temp_to_comp_so = Signal(bool(0))
    comp_to_low_so = Signal(bool(0))
    low_to_high_so = Signal(bool(0))
    high_to_led_so = Signal(bool(0))
    temperature = Signal(intbv(AMBIENT, min=0, max=OVERTEMP))
    dummy_temperature = Signal(intbv(AMBIENT, min=0, max=OVERTEMP))
    low_register = Signal(intbv(70, min=0, max=451))
    high_register = Signal(intbv(400, min=0, max=451))
    compsr_register = Signal(intbv(0)[8:])
    led_signal = Signal(intbv(0)[1:])

    sib2_inst = sib_mux_post(path + "." + name, "SIB2", sib1_to_sib2_so, from_ijtag_interface, sib2_to_sib3_so,
                             sib2_to_si, sib2_to_ijtag_interface, sib2_from_so, monitor=monitor)

    temp_SReg_inst = SReg(path + "." + name, "temperature", sib2_to_si, sib2_to_ijtag_interface, temp_to_comp_so,
                          temperature, dummy_temperature, dr_width=9, monitor=monitor)
    temp_inst = thermometer(path + "." + name, 'TEMP0', sib2_to_ijtag_interface.CLOCK, reset2_n, temperature,
                            thermal_register1, thermal_register2, thermal_register3,
                            thermal_register4, thermal_register5, monitor=monitor)
    comp_SReg_inst = SReg(path + "." + name, "comparator", temp_to_comp_so, sib2_to_ijtag_interface, comp_to_low_so,
                          compsr_register, compsr_register, dr_width=8, monitor=monitor)
    low_SReg_inst = SReg(path + "." + name, "low", comp_to_low_so, sib2_to_ijtag_interface, low_to_high_so,
                         low_register, low_register, dr_width=9, monitor=monitor)
    high_SReg_inst = SReg(path + "." + name, "high", low_to_high_so, sib2_to_ijtag_interface, high_to_led_so,
                          high_register, high_register, dr_width=9, monitor=monitor)
    comp_inst = comparator(path + "." + name, 'COMP0', sib2_to_ijtag_interface.CLOCK, reset2_n, temperature,
                           low_register, high_register, compsr_register, monitor=monitor)
    led_SReg_inst = SReg(path + "." + name, "LEDS0", high_to_led_so, sib2_to_ijtag_interface, sib2_from_so,
                          led_signal, led_signal, dr_width=1, monitor=monitor)
    led_inst = LED(path + "." + name, "LED0", led_signal)

    sib3_to_ijtag_interface = IJTAGInterface()
    sib3_to_si = Signal(bool(0))
    sib3_from_so = Signal(bool(0))
    cr4 = Signal(intbv(0)[8:])
    cr5 = Signal(intbv(0)[8:])
    sr4 = Signal(intbv(0)[8:])
    sr5 = Signal(intbv(0)[8:])
    cr_latch3 = Signal(bool(0))
    mux_so = Signal(bool(0))
    mux_select = Signal(intbv(0)[1:])
    mbist4_to_mux_so = Signal(bool(0))
    mbist5_to_mux_so = Signal(bool(0))

    sib3_inst = sib_mux_post(path + "." + name, "SIB3", sib2_to_sib3_so, from_ijtag_interface, ijtag_so,
                             sib3_to_si, sib3_to_ijtag_interface, sib3_from_so, monitor=monitor)
    mbist4_inst = SReg(path + "." + name, "MBIST_SReg4", sib3_to_si, sib2_to_ijtag_interface, mbist4_to_mux_so,
                       thermal_register4, thermal_register4, dr_width=8, monitor=monitor)
    simbist4_inst = simulatedmbist(path + "." + name, 'SMBIST4', sib3_to_ijtag_interface.CLOCK, reset3_n,
                                   cr4, cr_latch3, sr4, pu_mbist4, thermal_register4,
                                   initialize_delay=10, test_delay=40,
                                   analyze_delay=30,
                                   monitor=monitor)
    mbist5_inst = SReg(path + "." + name, "MBIST_SReg5", sib3_to_si, sib2_to_ijtag_interface, mbist5_to_mux_so,
                       thermal_register5, thermal_register5, dr_width=8, monitor=monitor)
    simbist5_inst = simulatedmbist(path + "." + name, 'SMBIST5', sib3_to_ijtag_interface.CLOCK, reset3_n,
                                   cr5, cr_latch3, sr5, pu_mbist5, thermal_register5,
                                   initialize_delay=10, test_delay=40,
                                   analyze_delay=30,
                                   monitor=monitor)
    muxsr_inst = SReg(path + "." + name, "MUX0", mux_so, sib3_to_ijtag_interface, sib3_from_so,
                      mux_select, mux_select, dr_width=1, monitor=monitor)

    @always_comb
    def reset_logic():
        reset1_n.next = not sib1_to_ijtag_interface.RESET
        reset2_n.next = not sib2_to_ijtag_interface.RESET
        reset3_n.next = not sib3_to_ijtag_interface.RESET

    @always(sib1_to_ijtag_interface.CLOCK.posedge)
    def latch1():
        cr_latch1.next = sib1_to_ijtag_interface.UPDATE
        
    @always_comb
    def mux():
        if mux_select[0]:
            mux_so.next = mbist5_to_mux_so
        else:
            mux_so.next = mbist4_to_mux_so

    @always_comb
    def bridge():
        wsp_interface.SelectWIR.next = select_wir and sib1_to_ijtag_interface.SELECT
        wsp_interface.WRCK.next = sib1_to_ijtag_interface.CLOCK
        wsp_interface.WRSTN.next = not sib1_to_ijtag_interface.RESET
        wsp_interface.UpdateWR.next = sib1_to_ijtag_interface.UPDATE
        wsp_interface.CaptureWR.next = sib1_to_ijtag_interface.CAPTURE
        wsp_interface.ShiftWR.next = sib1_to_ijtag_interface.SHIFT
        select_wby.next = wr_select_list[0]
        select_mbist1.next = dr_select_list[0]
        select_mbist2.next = dr_select_list[1]
        select_mbist3.next = dr_select_list[2]

    if monitor == False:
        return sib1_inst, selwir_inst, wir_inst, wdrmux_inst, wirmux_inst, wby_inst, \
               mbist1_inst, mbist2_inst, mbist3_inst, simbist1_inst, simbist2_inst, simbist3_inst, \
               sib2_inst, temp_SReg_inst, temp_inst, comp_SReg_inst, low_SReg_inst, high_SReg_inst, comp_inst, \
               led_SReg_inst, led_inst.rtl(), bridge, reset_logic, latch1, mux, \
               sib3_inst, mbist4_inst, simbist4_inst, mbist5_inst, simbist5_inst, muxsr_inst
    else:
        @instance
        def monitor_ijtag_si():
            print("\t\tIP_3({:s}): ijtag_si".format(path + '.' + name), ijtag_si)
            while 1:
                yield ijtag_si
                print("\t\tIP_3({:s}): ijtag_si".format(path + '.' + name), ijtag_si)

        @instance
        def monitor_ijtag_so():
            print("\t\tIP_3({:s}): ijtag_so".format(path + '.' + name), ijtag_so)
            while 1:
                yield ijtag_so
                print("\t\tIP_3({:s}): ijtag_so".format(path + '.' + name), ijtag_so)

        @instance
        def monitor_mux_select():
            print("\t\tIP_3({:s}): mux_select".format(path + '.' + name), mux_select)
            while 1:
                yield mux_select
                print("\t\tIP_3({:s}): mux_select".format(path + '.' + name), mux_select)

        @instance
        def monitor_from_ijtag_interface_SELECT():
            print("\t\tIP_3({:s}): from_ijtag_interface.SELECT".format(path + '.' + name), from_ijtag_interface.SELECT)
            while 1:
                yield from_ijtag_interface.SELECT
                print("\t\tIP_3({:s}): from_ijtag_interface.SELECT".format(path + '.' + name), from_ijtag_interface.SELECT)

        @instance
        def monitor_from_ijtag_interface_CAPTURE():
            print("\t\tIP_3({:s}): from_ijtag_interface.CAPTURE".format(path + '.' + name), from_ijtag_interface.CAPTURE)
            while 1:
                yield from_ijtag_interface.CAPTURE
                print("\t\tIP_3({:s}): from_ijtag_interface.CAPTURE".format(path + '.' + name), from_ijtag_interface.CAPTURE)

        @instance
        def monitor_from_ijtag_interface_SHIFT():
            print("\t\tIP_3({:s}): from_ijtag_interface.SHIFT".format(path + '.' + name), from_ijtag_interface.SHIFT)
            while 1:
                yield from_ijtag_interface.SHIFT
                print("\t\tIP_3({:s}): from_ijtag_interface.SHIFT".format(path + '.' + name), from_ijtag_interface.SHIFT)

        @instance
        def monitor_from_ijtag_interface_UPDATE():
            print("\t\tIP_3({:s}): from_ijtag_interface.UPDATE".format(path + '.' + name), from_ijtag_interface.UPDATE)
            while 1:
                yield from_ijtag_interface.UPDATE
                print("\t\tIP_3({:s}): from_ijtag_interface.UPDATE".format(path + '.' + name), from_ijtag_interface.UPDATE)

        @instance
        def monitor_from_ijtag_interface_RESET():
            print("\t\tIP_3({:s}): from_ijtag_interface.RESET".format(path + '.' + name), from_ijtag_interface.RESET)
            while 1:
                yield from_ijtag_interface.RESET
                print("\t\tIP_3({:s}): from_ijtag_interface.RESET".format(path + '.' + name), from_ijtag_interface.RESET)

        @instance
        def monitor_from_ijtag_interface_CLOCK():
            print("\t\tIP_3({:s}): from_ijtag_interface.CLOCK".format(path + '.' + name), from_ijtag_interface.CLOCK)
            while 1:
                yield from_ijtag_interface.CLOCK
                print("\t\tIP_3({:s}): from_ijtag_interface.CLOCK".format(path + '.' + name), from_ijtag_interface.CLOCK)

        return sib1_inst, selwir_inst, wir_inst, wdrmux_inst, wirmux_inst, wby_inst, \
               mbist1_inst, mbist2_inst, mbist3_inst, simbist1_inst, simbist2_inst, simbist3_inst, \
               sib2_inst, temp_SReg_inst, temp_inst, comp_SReg_inst, low_SReg_inst, high_SReg_inst, comp_inst, \
               led_SReg_inst, led_inst.rtl(), bridge, reset_logic, latch1, mux, \
               sib3_inst, mbist4_inst, simbist4_inst, mbist5_inst, simbist5_inst, muxsr_inst, \
               monitor_ijtag_si, monitor_ijtag_so, monitor_mux_select, monitor_from_ijtag_interface_SELECT, \
               monitor_from_ijtag_interface_CAPTURE, monitor_from_ijtag_interface_SHIFT, \
               monitor_from_ijtag_interface_UPDATE, monitor_from_ijtag_interface_RESET, \
               monitor_from_ijtag_interface_CLOCK


@block
def IP_3_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    H = bool(1)
    L = bool(0)
    ijtag_si = Signal(L)
    ijtag_so = Signal(L)
    from_ijtag_interface = IJTAGInterface()
    fast_ck = Signal(L)
    ck = Signal(L)
    pu_mbist1 = Signal(intbv(0, min=0, max=101))
    pu_mbist2 = Signal(intbv(0, min=0, max=101))
    pu_mbist3 = Signal(intbv(0, min=0, max=101))
    pu_mbist4 = Signal(intbv(0, min=0, max=101))
    pu_mbist5 = Signal(intbv(0, min=0, max=101))

    sib1_0 = '0'
    sib1_1 = '1'
    sib2_0 = '0'
    sib2_1 = '1'
    sib3_0 = '0'
    sib3_1 = '1'
    selwir_0 = '0'
    selwir_1 = '1'
    wby_0 = '0'
    wir_byp = '000'
    wir_bist1 = '110'
    wir_bist2 = '001'
    wir_bist3 = '101'
    wirmux_0 = '0'
    wirmux_1 = '1'
    bist_start = '00000001'
    width0 = len(sib1_0) + len(sib2_0) + len(sib3_0)  # BYPASS all SIBs
    width1wir = len(sib1_1) + len(selwir_1) + len(wir_byp) + len(sib2_0) + len(sib3_0)
    width1bist1 = len(sib1_1) + len(selwir_0) + len(wir_bist1) + len(sib2_0) + len(sib3_0)
    width1wby = len(sib1_1) + len(selwir_0) + len(wby_0) + len(sib2_0) + len(sib3_0)
    width_bist1_start_pattern = len(sib1_1) + len(selwir_1) + len(wir_bist1) + len(sib2_0) + len(sib3_0)
    sibs000 = Signal(intbv(sib1_0 + sib2_0 + sib3_0)[3:])
    sibs100 = Signal(intbv(sib1_1 + sib2_0 + sib3_0)[3:])
    sib1wir = Signal(intbv(sib1_1 + selwir_0 + wir_byp + sib2_0 + sib3_0))
    wby_pattern_0 = Signal(intbv(sib1_1 + selwir_0 + wby_0 + sib2_0 + sib3_0))
    wby_pattern_1 = Signal(intbv(sib1_1 + selwir_1 + wby_0 + sib2_0 + sib3_0))
    sel_bist1_pattern1 = Signal(intbv(sib1_1 + selwir_0 + wir_bist1 + sib2_0 + sib3_0))
    bist1_start_pattern = Signal(intbv(sib1_1 + selwir_0 + bist_start + sib2_0 + sib3_0))

    vec0in = Signal(intbv('000101010000'))
    vec0out = Signal(intbv('101010000000'))
    vec1in = Signal(intbv('000'))
    vec1out = Signal(intbv('000'))
    vec2in = Signal(intbv('100'))
    vec2out = Signal(intbv('000'))
    vec3in = Signal(intbv('1100000'))
    vec3out = Signal(intbv('1100000'))
    vec4in = Signal(intbv('1000000'))
    vec4out = Signal(intbv('1100000'))
    vec5in = Signal(intbv('10000'))
    vec5out = Signal(intbv('10000'))
    vec6in = Signal(intbv('11000'))
    vec6out = Signal(intbv('10000'))
    vec7in = Signal(intbv('1001100'))
    vec7out = Signal(intbv('1100000'))
    vec8in = Signal(intbv('100111000100'))
    vec8out = Signal(intbv('100000000000'))
    vec9in = Signal(intbv('100111000000'))
    vec9out = Signal(intbv('100000000100'))
    vec10in = Signal(intbv('110000000000'))
    vec10out = Signal(intbv('100000000100'))
    vec11in = Signal(intbv('1100000'))
    vec11out = Signal(intbv('1101100'))
    vec12in = Signal(intbv('1000000'))
    vec12out = Signal(intbv('1100000'))
    vec13in = Signal(intbv('10000'))
    vec13out = Signal(intbv('10000'))
    vec14in = Signal(intbv('11000'))
    vec14out = Signal(intbv('10000'))
    vec15in = Signal(intbv('1100000'))
    vec15out = Signal(intbv('1100000'))
    vec16in = Signal(intbv('0100000'))
    vec16out = Signal(intbv('1100000'))
    vec17in = Signal(intbv('000'))
    vec17out = Signal(intbv('000'))

    ip3_inst = IP_3("TOP", "IP_3", ijtag_si, ijtag_so, from_ijtag_interface,
         fast_ck, ck,
         pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
         monitor=monitor)

    # print simulation data to file
    file_data = open("IP_3.csv", 'w')  # file for saving data
    # print header to file
    print("{0},{1},{2},{3},{4},{5}".format("si", "ce", "se", "ue", "sel", "so"),
          file=file_data)
    # print data on each tap_interface.ClockDR
    @always(from_ijtag_interface.CLOCK.posedge)
    def print_data():
        """
        """
        # print in file
        # print.format is not supported in MyHDL 1.0
        print(ijtag_si, ",", from_ijtag_interface.CAPTURE, ",", from_ijtag_interface.SHIFT, ",",
              from_ijtag_interface.UPDATE, ",", from_ijtag_interface.SELECT, ",", ijtag_so, file=file_data)

    @instance
    def fast_ckgen():
        while True:
            fast_ck.next = not fast_ck
            yield delay(period // 10)

    @instance
    def ckgen():
        while True:
            ck.next = not ck
            yield delay(period)

    @instance
    def ijtagckgen():
        while True:
            from_ijtag_interface.CLOCK.next = not from_ijtag_interface.CLOCK
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        # Reset the network
        from_ijtag_interface.RESET.next = H
        yield delay(1)
        from_ijtag_interface.RESET.next = L
        yield delay(1)

        print("Scan vec0")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec0in)):
            print("ijtag_si.next = vec0in[i], vec0in[", i, "] = ", vec0in[i])
            ijtag_si.next = vec0in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec0out[", i, "] = ", vec0out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec0out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec1")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec1in)):
            print("ijtag_si.next = vec1in[i], vec1in[", i, "] = ", vec1in[i])
            ijtag_si.next = vec1in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec1out[", i, "] = ", vec1out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec1out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec2")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec2in)):
            print("ijtag_si.next = vec2in[i], vec2in[", i, "] = ", vec2in[i])
            ijtag_si.next = vec2in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec2out[", i, "] = ", vec2out[i], ", ijtag_so = ", ijtag_so)
            assert (ijtag_so == vec2out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec3")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec3in)):
            print("ijtag_si.next = vec3in[i], vec3in[", i, "] = ", vec3in[i])
            ijtag_si.next = vec3in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec3out[", i, "] = ", vec3out[i], ", ijtag_so = ", ijtag_so)
            # assert(ijtag_so == vec3out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec4")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec4in)):
            print("ijtag_si.next = vec4in[i], vec4in[", i, "] = ", vec4in[i])
            ijtag_si.next = vec4in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec4out[", i, "] = ", vec4out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec4out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec5")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec5in)):
            print("ijtag_si.next = vec5in[i], vec5in[", i, "] = ", vec5in[i])
            ijtag_si.next = vec5in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec5out[", i, "] = ", vec5out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec5out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec6")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec6in)):
            print("ijtag_si.next = vec6in[i], vec6in[", i, "] = ", vec6in[i])
            ijtag_si.next = vec6in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec6out[", i, "] = ", vec6out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec6out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec7")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec7in)):
            print("ijtag_si.next = vec7in[i], vec7in[", i, "] = ", vec7in[i])
            ijtag_si.next = vec7in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec7out[", i, "] = ", vec7out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec7out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec8")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec8in)):
            print("ijtag_si.next = vec8in[i], vec8in[", i, "] = ", vec8in[i])
            ijtag_si.next = vec8in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec8out[", i, "] = ", vec8out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec8out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        # wait for MBIST1 to finish running
        yield delay(10000)

        print("Scan vec9")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec9in)):
            print("ijtag_si.next = vec9in[i], vec9in[", i, "] = ", vec9in[i])
            ijtag_si.next = vec9in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec9out[", i, "] = ", vec9out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec9out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec10")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec10in)):
            print("ijtag_si.next = vec10in[i], vec10in[", i, "] = ", vec10in[i])
            ijtag_si.next = vec10in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec10out[", i, "] = ", vec10out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec10out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec11")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec11in)):
            print("ijtag_si.next = vec11in[i], vec11in[", i, "] = ", vec11in[i])
            ijtag_si.next = vec11in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec11out[", i, "] = ", vec11out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec11out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec12")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec12in)):
            print("ijtag_si.next = vec12in[i], vec12in[", i, "] = ", vec12in[i])
            ijtag_si.next = vec12in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec12out[", i, "] = ", vec12out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec12out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec13")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec13in)):
            print("ijtag_si.next = vec13in[i], vec13in[", i, "] = ", vec13in[i])
            ijtag_si.next = vec13in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec13out[", i, "] = ", vec13out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec13out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec14")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec14in)):
            print("ijtag_si.next = vec14in[i], vec14in[", i, "] = ", vec14in[i])
            ijtag_si.next = vec14in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec14out[", i, "] = ", vec14out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec14out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec15")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec15in)):
            print("ijtag_si.next = vec15in[i], vec15in[", i, "] = ", vec15in[i])
            ijtag_si.next = vec15in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec15out[", i, "] = ", vec15out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec15out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec16")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec16in)):
            print("ijtag_si.next = vec16in[i], vec16in[", i, "] = ", vec16in[i])
            ijtag_si.next = vec16in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec16out[", i, "] = ", vec16out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec16out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        print("Scan vec17")
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Capture value
        from_ijtag_interface.CAPTURE.next = H
        from_ijtag_interface.SELECT.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        # Write Shift value
        from_ijtag_interface.CAPTURE.next = L
        from_ijtag_interface.SHIFT.next = H
        for i in range(len(vec17in)):
            print("ijtag_si.next = vec17in[i], vec17in[", i, "] = ", vec17in[i])
            ijtag_si.next = vec17in[i]  # ########################################################### SHIFT
            yield from_ijtag_interface.CLOCK.posedge
            print("vec17out[", i, "] = ", vec17out[i], ", ijtag_so = ", ijtag_so)
            assert(ijtag_so == vec17out[i])
            yield from_ijtag_interface.CLOCK.negedge
        # Update
        from_ijtag_interface.SHIFT.next = L
        from_ijtag_interface.UPDATE.next = H
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        from_ijtag_interface.UPDATE.next = L

        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge
        yield from_ijtag_interface.CLOCK.posedge
        yield from_ijtag_interface.CLOCK.negedge

        raise StopSimulation()

    return ip3_inst, ijtagckgen, fast_ckgen, ckgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    H = bool(1)
    L = bool(0)
    ijtag_si = Signal(L)
    ijtag_so = Signal(L)
    from_ijtag_interface = IJTAGInterface()
    fast_ck = Signal(L)
    ck = Signal(L)
    pu_mbist1 = Signal(intbv(0, min=0, max=101))
    pu_mbist2 = Signal(intbv(0, min=0, max=101))
    pu_mbist3 = Signal(intbv(0, min=0, max=101))
    pu_mbist4 = Signal(intbv(0, min=0, max=101))
    pu_mbist5 = Signal(intbv(0, min=0, max=101))

    ip3_inst = IP_3("TOP", "IP_3", ijtag_si, ijtag_so, from_ijtag_interface,
         fast_ck, ck,
         pu_mbist1, pu_mbist2, pu_mbist3, pu_mbist4, pu_mbist5,
         monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    ip3_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="IP_3")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    ip3_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="IP_3")
    tb = IP_3_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="IP_3_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="IP_3_tb")


def main():
    tb = IP_3_tb(monitor=False)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
