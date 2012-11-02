// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONNECTIONTHREAD_H
#define CONNECTIONTHREAD_H (1)

#include <QThread>

#include <jsonrpc.h>

#include <conveyor/connection.h>
#include <conveyor/conveyor.h>

#include "conveyorprivate.h"

namespace conveyor
{
    class ConnectionThread : public QThread
    {
        Q_OBJECT

    public:
        ConnectionThread 
            ( Connection * connection
            , JsonRpc * jsonRpc
            , ConveyorPrivate * m_conveyor
            );

    public slots:
        void stop (void);

    protected:
        void run (void);

    private:
        Connection * const m_connection;
        JsonRpc * const m_jsonRpc;
        ConveyorPrivate * const m_conveyor;
        bool volatile m_stop;
    };
}

#endif
