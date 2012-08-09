// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstddef>
#include <exception>
#include <unistd.h>

#include "connectionprivate.h"
#include "socketconnectionprivate.h"

namespace conveyor
{
    SocketConnectionPrivate::SocketConnectionPrivate (int const fd)
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
    SocketConnectionPrivate::read (char * const buffer, std::size_t const length)
    {
        ssize_t const result (::read (this->m_fd, buffer, length));
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
            return result;
        }
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
