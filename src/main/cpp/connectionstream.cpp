// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstddef>
#include <string>

#include <jsonrpc/jsonrpc.h>

#include <conveyor/connection.h>

#include "connectionstream.h"

namespace conveyor
{
    ConnectionStream::ConnectionStream (Connection * const connection)
        : m_connection (connection)
    {
    }

    void
    ConnectionStream::feed (char const * const buffer, std::size_t const length)
    {
        this->m_connection->write (buffer, length);
    }

    void
    ConnectionStream::feed (std::string const & buffer)
    {
        char const * const c_buffer (buffer.c_str ());
        std::size_t const length (buffer.length ());
        this->m_connection->write (c_buffer, length);
    }

    void
    ConnectionStream::feedeof (void)
    {
    }
}
