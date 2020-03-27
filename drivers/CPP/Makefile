CPP		  = g++
CC		  = gcc
OBJ		  = atesim.o TelnetClient.o
LINKOBJ	  = atesim.o TelnetClient.o
LIBS	  =
INCS	  = -I"."
CXXINCS   = -I"."
DEFINES	  = -D__GNU__
CXXFLAGS  = -g $(CXXINCS) $(DEFINES)
CFLAGS    = -g $(INCS) $(DEFINES)
GPROF     = gprof.exe
RM        = rm -f
LINK      = ar
BIN		  = libatesim.a
LINKFLAGS = -L. -latesim -lcppunit

.PHONY: all all-before all-after clean clean-custom
all: all-before $(BIN) test_simservice TelnetClient_test all-after

clean: clean-custom
	$(RM) $(OBJ) $(BIN) libatesim.a test_simservice.o TelnetClient_test.o test_simservice TelnetClient_test

$(BIN): $(OBJ)
	$(LINK) rcu "$(BIN)" $(LINKOBJ)
	ranlib $@

atesim.o: $(GLOBALDEPS) atesim.cpp
	$(CPP) -c atesim.cpp -o atesim.o $(CXXFLAGS)

TelnetClient.o: $(GLOBALDEPS) TelnetClient.cpp TelnetClient.hpp
	$(CPP) -c TelnetClient.cpp -o TelnetClient.o $(CXXFLAGS)

test_simservice: test_simservice.cpp libatesim.a
	$(CPP) $(CXXFLAGS) -o $@ test_simservice.cpp $(OBJM) $(LINKFLAGS) $(LINKFLAGSLOG4) $(LIBLOG)

TelnetClient_test: TelnetClient_test.cpp libatesim.a
	$(CPP) $(CXXFLAGS) -o $@ TelnetClient_test.cpp $(OBJM) $(LINKFLAGS) $(LINKFLAGSLOG4) $(LIBLOG)
