// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_CONVEYOR_H
#define CONVEYOR_CONVEYOR_H (1)

#include <QList>
#include <QObject>
#include <QScopedPointer>

#include <list>

#include <conveyor/fwd.h>
#include <conveyor/eeprommap.h>
#include <conveyor/jobstatus.h>
#include <conveyor/port.h>

#include <jsonrpc/jsonrpc.h>

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

        Printer * printerByUniqueName(QString uniqueName);

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
        bool verifyS3g(QString &s3gPath) const;

        /** Run the "getports" command and format the result */
        std::list<Port> getPorts() const;

        void connectToPort(const Port &port) const;

    signals:
        void printerAdded (Printer *);
        void printerRemoved (Printer *);

        /** Signals that a new job has been created */
        void jobAdded (Job *);

        /** Signals that a job has finished and been removed */
        void jobRemoved (Job *);

        void portAttached(const conveyor::Port *port);
        void portDetached(const QString portName);

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
        friend class PortAttachedMethod;
        friend class PortDetachedMethod;

        void emitPrinterAdded (Printer *);
        void emitPrinterRemoved (Printer *);

        void emitJobAdded (Job *);
        void emitJobRemoved (Job *);

        void emitPortAttached(const conveyor::Port *port);
        void emitPortDetached(const QString &portName);
    };

    /// True if the job is for the specified printer or printer type
    ///
    /// If the printer is a physical machine, it is matched against
    /// the jobs' machine name and unique ID fields. For archetype
    /// printers, the profile name is used.
    bool isJobForPrinter(
        const Job * const job, const Printer * const printer);

    /// Return a new list of jobs filtered by their associated printers
    ///
    /// Uses isJobForPrinter() to determine a match.
    QList<Job *> filterJobsByPrinter(
        const QList<Job *> jobs, const Printer * const printer);

    /// Return a new list of jobs filtered by their conclusion
    QList<Job *> filterJobsByConclusion(
        const QList<Job *> jobs, const JobConclusion jobConclusion);
}

#endif
