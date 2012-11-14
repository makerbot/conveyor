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
        /** This must be called before any Conveyor object is created */
        static void initialize();

        static Conveyor * connectToDaemon (Address const * address);

        ~Conveyor (void);

        QList<Job *> jobs (void);
        QList<Printer *> printers (void);

        void cancelJob (int jobId);

        /** Get connected machines that can be uploaded to

            Returns a JSON list of machine-types, which can be matched
            against Printer::machineNames()
          */
        Json::Value getUploadableMachines();

        /** Download available firmware versions for a particular machine type

            Returns a JSON list of versions. Each version is a number
            followed by a description of what's new in that version.
         */
        Json::Value getMachineVersions(QString machinetype);

        /** Download .hex file for a particular machine-type/version combo

            Returns the path of the .hex file
        */
        QString downloadFirmware
            ( const QString &machinetype
            , const QString &version
            );
        
        /** Upload a .hex file to the specified bot */
        void uploadFirmware
            ( Printer * const printer
            , QString machinetype
            , QString hexPath
            );

        EepromMap readEeprom(Printer * const printer) const;
        void writeEeprom(Printer * const printer, EepromMap eepromMap);
        void resetToFactory(Printer * const printer) const;
        bool compatibleFirmware(QString &firmwareVersion) const;

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
