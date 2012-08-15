// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SOCKETCONNECTIONPRIVATE_H
#define SOCKETCONNECTIONPRIVATE_H (1)

#include <cstddef>
#include <string>

#ifdef _WIN32
# include <windows.h>
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

        static bool invalidSocket (socket_t fd);

        static SocketConnectionPrivate * connectTcp
            ( std::string const & host
            , int port
            );

#ifndef _WIN32
        static SocketConnectionPrivate * connectUnix
            ( std::string const & path
            );
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
}

#endif
