// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONNECTIONPRIVATE_H
#define CONNECTIONPRIVATE_H (1)

#include <cstddef>
#include <unistd.h>

namespace conveyor
{
    class ConnectionPrivate
    {
    public:
        virtual ~ConnectionPrivate (void);

        virtual bool eof (void) = 0;
        virtual ssize_t read (char * buffer, std::size_t length) = 0;
        virtual void write (char const * buffer, std::size_t length) = 0;
        virtual void cancel (void) = 0;
    };
}

#endif
