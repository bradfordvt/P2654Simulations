CPP		  = g++
CC		  = gcc
OBJ		  = atesim.o TelnetClient.o telnetlib.o Socket.o
LINKOBJ	  = atesim.o TelnetClient.o telnetlib.o
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
LINKFLAGS = -L. -latesim -lcppunit -lws2_32

.PHONY: all all-before all-after clean clean-custom
all: all-before $(BIN) test_simservice TelnetClient_test test_telnetlib all-after

clean: clean-custom
	$(RM) $(OBJ) $(BIN) libatesim.a test_simservice.o TelnetClient_test.o telnetlib.o test_simservice TelnetClient_test test_telnetlib

$(BIN): $(OBJ)
	$(LINK) rcu "$(BIN)" $(LINKOBJ)
	ranlib $@

Socket.o: $(GLOBALDEPS) Socket.cpp
	$(CPP) -c Socket.cpp -o Socket.o $(CXXFLAGS)

atesim.o: $(GLOBALDEPS) atesim.cpp atesim.hpp
	$(CPP) -c atesim.cpp -o atesim.o $(CXXFLAGS)

TelnetClient.o: $(GLOBALDEPS) TelnetClient.cpp TelnetClient.hpp
	$(CPP) -c TelnetClient.cpp -o TelnetClient.o $(CXXFLAGS)

telnetlib.o: $(GLOBALDEPS) telnetlib.cpp telnetlib.hpp
	$(CPP) -c telnetlib.cpp -o telnetlib.o $(CXXFLAGS)

test_simservice: test_simservice.cpp libatesim.a
	$(CPP) $(CXXFLAGS) -o $@ test_simservice.cpp $(OBJM) $(LINKFLAGS) $(LINKFLAGSLOG4) $(LIBLOG)

TelnetClient_test: TelnetClient_test.cpp libatesim.a
	$(CPP) $(CXXFLAGS) -o $@ TelnetClient_test.cpp $(OBJM) $(LINKFLAGS) $(LINKFLAGSLOG4) $(LIBLOG)

test_telnetlib: test_telnetlib.cpp libatesim.a
	$(CPP) $(CXXFLAGS) -o $@ test_telnetlib.cpp $(OBJM) $(LINKFLAGS) $(LINKFLAGSLOG4) $(LIBLOG)

