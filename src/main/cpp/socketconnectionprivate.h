// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SOCKETCONNECTIONPRIVATE_H
#define SOCKETCONNECTIONPRIVATE_H (1)

#include <cstddef>
#ifdef _WIN32
#include <windows.h>
#endif

#include "connectionprivate.h"

namespace conveyor
{
    class SocketConnectionPrivate : public ConnectionPrivate
    {
    public:
		#ifdef _WIN32
		typedef SOCKET socket_t;
		#else
		typedef int socket_t;
		#endif
	
        SocketConnectionPrivate (socket_t fd);
        ~SocketConnectionPrivate (void);

        bool eof (void);
        ssize_t read (char * buffer, std::size_t length);
        void write (char const * buffer, std::size_t length);
        void cancel (void);

    private:
        socket_t  m_fd;
        bool m_eof;
        bool volatile m_cancel;
    };
	
	// Abstraction for checking validity of a socket file descriptor on windows/*nix
	bool invalidSocket (SocketConnectionPrivate::socket_t const fd);
}

#endif
