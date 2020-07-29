/*
 * TelnetClient.cpp
 *
 *  Created on: Mar 22, 2020
 *      Author: bvt
 */

#include "TelnetClient.hpp"

#include <stdlib.h>
#if _WIN32
#include <WinSock2.h>

#include <string>
#else
#include <unistd.h>		// close() read() write()
#endif
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
	sock = INVALID_SOCKET;
	irawq = 0;
	rawq[0] = '\0';
	mytimeout = 0;
	ai = NULL;
	rs = 0;
	first_write = true;
	debug_level = 0;
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
	sock = INVALID_SOCKET;
	debug_level = 0;
	open(host, port);
}

TelnetClient::~TelnetClient() {
	close();
	sock = INVALID_SOCKET;
}

void TelnetClient::open(const char* host, int port) {
    fprintf(stderr, "sock = %d", sock);
	if(sock != INVALID_SOCKET) {
		throw IOError("TelnetClient already open!");
	}
#ifdef __WIN32__
    WSADATA wsa;
    fprintf(stderr, "\nInitialising Winsock...\n");
    if (WSAStartup(MAKEWORD(2,2),&wsa) != 0)
    {
        char msg[512];
        sprintf(msg, "Failed. Error Code : %d",WSAGetLastError());
        throw IOError(msg);
    }
#endif
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
		char buff[200];
		sprintf(buff, "getaddrinfo() failed for %s %d", hostname, rs);
		throw IOError(buff);
	}

	struct sockaddr_in addr;

    /* create server socket */
	if ((sock = socket(AF_INET, SOCK_STREAM, 0)) == INVALID_SOCKET) {
#ifdef __WIN32__
		throw IOError(std::string("socket() failed: ") + strerror(WSAGetLastError()));
#else
		throw IOError(std::string("socket() failed: ") + strerror(errno));
#endif
	}

	/* bind server socket */
	memset(&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) == -1) {
	    close();
		throw IOError(std::string("bind() failed: ") + strerror(errno));
	}

	/* connect */
	if (connect(sock, ai->ai_addr, ai->ai_addrlen) == SOCKET_ERROR) {
	    close();
		throw IOError(std::string("connect() failed: ") + strerror(errno));
	}

	/* free address lookup info */
	freeaddrinfo(ai);

	/* initialize poll descriptor */
#ifdef __WIN32__
    //clear the socket fd set
    // FD_ZERO(&(this->fds));
    // FD_SET( (this->sock) , &(this->fds));
#else
	pfd.fd = sock;
	pfd.events = POLLIN;
#endif

	first_write = true;
}

void TelnetClient::close() {
#ifdef __WIN32__
	closesocket(sock);
	WSACleanup();
#else
	::close(sock);
#endif
	sock = INVALID_SOCKET;
}

void TelnetClient::write(const char* buffer) {
	if(first_write == true) {
		first_write = false;
		__sendComm(DONT, 1);	// suppress server echo (telehack.com DOES NOT honor this request)
	}
	if (debug_level > 0)  {
        fprintf(stderr, "In write(): calling send(%d,\n\t", sock);
        int sz = strlen(buffer);
        for (int j = 0; j < sz; j++) {
            fprintf(stderr, "%c,", buffer[j]);
        }
        fprintf(stderr, "\n\t%d.\n\t0)\n", sz);
        fflush(stderr);
	}
#ifdef __WIN32__
    if(send(sock, buffer, strlen(buffer), 0) < 0) {
        throw IOError(std::string("write(buffer) failed: ") + strerror(WSAGetLastError()));
    }
#else
	if(::write(sock, buffer, strlen(buffer)) < 0) {
		throw IOError("write(buffer) failed!");
	}
#endif
}

