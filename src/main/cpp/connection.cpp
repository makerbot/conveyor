// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <cstddef>
#include <unistd.h>

#include <string>

#include <conveyor/connection.h>
#include <conveyor/log.h>

#include "connectionprivate.h"

namespace conveyor
{
    Connection::~Connection (void)
    {
    }

    bool
    Connection::eof (void)
    {
        bool const eof (this->m_private->eof ());
        return eof;
    }

    ssize_t
    Connection::read (char * const buffer, std::size_t const length)
    {
        ssize_t const result (this->m_private->read (buffer, length));
        if (buffer && result)
            LOG_SPAM << "\"" << std::string(buffer, result) << "\"\n";
        return result;
    }

    void
    Connection::write (char const * const buffer, std::size_t const length)
    {
        if (buffer && length)
            LOG_SPAM << "\"" << std::string(buffer, length) << "\"\n";

        this->m_private->write (buffer, length);
    }

    void
    Connection::cancel (void)
    {
        this->m_private->cancel ();
    }

    Connection::Connection (ConnectionPrivate * const private_)
        : m_private (private_)
    {
    }
}
