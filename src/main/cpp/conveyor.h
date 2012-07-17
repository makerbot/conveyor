// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_H
#define CONVEYOR_H (1)

#include <QList>
#include <QObject>
#include <QSharedPointer>
#include <QDebug>

namespace conveyor
{
    class Address;
    class Conveyor;
    class Job;
    class Printer;

    struct ConveyorPrivate;
    struct JobPrivate;
    struct PrinterPrivate;

    typedef QSharedPointer<Conveyor> ConveyorPointer;
    typedef QSharedPointer<Job> JobPointer;
    typedef QSharedPointer<Printer> PrinterPointer;

    enum ConnectionStatus
    {
        CONNECTED,
        NOT_CONNECTED
    };

    enum JobStatus
    {
        QUEUED,
        STARTING,
        PRINTING,
        ENDING,
        FINISHED,
        CANCELLED,
        PAUSED
    };

    class Address : public QObject
    {
        Q_OBJECT
    };

    class Conveyor : public QObject
    {
        Q_OBJECT

    public:
        explicit Conveyor (Address const & address);

        QList<JobPointer>     jobs     (void);
        QList<PrinterPointer> printers (void);

        friend class Job;
        friend class Printer;

    private:
        ConveyorPrivate const * m_private;
    };

    class Job : public QObject
    {
        Q_OBJECT

    public:
        Job (PrinterPointer printerPointer, QString const & id);

        JobStatus jobStatus () const;

        friend class Conveyor;
        friend class Printer;
    signals:
        void JobPercentageChanged(int percent);

        /** Emitted when the jobStatus changes */
        void jobStatusChanged(JobStatus);

    private:
        JobPrivate * const m_private;
    };

    class Printer : public QObject
    {
        Q_OBJECT

    public:
        Printer (ConveyorPointer conveyorPointer, QString const & name);
        ~Printer ();

        /** A list of all the jobs the printer has queued */
        QList<JobPointer> jobs ();

        /** A Pointer to the current job */
        JobPointer getCurrentJob();
        /** A human readable name for the printer, for display in GUI elements */
        QString const & displayName () const;
        /** A name for the printer guaranteed to be distinct from all other
            printer names */
        QString const & uniqueName () const;
        /** A string represenetation of the type of printer this is */
        QString const & printerType () const;

        /** Can this printer create physical objects? false for virtual printers */
        bool canPrint () const;
        /** Can this printer print to a file? */
        bool canPrintToFile () const;

        /** Details about our connection to the printer */
        ConnectionStatus connectionStatus () const;
        /** A human readable version of the connection status, possibly with
            additional details */
        QString connectionStatusString () const;

        /** The number of extruders the printer has. Usually 1 or 2. */
        int numberOfExtruders () const;

        /** True if this printer can set the temperature of its platform */
        bool hasHeatedPlatform () const;

        /** Ask the machine to move by some amount at a given speed */
        void jog (float x, float y, float z, float a, float b, float f);

        JobPointer print       (QString const & inputFile);
        JobPointer printToFile (QString const & inputFile, QString const & outputFile);
        JobPointer slice       (QString const & inputFile, QString const & outputFile);

        friend class Conveyor;
        friend class Job;

    signals:

        /** Emitted when the connectionStatus changes. */
        void connectionStatusChanged(ConnectionStatus);

        /** Emitted when the printer switches jobs */
        void currentJobChanged(JobPointer const);

    private:
        PrinterPrivate * const m_private;
    };
}

#endif