void TelnetClient::write(const char* buffer, int sz) {
	if(first_write == true) {
		first_write = false;
		__sendComm(DONT, 1);	// suppress server echo (telehack.com DOES NOT honor this request)
	}
    if (debug_level > 0) {
        fprintf(stderr, "In write(): calling send(%d,\n\t", sock);
        for (int j = 0; j < sz; j++) {
            fprintf(stderr, "%c,", buffer[j]);
        }
        fprintf(stderr, "\n\t%d.\n\t0)\n", sz);
        fflush(stderr);
    }
#ifdef __WIN32__
    if(send(sock, buffer, sz, 0) < 0) {
        throw IOError(std::string("write(sock, buffer, sz) failed: ") + strerror(WSAGetLastError()));
    }
#else
	if(::write(sock, buffer, sz) < 0) {
		throw IOError("write(sock, buffer, sz) failed!");
	}
#endif
}

const char* TelnetClient::read_until(const char* expected) {
	return read_until(expected, 0);
}

const char* TelnetClient::read_until(const char* expected, int timeout) {
    long deadline;
	int n = strlen(expected);
	mytimeout = timeout;
	if (debug_level > 0) {
        fprintf(stderr, "In read_until(): timeout = %d\n", timeout);
        fprintf(stderr, "In read_until(): expected = %s\n", expected);
        fflush(stderr);
    }
	try {
	    memset(buffer, 0, sizeof(buffer));
		__process_rawq();
		if (debug_level > 0) {
            fprintf(stderr, "In read_until(): cookedq = %s\n", cookedq);
            if(eof == false) {
                fprintf(stderr, "In read_until(): eof == false.\n");
            }
            else {
                fprintf(stderr, "In read_until(): eof == true.\n");
            }
            fflush(stderr);
        }
		char *fp;
		if((fp = strstr(cookedq, expected)) > 0) {
			int sz = fp - cookedq;
			strncpy(buffer, cookedq, sz + n);
			buffer[sz + n] = '\0';
			int cqlen = strlen(cookedq);
			memcpy(cookedq, cookedq + sz + n, sz + n + 1);
			if (debug_level > 0) {
                fprintf(stderr, "In read_until(): returning(1) buffer = %s\n", buffer);
                fprintf(stderr, "In read_until(): cookedq(1) cookedq = %s\n", cookedq);
                fflush(stderr);
            }
			return buffer;
		}
#ifdef __WIN32__
        SYSTEMTIME start;
        if (timeout != 0) {
            GetSystemTime(&start);
        }
        if (debug_level > 0) {
            fprintf(stderr, "In read_until(): Setting timeout to %d.\n", timeout);
            fflush(stderr);
        }
        DWORD timeout_msec = timeout * 1000;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout_msec, sizeof timeout_msec);
		while(eof == false) {
			int len = strlen(cookedq)-n;
#if _MSC_VER >= 1900
			int i = max(0, len);
#else
			int i = std::max(0, len);
#endif
			__fill_rawq();
			__process_rawq();
			if((fp = strstr(&cookedq[i], expected)) > 0) {
				int sz = fp - cookedq;
				strncpy(buffer, cookedq, sz + n);
				buffer[sz + n] = '\0';
				int cqlen = strlen(cookedq);
				memcpy(cookedq, cookedq + sz + n, sz + n + 1);
				if (debug_level > 0) {
                    fprintf(stderr, "In read_until(): returning(2) buffer = %s\n", buffer);
                    fflush(stderr);
                }
				return buffer;
			}
            SYSTEMTIME end;
            if (timeout != 0) {
                GetSystemTime(&end);
                if (end.wSecond - start.wSecond > timeout) {
                    throw TimeoutError("read_until() timeout.");
                }
            }
		}
		if(buffer[0] == '\0' && eof == true && rawq[0] == '\0') {
			throw EOFError("telnet connection closed");
		}
#else
        _clock::time_point start = _clock::now();
        if (debug_level > 0) {
            fprintf(stderr, "In read_until(): Setting timeout to %d.\n", timeout);
            fflush(stderr);
        }
        struct timeval tv;
        tv.tv_sec = timeout;
        tv.tv_usec = 0;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(tv));
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
				if (debug_level > 0) {
                    fprintf(stderr, "In read_until(): returning(2) buffer = %s\n", buffer);
                    fflush(stderr);
                }
				return buffer;
			}
            _clock::time_point end = _clock::now();
            if (timeout != 0) {
                if (std::chrono::duration_cast<std::chrono::seconds>(end - start).count() > timeout) {
                    throw TimeoutError("read_until() timeout.");
                }
            }
		}
		if(buffer[0] == '\0' && eof == true && rawq[0] == '\0') {
			throw EOFError("telnet connection closed");
		}
