// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_ADDRESS_H
#define CONVEYOR_ADDRESS_H (1)

#include <conveyor/connection.h>

namespace conveyor
{
    class Address
    {
    public:
        virtual ~Address (void);
        virtual Connection * createConnection (void) const = 0;
    };
}

#endif
