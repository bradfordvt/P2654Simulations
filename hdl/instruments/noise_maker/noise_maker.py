"""
Copyright (c) 2019 Bradford G. Van Treuren
See the licence file in the top directory

Noise Maker
Simulated instrument to inject noise into the power supply for the Rearick Use Case model.
"""
from myhdl import *
import os
import os.path

period = 20  # clk frequency = 50 MHz
MAX_TOGGLES = 20
MAX_STAGES = 10


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
    @always(ck.posedge)
    def ck_cond():
        noise.next = num_toggles * num_stages

    return ck_cond


@block
def noise_maker_tb(monitor=False):
    """
    Test bench interface for a quick test of the operation of the design
    :param monitor: False=Do not turn on the signal monitors, True=Turn on the signal monitors
    :return: A list of generators for this logic
    """
    num_toggles = Signal(intbv(0, min=0, max=MAX_TOGGLES))
    num_stages = Signal(intbv(0, min=0, max=MAX_STAGES))
    noise = Signal(intbv(0, min=0, max=(MAX_TOGGLES * MAX_STAGES)))
    ck = Signal(bool(0))

    nm_inst = noise_maker("TOP", "NM0", num_toggles, num_stages, ck, noise, monitor=monitor)

    @instance
    def clkgen():
        while True:
            ck.next = not ck
            yield delay(period // 2)

    @instance
    def stimulus():
        """
        Perform instruction decoding for various instructions
        :return:
        """
        assert(noise == 0)
        num_toggles.next = 5
        num_stages.next = 4
        yield delay(100)
        assert(noise == 20)
        num_toggles.next = 1
        num_stages.next = 2
        yield delay(100)
        assert(noise == 2)
        # try:
        #     num_toggles.next = MAX_TOGGLES
        #     num_stages.next = MAX_STAGES
        #     yield delay(100)
        #     assert(noise == MAX_TOGGLES*MAX_STAGES)
        # except ValueError as ve:
        #     print("Did not catch max boundary condition!")

        raise StopSimulation()

    return nm_inst, clkgen, stimulus


def convert():
    """
    Convert the myHDL design into VHDL and Verilog
    :return:
    """
    num_toggles = Signal(intbv(0, min=0, max=MAX_TOGGLES))
    num_stages = Signal(intbv(0, min=0, max=MAX_STAGES))
    noise = Signal(intbv(0, min=0, max=MAX_TOGGLES*MAX_STAGES))
    ck = Signal(bool(0))

    nm_inst = noise_maker("TOP", "NM0", num_toggles, num_stages, ck, noise, monitor=False)

    vhdl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vhdl')
    if not os.path.exists(vhdl_dir):
        os.mkdir(vhdl_dir, mode=0o777)
    nm_inst.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="noise_maker")
    verilog_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verilog')
    if not os.path.exists(verilog_dir):
        os.mkdir(verilog_dir, mode=0o777)
    nm_inst.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="noise_maker")
    tb = noise_maker_tb(monitor=False)
    tb.convert(hdl="VHDL", initial_values=True, directory=vhdl_dir, name="noise_maker_tb")
    tb.convert(hdl="Verilog", initial_values=True, directory=verilog_dir, name="noise_maker_tb")


def main():
    tb = noise_maker_tb(monitor=True)
    tb.config_sim(trace=True)
    tb.run_sim()
    convert()


if __name__ == '__main__':
    main()