#endif
	} catch(TimeoutError toe) {
	    if (debug_level > 0) {
	        fprintf(stderr, "In read_until(): Timeout detected!\n");
	        fflush(stderr);
	    }
		throw TimeoutError("read_until() timeout.");
	}
	return read_very_lazy();
}

const char* TelnetClient::read_all() {
    memset(buffer, 0, sizeof(buffer));
	__process_rawq();
	while(eof == false) {
		__fill_rawq();
		__process_rawq();
	}
	if (debug_level > 0) {
        fprintf(stderr, "In read_all(): cookedq = %s\n", cookedq);
        fflush(stderr);
    }
    strcpy(buffer, cookedq);
    if (debug_level > 0) {
        fprintf(stderr, "In read_all(): buffer = %s\n", buffer);
        fflush(stderr);
    }
	memset(cookedq, 0, sizeof(cookedq));
	return buffer;
}

const char* TelnetClient::read_some() {
    memset(buffer, 0, sizeof(buffer));
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
    if (debug_level > 0) {
        fprintf(stderr, "In read_very_lazy(): cookedq = %s\n", cookedq);
        fflush(stderr);
    }
    memset(buffer, 0, sizeof(buffer));
    strncpy(buffer, cookedq, RAWQLEN);
    buffer[RAWQLEN] = '\0';
    if (debug_level > 0) {
        fprintf(stderr, "In read_very_lazy(): buffer = %s\n", buffer);
        fflush(stderr);
    }
	memset(cookedq, 0, RAWQLEN);
	if(buffer[0] == '\0' && eof == true && rawq[0] == '\0') {
		throw EOFError("telnet connection closed");
	}
	return buffer;
}

void TelnetClient::__sendComm(uint8_t optCode, uint8_t code) {
	char comm[3]; comm[0]=IAC; comm[1]=optCode; comm[2]=code;
	if (debug_level > 0) {
    	fprintf(stderr, "*");
	    fflush(stderr);
	}
	write(comm,3);
}

void TelnetClient::__readComm() {
	uint8_t buff[2];
	buff[0] = __rawq_getchar();
	buff[1] = __rawq_getchar();
	if(buff[0] == WILL) {
	    if (debug_level > 0) {
            fprintf(stderr, "In __readComm(): Detected WILL command.  Sending DONT %c.\n", buff[1]);
            fflush(stderr);
        }
		__sendComm(DONT, buff[1]);
	}
	if(buff[0] == DO) {
	    if (debug_level > 0) {
            fprintf(stderr, "In __readComm(): Detected DO command.  Sending WONT %c.\n", buff[1]);
            fflush(stderr);
        }
		__sendComm(WONT, buff[1]);
	}
}

