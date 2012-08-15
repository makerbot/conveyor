// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <conveyor/pipeaddress.h>

namespace conveyor
{
    Connection *
    PipeAddress::createConnection (void) const
    {
        throw std::exception (); // TODO: implement Win32 named pipes
    }
}
