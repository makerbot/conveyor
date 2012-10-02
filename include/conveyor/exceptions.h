// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_EXCEPTIONS_H
#define CONVEYOR_EXCEPTIONS_H (1)

#include <stdexcept>

namespace conveyor
{
    class SocketError : public std::runtime_error
    {
    public:
        SocketError (std::string const & msg);

        int getErrno (void) const
        {
            return this->m_errno;
        }

    private:
        int const m_errno;
    };

    class SocketCreateError : public SocketError
    {
    public:
        SocketCreateError (void)
            : SocketError ("Unable to create socket")
        {
        }
    };

    class HostLookupError : public SocketError
    {
    public:
        HostLookupError (std::string const & host)
            : SocketError ("Unable to lookup host" + host)
        {
        }
    };

    class SocketConnectError : public SocketError
    {
    public:
        SocketConnectError (std::string const & host, int const = -1)
            : SocketError ("Unable to connect to " + host)
        {
        };
    };

    class SocketIOError : public SocketError
    {
    public:
        SocketIOError (void)
            : SocketError ("IO error on socket")
        {
        }
    };

    class SocketWriteError : public SocketIOError
    {
    public: 
        //TODO: smarter error
        SocketWriteError (int)
        {
        }
    };

    class SocketReadError : public SocketIOError
    {
    public: 
        //TODO: smarter error
        SocketReadError (int)
        {
        }
    };

    class InvalidAddressError : public std::runtime_error
    {
    public:
        InvalidAddressError (std::string const & address)
            : std::runtime_error ("Invalid address " + address)
        {
        }
    };

    class NotImplementedError : public std::logic_error
    {
    public:
        NotImplementedError (std::string const & function)
            : std::logic_error ("Not Implemented: " + function)
        {
        }
    };

    class InitializationError : public std::runtime_error
    {
    public:
        InitializationError (std::string const & message)
            : std::runtime_error ("Initialization failed: " + message)
        {
        }
    };
}

#endif
