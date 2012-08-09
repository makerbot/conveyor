// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SOCKETCONNECTIONPRIVATE_H
#define SOCKETCONNECTIONPRIVATE_H (1)

#include <cstddef>

#include "connectionprivate.h"

namespace conveyor
{
    class SocketConnectionPrivate : public ConnectionPrivate
    {
    public:
        SocketConnectionPrivate (int fd);
        ~SocketConnectionPrivate (void);

        bool eof (void);
        ssize_t read (char * buffer, std::size_t length);
        void write (char const * buffer, std::size_t length);
        void cancel (void);

    private:
        int m_fd;
        bool m_eof;
        bool m_cancel;
    };
}

#endif
