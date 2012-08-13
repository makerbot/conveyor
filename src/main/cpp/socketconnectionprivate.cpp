// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstddef>
#include <cstring>
#include <exception>
#include <sys/time.h>
#include <sys/types.h>
#include <unistd.h>

#ifdef _WIN32
# include <winsock2.h>
# include <ws2tcpip.h>
#else
# include <netinet/in.h>
# include <netdb.h>
# include <sys/select.h>
# include <sys/socket.h>
#endif

#include "connectionprivate.h"
#include "socketconnectionprivate.h"

namespace conveyor
{
    SocketConnectionPrivate *
    SocketConnectionPrivate::connectTcp
        ( std::string const & host
        , int const port
        )
    {
        SocketConnectionPrivate::socket_t const fd
            ( socket (PF_INET, SOCK_STREAM, IPPROTO_TCP)
            );
        if (SocketConnectionPrivate::invalidSocket (fd))
        {
            throw std::exception ();
        }
        else
        {
            struct sockaddr_in address;
            memset (& address, 0, sizeof (struct sockaddr_in));
            address.sin_family = AF_INET;
            address.sin_port = htons (port);
            struct hostent * hostent;
            hostent = gethostbyname (host.c_str ());
            if (0 == hostent)
            {
                throw std::exception ();
            }
            else
            {
                std::memcpy
                    ( & address.sin_addr.s_addr
                    , hostent->h_addr_list[0]
                    , hostent->h_length
                    );
                if (0 != connect
                    ( fd
                    , reinterpret_cast <struct sockaddr *> (& address)
                    , sizeof (struct sockaddr_in)
                    ))
                {
                    throw std::exception ();
                }
                else
                {
                    SocketConnectionPrivate * const private_
                        ( new SocketConnectionPrivate (fd)
                        );
                    return private_;
                }
            }
        }
    }

    SocketConnectionPrivate::SocketConnectionPrivate (socket_t const fd)
        : m_fd (fd)
        , m_eof (false)
        , m_cancel (false)
    {
    }

    SocketConnectionPrivate::~SocketConnectionPrivate (void)
    {
        close (this->m_fd);
    }

    bool
    SocketConnectionPrivate::eof (void)
    {
        return this->m_eof;
    }

    ssize_t
    SocketConnectionPrivate::read
        ( char * const buffer
        , std::size_t const length
        )
    {
        fd_set readfds;
        FD_ZERO (& readfds);
        FD_SET (this->m_fd, & readfds);

        struct timeval timeval;
        timeval.tv_sec = 1u;
        timeval.tv_usec = 0u;

        for (;;)
        {
            int const nfds
                ( select (this->m_fd + 1, & readfds, 0, 0, & timeval)
                );
            if (this->m_cancel or 0 != nfds)
            {
                break;
            }
        }

        ssize_t result;
        if (this->m_cancel)
        {
            result = static_cast <ssize_t> (0);
        }
        else
        {
            result = ::read (this->m_fd, buffer, length);
            if (static_cast <ssize_t> (-1) == result)
            {
                throw std::exception ();
            }
            else
            {
                if (static_cast <ssize_t> (0) == result)
                {
                    this->m_eof = true;
                }
            }
        }

        return result;
    }

    void
    SocketConnectionPrivate::write
        ( char const * buffer
        , std::size_t length
        )
    {
        while (length > static_cast <std::size_t> (0u))
        {
            ssize_t const result (::write (this->m_fd, buffer, length));
            if (static_cast <ssize_t> (-1) == result)
            {
                throw std::exception ();
            }
            else
            {
                buffer += result;
                length -= result;
            }
        }
    }

    void
    SocketConnectionPrivate::cancel (void)
    {
        this->m_cancel = true;
    }
}
