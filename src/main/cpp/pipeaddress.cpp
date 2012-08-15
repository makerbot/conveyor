// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <string>

#include <conveyor/connection.h>
#include <conveyor/pipeaddress.h>

#include "socketconnectionprivate.h"

namespace conveyor
{
    PipeAddress::PipeAddress (std::string const & path)
        : m_path (path)
    {
    }

    std::string const &
    PipeAddress::path (void) const
    {
        return this->m_path;
    }
}
