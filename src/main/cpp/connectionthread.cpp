// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstddef>
#include <QThread>
#include <unistd.h>

#include <jsonrpc/jsonrpc.h>

#include <conveyor/connection.h>

#include "connectionthread.h"

namespace
{
    static std::size_t const LENGTH = 4096;
}

namespace conveyor
{
    ConnectionThread::ConnectionThread
        ( Connection * const connection
        , JsonRpc * const jsonRpc
        )
        : m_connection (connection)
        , m_jsonRpc (jsonRpc)
        , m_stop (false)
    {
    }

    void
    ConnectionThread::run (void)
    {
        char buffer[LENGTH];
        try
        {
            while (not this->m_stop)
            {
                // TODO: this loop needs some work for (i.e., EINTR)

                ssize_t const read (this->m_connection->read (buffer, LENGTH));
                if (static_cast <ssize_t> (-1) == read)
                {
                    this->m_stop = true;
                }
                else
                if (static_cast <ssize_t> (0) != read)
                {
                    std::size_t const length (static_cast <std::size_t> (read));
                    this->m_jsonRpc->feed (buffer, length);
                }
                else
                {
                    this->m_stop = true;
                }
            }
            this->m_jsonRpc->feedeof ();
        }
        catch (...)
        {
            this->m_jsonRpc->feedeof ();
            throw;
        }
    }

    void
    ConnectionThread::stop (void)
    {
        this->m_stop = true;
        this->m_connection->cancel ();
    }
}
