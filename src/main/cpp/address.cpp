// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <sstream>
#include <string>
#include <stdexcept>
#include <QtGlobal>

#include <conveyor/address.h>
#include <conveyor/pipeaddress.h>
#include <conveyor/tcpaddress.h>
#include <conveyor/exceptions.h>

namespace
{
    conveyor::TcpAddress DefaultTcpAddress ("localhost", 9999);

    conveyor::PipeAddress DefaultPipeAddress
        ( 
            #ifdef __APPLE__
            // The OSX developer documentation says that non-root daemons
            // should use /var/tmp for such socket files.
            "/var/tmp/conveyord.socket"
            #else
            "/var/run/conveyor/conveyord.socket"
            #endif
        );

    static
    conveyor::Address *
    parseTcpAddress (std::string const & hostport)
    {
        std::string::size_type const colon (hostport.find (":"));
        if (std::string::npos == colon)
        {
            throw std::runtime_error ("Error on hostport");
        }
        else
        {
            std::string const host (hostport.substr (0, colon));
            std::istringstream stream (hostport.substr (colon + 1));
            int port;
            stream >> port;
            if (stream.bad () or stream.fail ())
            {
                throw std::runtime_error ("Error writing to string stream");
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
                throw InvalidAddressError(str);
            }
            return address;
        }
        catch (std::out_of_range const & exception)
        {
            throw;
        }
    }

    Address::~Address (void)
    {
    }
}
