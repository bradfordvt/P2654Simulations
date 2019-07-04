Module SReg {
  ScanInPort    SI;
  CaptureEnPort CE;
  ShiftEnPort   SE;
  CaptureEnPort CE;
  UpdateEnPort  UE;
  SelectPort    SEL;
  ResetPort     RST;
  TCKPort       TCK;
  ScanOutPort   SO { Source SR[0];
                     Attribute LaunchEdge = "Rising";}
  DataInPort    DI[8:0];
  DataOutPort   DO[8:0] { Source SR[0]; }
  ScanInterface SReg_client { Port SI; Port SO; Port SEL; }
  ScanRegister  SR[8:0] {
    ScanInSource SI; CaptureSource DI; ResetValue 9'b000000000;
  }
}