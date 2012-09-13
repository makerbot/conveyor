// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_CONVEYOR_H
#define CONVEYOR_CONVEYOR_H (1)

#include <QList>
#include <QObject>
#include <QScopedPointer>

#include <conveyor/fwd.h>
#include <conveyor/eeprommap.h>

#include <jsonrpc.h>

namespace conveyor
{
    class Conveyor : public QObject

    {
        Q_OBJECT
    public:
        static Conveyor * connectToDaemon (Address const * address);

        ~Conveyor (void);

        QList<Job *> jobs (void);
        QList<Printer *> printers (void);

        void cancelJob (int jobId);

        Json::Value getUploadableMachines();
        Json::Value getMachineVersions(QString machinetype);
        void uploadFirmware
            ( Printer * const printer
            , QString machinetype
            , QString version
            );
        EepromMap readEeprom(Printer * const printer) const;
        void writeEeprom(Printer * const printer, EepromMap eepromMap);
        void resetToFactory(Printer * const printer) const;

    signals:
        void printerAdded (Printer *);
        void printerRemoved (Printer *);

        /** Signals that a new job has been created */
        void jobAdded (Job *);

        /** Signals that a job has finished and been removed */
        void jobRemoved (Job *);

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

        void emitPrinterAdded (Printer *);
        void emitPrinterRemoved (Printer *);

        void emitJobAdded (Job *);
        void emitJobRemoved (Job *);
    };
}

#endif
