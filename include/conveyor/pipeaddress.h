// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_PIPEADDRESS_H
#define CONVEYOR_PIPEADDRESS_H (1)

#include <string>

#include <conveyor/fwd.h>
#include <conveyor/address.h>

namespace conveyor
{
    class PipeAddress : public Address
    {
    public:
        PipeAddress (std::string const & path);

        Connection * createConnection (void) const;
        std::string const & path (void) const;

    private:
        std::string const m_path;
    };
}

#endif
