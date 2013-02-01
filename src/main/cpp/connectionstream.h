// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SOCKETSTREAM_H
#define SOCKETSTREAM_H (1)

#include <cstddef>
#include <string>

#include <jsonrpc/jsonrpc.h>

#include <conveyor/connection.h>

namespace conveyor
{
    class ConnectionStream : public JsonRpcStream
    {
    public:
        ConnectionStream (Connection * connection);

        void feed (char const * buffer, std::size_t length);
        void feed (std::string const & buffer);
        void feedeof (void);

    private:
        Connection * const m_connection;
    };
}

#endif
