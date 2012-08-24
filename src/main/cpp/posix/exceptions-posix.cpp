// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <errno.h>
#include <stdexcept>
#include <string>

#include <conveyor/exceptions.h>

namespace conveyor
{
    SocketError::SocketError (std::string const & msg)
        : std::runtime_error (msg)
        , m_errno (errno)
    {
    }
}
