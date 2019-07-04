Module sib_mux_post {
	ScanInPort SI;
	CaptureEnPort CE;
	ShiftEnPort SE;
	UpdateEnPort UE;
	SelectPort SEL;
	ResetPort RST;
	TCKPort TCK;
	ScanOutPort SO { Source SIBMux;
	                 Attribute LaunchEdge = "Rising"; }
	ScanInterface client {
		port SI; port CE; port SE; port UE;
		port SEL; port RST; port TCK; port SO;
	}
	ScanInPort fromSO;
	ToCaptureEnPort toCE;
	ToShiftEnPort toSE;
	ToUpdateEnPort toUE;
	ToSelectPort toSEL;
	ToResetPort toRST;
	ToTCKPort toTCK;
	ScanOutPort toSI { Source SR;
	                   Attribute LaunchEdge = "Rising";}
	ScanInterface host {
		port fromSO; port toCE; port toSE; port toUE;
		port toSEL; port toRST; port toTCK; port toSI;
	}
	ScanRegister SR {
		ScanInSource SI; CaptureSource SR; ResetValue 1'b0;
	}
	ScanMux SIBmux SelectedBy SR {
		1'b0 : SR;
		1'b1 : fromSO;
	}
}
