// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_CONVEYOR_H
#define CONVEYOR_CONVEYOR_H (1)

#include <QList>
#include <QObject>
#include <QScopedPointer>

#include <conveyor/fwd.h>

#include <jsonrpc.h>

namespace conveyor
{
    class Conveyor : public QObject
    {
        Q_OBJECT

    public:
        static Conveyor * connectToDaemon (Address const * address);

        ~Conveyor (void);

        QList<Job *> const & jobs (void);
        QList<Printer *> const & printers (void);

    signals:
        void printerAdded (Printer *);
        void printerRemoved (Printer *);

        /** Signals that a new job has been created */
        void jobAdded (Job *);

        /** Signals that one or more jobs have been removed */
        void jobRemoved (void);

    private:
        Conveyor
            ( Connection * connection
            , ConnectionStream * connectionStream
            , JsonRpc * jsonRpc
            , ConnectionThread * connectionThread
            );

        QScopedPointer <ConveyorPrivate> m_private;

        friend class Job;
        friend class JobPrivate;
        friend class Printer;
        friend class PrinterPrivate;
        friend class ConveyorPrivate;

/*  Commented out rather than deleted in case we need to fall back on the polling method
        QList<Printer *> m_printers;

    private slots:
        void poll();
*/
    };
}

#endif
