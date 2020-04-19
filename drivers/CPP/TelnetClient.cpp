/*
 * TelnetClient.cpp
 *
 *  Created on: Mar 22, 2020
 *      Author: bvt
 */

#include "TelnetClient.hpp"

#include <stdlib.h>
#include <unistd.h>		// close() read() write()
#include <chrono>

typedef std::chrono::steady_clock _clock;

#define WILL 251
#define WONT 252
#define DO   253
#define DONT 254
#define IAC  255

namespace telnetclient {

TelnetClient::TelnetClient() {
	strcpy(hostname, "");
	myport = 0;
	sock = -1;
	irawq = 0;
	rawq[0] = '\0';
	mytimeout = 0;
	ai = NULL;
	rs = 0;
	first_write = true;
	eof = false;
}

TelnetClient::TelnetClient(const char* host, int port) {
	rawq[0] = '\0';
	irawq = 0;
	mytimeout = 0;
	ai = NULL;
	rs = 0;
	first_write = true;
	eof = false;
	sock = -1;
	open(host, port);
}

TelnetClient::~TelnetClient() {
	close();
	sock = -1;
}

void TelnetClient::open(const char* host, int port) {
	if(sock >= 0) {
		throw IOError("TelnetClient already open!");
	}
	strcpy(hostname, host);
	myport = port;
	char servname[50];
	memset(servname, 0, sizeof(servname));
	sprintf(servname, "%d", port);

	/* look up server host */
	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	if ((rs = getaddrinfo(hostname, servname, &hints, &ai)) != 0) {
		throw IOError(std::string("getaddrinfo() failed for ") + hostname + " " + gai_strerror(rs));
	}struct sockaddr_in addr;

    /* create server socket */
	if ((sock = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
		throw IOError(std::string("socket() failed: ") + strerror(errno));
	}

	/* bind server socket */
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
		::close(sock);
		throw IOError(std::string("bind() failed: ") + strerror(errno));
	}

	/* connect */
	if (connect(sock, ai->ai_addr, ai->ai_addrlen) == -1) {
		::close(sock);
		throw IOError(std::string("connect() failed: ") + strerror(errno));
	}

	/* free address lookup info */
	freeaddrinfo(ai);

	/* initialize poll descriptor */
	pfd.fd = sock;
	pfd.events = POLLIN;

	first_write = true;
}

void TelnetClient::close() {
	::close(sock);
	sock = -1;
}

void TelnetClient::write(const char* buffer) {
	if(first_write == true) {
		__sendComm(DONT, 1);	// suppress server echo (telehack.com DOES NOT honor this request)
		first_write = false;
	}
	if(::write(sock, buffer, strlen(buffer)) < 0) {
		IOError("write(buffer) failed!");
	}
}

void TelnetClient::write(const uint8_t* buffer, int sz) {
	if(::write(sock, buffer, sz) < 0) {
		throw IOError("write(sock, buffer, sz) failed!");
	}
}

const char* TelnetClient::read_until(const char* expected) {
	return read_until(expected, 0);
}

const char* TelnetClient::read_until(const char* expected, int timeout) {
	int n = strlen(expected);
	mytimeout = timeout;
	try {
		__process_rawq();
		char *fp;
		if((fp = strstr(cookedq, expected)) > 0) {
			int sz = fp - cookedq;
			strncpy(buffer, cookedq, sz + n);
			int cqlen = strlen(cookedq);
			memcpy(cookedq, cookedq + sz + n, sz + n + 1);
			return buffer;
		}
		while(eof == false) {
			int len = strlen(cookedq)-n;
			int i = std::max(0, len);
			__fill_rawq();
			__process_rawq();
			if((fp = strstr(&cookedq[i], expected)) > 0) {
				int sz = fp - cookedq;
				strncpy(buffer, cookedq, sz + n);
				buffer[sz + n] = '\0';
				int cqlen = strlen(cookedq);
				memcpy(cookedq, cookedq + sz + n, sz + n + 1);
				return buffer;
			}
		}
		if(buffer[0] == '\0' and eof == true and rawq[0] == '\0') {
			throw EOFError("telnet connection closed");
		}
	} catch(TimeoutError toe) {
		;
	}
	return read_very_lazy();
}

const char* TelnetClient::read_all() {
	__process_rawq();
	while(eof == false) {
		__fill_rawq();
		__process_rawq();
	}
	strcpy(buffer, cookedq);
	memset(cookedq, 0, sizeof(cookedq));
	return buffer;
}

const char* TelnetClient::read_some() {
    __process_rawq();
    while(strlen(cookedq) == 0 && eof == false) {
    	__fill_rawq();
    	__process_rawq();
    }
	strcpy(buffer, cookedq);
	memset(cookedq, 0, sizeof(cookedq));
	return buffer;
}

const char* TelnetClient::read_very_lazy() {
	strcpy(buffer, cookedq);
	memset(cookedq, 0, sizeof(cookedq));
	if(buffer[0] == '\0' and eof == true and rawq[0] == '\0') {
		throw EOFError("telnet connection closed");
	}
	return buffer;
}

void TelnetClient::__sendComm(uint8_t optCode, uint8_t code) {
	uint8_t comm[3]; comm[0]=IAC; comm[1]=optCode; comm[2]=code;
	write(comm,3);
}

void TelnetClient::__readComm() {
	uint8_t buff[2];
	buff[0] = __rawq_getchar();
	buff[1] = __rawq_getchar();
	if(buff[0] == WILL) {
		__sendComm(DONT, buff[1]);
	}
	if(buff[0] == DO) {
		__sendComm(WONT, buff[1]);
	}
}

void TelnetClient::__process_rawq() {
	uint8_t c[2];
	c[1] = '\0';
	while(strlen((const char*)rawq) > 0) {
		c[0] = __rawq_getchar();
		if(c[0] == IAC) {
			__readComm();
		}
		else if(c[0] == '\0') {
			continue;
		}
		else {
			if(strlen(cookedq) + 1 < RAWQLEN) {
				strcat(cookedq, (const char*)c);
			}
			else {
				throw IOError("__process_rawq() overflow!");
			}
		}
	}
}

uint8_t TelnetClient::__rawq_getchar() {
	if(strlen((const char*)rawq) == 0) {
		__fill_rawq();
	}
	uint8_t c;
	c = rawq[irawq];
	irawq += 1;
	if(irawq >= strlen((const char*)rawq)) {
		memset(rawq, 0, sizeof(rawq));
		irawq = 0;
	}
	return c;
}

void TelnetClient::__fill_rawq() {
	uint8_t buff[200];
	if(irawq >= strlen((const char*)rawq)) {
		memset(rawq, 0, sizeof(rawq));
		irawq = 0;
	}
	_clock::time_point start = _clock::now();
	while (true) {
		int rc = poll(&pfd, 1, (3 * 60 * 1000));
		if(rc == -1) {
			printf("Poll rc = -1\n");
			break;
		} else if (rc == 0) {
			eof = true;
			throw TimeoutError("__fill_rawq() Timeout!");
			break;
		}
		unsigned long long seconds_elapsed = std::chrono::duration_cast<std::chrono::seconds>( _clock::now() - start ).count();
		if(mytimeout > 0 && int(seconds_elapsed) >= mytimeout) {
			eof = true;
			throw TimeoutError("__fill_rawq() Timeout!");
		}
		/* read from client */
		if (pfd.revents & POLLIN) {
			if ((rs = ::recv(sock, buff, sizeof(buff), 0)) > 0) {
				if(strlen((const char*)rawq) + rs <= RAWQLEN) {
					strncat((char*)rawq, (const char*)buff, rs);
					break;
				}
				else {
					throw IOError("__fill_rawq() overflow detected!");
				}
			}
			else if(rs == 0) {
				eof = true;
			}
			else {
				throw IOError(std::string("recv(client) failed: ") + strerror(errno));
			}
		}
	}
}

} /* namespace telnetclient */
