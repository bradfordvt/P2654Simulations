/*
 * TelnetClient.h
 *
 *  Created on: Mar 22, 2020
 *      Author: bvt
 */

#ifndef TELNETCLIENT_HPP_
#define TELNETCLIENT_HPP_

#include <string>
#include <cstdio>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>	// uint8_t, addrinfo
#include <arpa/inet.h>
#include <netdb.h>
#include <poll.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <termios.h>
#include <unistd.h>

#define RAWQLEN 2048

namespace telnetclient {

class TelnetClient {
public:
	class IOError:  public std::exception
	{
	    std::string what_message;
	public:
	    IOError(const char* message) : what_message(message) { };
	    IOError(std::string message) : what_message(message.c_str()) { };
	    const char* what()
	    {
	        return what_message.c_str();
	    }
	};

	class TimeoutError:  public std::exception
	{
	    std::string what_message;
	public:
	    TimeoutError(const char* message) : what_message(message) { };
	    TimeoutError(std::string message) : what_message(message.c_str()) { };
	    const char* what()
	    {
	        return what_message.c_str();
	    }
	};

	class EOFError:  public std::exception
	{
	    std::string what_message;
	public:
	    EOFError(const char* message) : what_message(message) { };
	    EOFError(std::string message) : what_message(message.c_str()) { };
	    const char* what()
	    {
	        return what_message.c_str();
	    }
	};

	TelnetClient();
	TelnetClient(const char* host, int port);
	virtual ~TelnetClient();

	void open(const char* host, int port);
	void close();

	void write(const char* buffer);
	void write(const uint8_t* buffer, int sz);
	const char* read_until(const char* expected);
	const char* read_until(const char* expected, int timeout);
	const char* read_all();
	const char* read_some();
	const char* read_very_lazy();
private:
	void __sendComm(uint8_t optCode, uint8_t code);
	void __readComm();
	void __process_rawq();
	uint8_t __rawq_getchar();
	void __fill_rawq();



	char hostname[50];
	int myport;
	struct addrinfo hints;
	struct addrinfo *ai;
	ssize_t rs;
	int sock;
	struct sockaddr_in addr;
	struct pollfd pfd;
	bool first_write;
	uint8_t rawq[RAWQLEN];
	char cookedq[RAWQLEN];
	char buffer[RAWQLEN];
	int irawq;
	int mytimeout;
	bool eof;

};

} /* namespace telnetclient */

#endif /* TELNETCLIENT_HPP_ */
