"""
My personal design of an I2C flexible host interface to the I2C bus.
"""
from myhdl import *


@block
def i2chost(clk, reset, tx, rx, control, status, scl_i, scl_o, scl_oen, sda_i, sda_o, sda_oen):
    # Control register bit signals
    start = Signal(bool(0))
    stop = Signal(bool(0))
    write = Signal(bool(0))
    execute = Signal(bool(0))
    master_ack = Signal(bool(0))
    # Status register bit signals
    busy = Signal(bool(0))
    ack_error = Signal(bool(0))
    # Internal signals
    execute_latched = Signal(bool(0))
    data_state = Signal(intbv(0, min=0, max=27))

    idle_wait, start1, start2, start3, shift1_change, shift1_stable, shift2_change, shift2_stable, \
        shift3_change, shift3_stable, shift4_change, shift4_stable, shift5_change, shift5_stable, \
        shift6_change, shift6_stable, shift7_change, shift7_stable, shift8_change, shift8_stable, \
        shift9w_change, shift9w_stable, shift9r_change, shift9r_stable, stop1, stop2, stop3 = range(27)

    @always_comb
    def comb0():
        execute.next = control[0]
        write.next = control[1]
        master_ack.next = control[2]
        start.next = control[3]
        stop.next = control[4]
        status.next[0] = busy
        status.next[1] = ack_error
        status.next[2] = scl_i

    @always(execute.posedge, busy.posedge)
    def execute_control():
        if busy:
            execute_latched.next = False
        elif execute and not busy:
            execute_latched.next = True
        else:
            execute_latched.next = False

    @always(clk.posedge, reset.posedge)
    def data_cycle():
        if data_state == idle_wait:
            ack_error.next = False
            scl_oen.next = False
            scl_o.next = False
            sda_oen.next = False
            sda_o.next = False
            if execute_latched:
                busy.next = True
                if start:
                    data_state.next = start1
                else:
                    data_state.next = shift1_change
        elif data_state == start1:
            scl_oen.next = True
            sda_oen.next = True
            scl_o.next = True
            sda_o.next = True
            data_state.next = start2
        elif data_state.next == start2:
            scl_o.next = True
            scl_oen.next = True
            sda_o.next = False
            sda_oen.next = False
            data_state.next = start3
        elif data_state == start3:
            scl_o.next = False
            scl_oen.next = False
            sda_o.next = False
            sda_oen.next = False
            data_state.next = shift1_change
        elif data_state == shift1_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[7]
                sda_oen.next = tx[7]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift1_stable
        elif data_state == shift1_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[7] = sda_i
            data_state.next = shift2_change
        elif data_state == shift2_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[6]
                sda_oen.next = tx[6]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift2_stable
        elif data_state == shift2_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[6] = sda_i
            data_state.next = shift3_change
        elif data_state == shift3_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[5]
                sda_oen.next = tx[5]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift3_stable
        elif data_state == shift3_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[5] = sda_i
            data_state.next = shift4_change
        elif data_state == shift4_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[4]
                sda_oen.next = tx[4]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift4_stable
        elif data_state == shift4_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[4] = sda_i
            data_state.next = shift5_change
        elif data_state == shift5_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[3]
                sda_oen.next = tx[3]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift5_stable
        elif data_state == shift5_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[3] = sda_i
            data_state.next = shift6_change
        elif data_state == shift6_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[2]
                sda_oen.next = tx[2]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift6_stable
        elif data_state == shift6_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[2] = sda_i
            data_state.next = shift7_change
        elif data_state == shift7_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[1]
                sda_oen.next = tx[1]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift7_stable
        elif data_state == shift7_stable:
            scl_oen.next = True
            scl_o.next = True
            if not write:
                rx.next[1] = sda_i
            data_state.next = shift8_change
        elif data_state == shift8_change:
            scl_oen.next = False
            scl_o.next = False
            if write:
                sda_o.next = tx[0]
                sda_oen.next = tx[0]
            else:
                sda_oen.next = True
                sda_o.next = True
            data_state.next = shift8_stable
        elif data_state == shift8_stable:
            scl_oen.next = True
            scl_o.next = True
            if write:
                data_state.next = shift9w_change
            else:
                rx.next[0] = sda_i
                data_state.next = shift9r_change
        elif data_state == shift9w_change:
            scl_o.next = False
            scl_oen.next = False
            sda_oen.next = True
            sda_o.next = True
            data_state.next = shift9w_stable
        elif data_state == shift9w_stable:
            scl_oen.next = True
            sda_oen.next = True
            scl_o.next = True
            sda_o.next = True
            if not sda_i:
                ack_error.next = True
            else:
                ack_error.next = False
            if stop:
                data_state.next = stop1
            else:
                data_state.next = idle_wait
                busy.next = False
        elif data_state == shift9r_change:
            scl_o.next = False
            scl_oen.next = False
            sda_oen.next = master_ack
            sda_o.next = master_ack
            data_state.next = shift9r_stable
        elif data_state == shift9r_stable:
            scl_oen.next = True
            scl_o.next = True
            if stop:
                data_state.next = stop1
            else:
                data_state.next = idle_wait
                busy.next = False
        elif data_state == stop1:
            scl_oen.next = False
            sda_o.next = False
            sda_oen.next = False
            data_state.next = stop2
        elif data_state == stop2:
            scl_oen.next = True
            sda_o.next = False
            sda_oen.next = False
            data_state.next = stop3
        elif data_state == stop3:
            scl_oen.next = True
            sda_oen.next = True
            scl_o.next = True
            sda_o.next = True
            busy.next = False
            data_state.next = idle_wait
    return comb0, execute_control, data_cycle



