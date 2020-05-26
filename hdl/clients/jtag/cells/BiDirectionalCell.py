"""
/**********************************************************************************
*																																									*
*		BiDirectional Cell:																														*
*																																									*
*		FromCore: Value that comes from on-chip logic and goes to pin									*
*		ToCore: Value that is read-in from the pin and goes to core										*
*		FromPreviousBSCell: Value from previous boundary scan cell										*
*		ToNextBSCell: Value for next boundary scan cell																*
*		CaptureDR, ShiftDR, UpdateDR: TAP states																			*
*		extest: Instruction Register Command																					*
*		TCK: Test Clock																																*
*		BiDirPin: Bidirectional pin connected to this BS cell													*
*		FromOutputEnable: This pin comes from core or ControlCell											*
*																																									*
*		Signal that is connected to BiDirPin comes from core or BS chain. Tristate		*
*		control is generated in core or BS chain (ControlCell).												*
*																																									*
**********************************************************************************/
"""
from myhdl import *


@block
def BiDirectionalCell( FromCore, ToCore, FromPreviousBSCell, CaptureDR, ShiftDR, UpdateDR,
                       extest, TCK, ToNextBSCell, FromOutputEnable, InPad, OutPad, EnablePad):
    Latch = Signal(bool(0))
    ShiftedControl = Signal(bool(0))
    SelectedInput = Signal(bool(0))

    @always_comb
    def sel_process():
        if CaptureDR:
            SelectedInput.next = InPad
        else:
            SelectedInput.next = FromPreviousBSCell

    @always(TCK.posedge)
    def latch_logic():
        if CaptureDR or ShiftDR:
            Latch.next = SelectedInput

    @always(TCK.negedge)
    def to_logic():
        ToNextBSCell.next = Latch

    @always(TCK.negedge)
    def update_logic():
        if UpdateDR:
            ShiftedControl.next = ToNextBSCell

    MuxedSignal = Signal(bool(0))

    @always_comb
    def mux_process1():
        if extest:
            MuxedSignal.next = ShiftedControl
        else:
            MuxedSignal.next = FromCore

    @always_comb
    def mux_process2():
        if FromOutputEnable:
            OutPad.next = MuxedSignal
            EnablePad.next = True
        else:
            OutPad.next = False
            EnablePad.next = False

    @always_comb
    def mux_process3():
        # BUF Buffer (.I(BiDirPin), .O(ToCore))
        ToCore.next = InPad

    return sel_process, latch_logic, to_logic, update_logic, mux_process1, mux_process2, mux_process3
