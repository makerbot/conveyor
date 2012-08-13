// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <sstream>
#include <string>
#include <stdexcept>
#include <QtGlobal>

#include <conveyor/address.h>
#include <conveyor/pipeaddress.h>
#include <conveyor/tcpaddress.h>

namespace
{
    conveyor::TcpAddress DefaultTcpAddress ("localhost", 9999);

    conveyor::PipeAddress DefaultPipeAddress
        ( "/var/run/conveyord/conveyord.socket"
        );

    static
    conveyor::Address *
    parseTcpAddress (std::string const & hostport)
    {
        std::string::size_type const colon (hostport.find (":"));
        if (std::string::npos == colon)
        {
            throw std::exception ();
        }
        else
        {
            std::string const host (hostport.substr (0, colon));
            std::istringstream stream (hostport.substr (colon + 1));
            int port;
            stream >> port;
            if (stream.bad () or stream.fail ())
            {
                throw std::exception ();
            }
            else
            {
                conveyor::Address * const address
                    ( new conveyor::TcpAddress (host, port)
                    );
                return address;
            }
        }
    }

    static
    conveyor::Address *
    parsePipeAddress (std::string const & path)
    {
        conveyor::Address * const address (new conveyor::PipeAddress (path));
        return address;
    }
}

namespace conveyor
{
    Address *
    Address::defaultAddress()
    {
#if defined (CONVEYOR_ADDRESS)
        return CONVEYOR_ADDRESS;
#elif defined (Q_OS_LINUX) || defined (Q_OS_MAC)
        return & DefaultPipeAddress;
#elif defined (Q_OS_WIN32)
        return & DefaultTcpAddress;
#else
# error No CONVEYOR_ADDRESS defined and no default location known for this platform
#endif
    }

    Address *
    Address::parse (std::string const & str)
    {
        try
        {
            Address * address;
            if ("tcp:" == str.substr (0, 4))
            {
                address = parseTcpAddress (str.substr (4));
            }
            else
            if (("pipe:" == str.substr (0, 5))
                or ("unix:" == str.substr (0, 5)))
            {
                address = parsePipeAddress (str.substr (5));
            }
            else
            {
                throw std::exception ();
            }
            return address;
        }
        catch (std::out_of_range const & exception)
        {
            throw std::exception ();
        }
    }

    Address::~Address (void)
    {
    }
}
