// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_CONNECTION_H
#define CONVEYOR_CONNECTION_H (1)

#include <cstddef>
#include <QScopedPointer>
#include <unistd.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    class ConnectionPrivate;

    class Connection
    {
    public:
        Connection (ConnectionPrivate * private_);
        ~Connection (void);

        bool eof (void);
        ssize_t read (char * buffer, std::size_t length);
        void write (char const * buffer, std::size_t length);
        void cancel (void);

    private:
        QScopedPointer <ConnectionPrivate> m_private;
    };
}

#endif