void TelnetClient::__process_rawq() {
    if (debug_level > 0) {
        fprintf(stderr, "In __process_rawq(): rawq = %s\n", rawq);
        fflush(stderr);
    }
	uint8_t c[2];
	c[1] = '\0';
	while(strlen((const char*)rawq) > 0) {
		c[0] = __rawq_getchar();
		if(c[0] == IAC) {
		    if (debug_level > 0) {
                fprintf(stderr, "In __process_rawq(): Detected IAC.  Calling __readComm().\n");
                fflush(stderr);
            }
			__readComm();
		}
		else if(c[0] == '\0') {
		    if (debug_level > 0) {
                fprintf(stderr, "In __process_rawq(): Found NULL.");
                fflush(stderr);
            }
			continue;
		}
		else {
			if(strlen(cookedq) + 1 < RAWQLEN) {
			    if (debug_level > 0) {
                    fprintf(stderr, "In __process_rawq(): Copying from rawq to cookedq (%c)\n", c);
                    fflush(stderr);
                }
                strcat(cookedq, (const char*)c);
                if (debug_level > 0) {
                    fprintf(stderr, "In __process_rawq(): cookedq = %s\n", cookedq);
                    fflush(stderr);
                }
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
	if (debug_level > 0) {
        fprintf(stderr, "In __rawq_getchar(): returning %c\n", c);
        fflush(stderr);
    }
	return c;
}

void TelnetClient::__fill_rawq() {
#ifdef __WIN32__
    char buff[RAWQLEN];
#else
	uint8_t buff[RAWQLEN];
#endif
    memset(buff, 0, sizeof(buff));
	if(irawq >= strlen((const char*)rawq)) {
		memset(rawq, 0, sizeof(rawq));
		irawq = 0;
	}
#ifdef __WIN32__
    SYSTEMTIME start;
    GetSystemTime(&start);
	while (true) {
        u_long rc = 0;
        if (ioctlsocket(sock, FIONREAD, &rc) != NO_ERROR) {
            throw IOError(std::string("ioctlsocket(client) failed: ") + strerror(errno));
            break;
        }

/*
        if (rc == 0) {
            if (debug_level > 0) {
                fprintf(stderr, "In __fill_rawq(): Detected eof for rc == 0\n");
                fflush(stderr);
            }
            eof = true;
            break;
        }
*/
        SYSTEMTIME end;
        GetSystemTime(&end);
        if (end.wSecond - start.wSecond >= mytimeout) {
            eof = true;
            throw TimeoutError("__fill_rawq() Timeout!");
        }
        if(mytimeout > 0 && rc == 0) {
            continue;
        }
        else if  (rc == 0) {
            if (debug_level > 0) {
                fprintf(stderr, "In __fill_rawq(): Detected eof for rc == 0\n");
                fflush(stderr);
            }
            eof = true;
            break;
        }
        if (rc > RAWQLEN) rc = RAWQLEN;

        int rv = recv(sock, buff, rc, 0);
        if (rv < 0) {
            throw IOError(std::string("recv(client) failed: ") + strerror(errno));
            break;
        }
        else if ( rv == 0) {
            if (debug_level > 0) {
                fprintf(stderr, "In __fill_rawq(): Detected eof for rv == 0\n");
                fflush(stderr);
            }
            eof = true;
            break;
        }
        else {
            if (debug_level > 0) {
                fprintf(stderr, "In __fill_rawq(): recv() returned %s\n", buff);
                fflush(stderr);
            }
            if(strlen((const char*)rawq) + rs <= RAWQLEN) {
                if (debug_level > 0) {
                    fprintf(stderr, "In __fill_rawq(): copying buff to rawq.\n");
                    fflush(stderr);
                }
                strncat((char*)rawq, (const char*)buff, rv);
                if (debug_level > 0) {
                    fprintf(stderr, "In __fill_rawq(): rawq = %s\n", rawq);
                    fflush(stderr);
                }
                break;
            }
            else {
                throw IOError("__fill_rawq() overflow detected!");
            }
        }
    }
#else
	_clock::time_point start = _clock::now();
	while (true) {
		int rc = poll(&pfd, 1, (3 * 60 * 1000));
		if(rc == -1) {
		    if (debug_level > 0) {
    			fprintf(stderr, "Poll rc = -1\n");
    			fflush(stderr);
    	    }
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
		if(mytimeout > 0 && rc == 0) {
		    continue;
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
#endif
}

} /* namespace telnetclient */
