// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_H
#define CONVEYOR_H (1)

#include <QList>
#include <QObject>

namespace conveyor
{
    class Address;
    class Conveyor;
    class Job;
    class Printer;

    struct ConveyorPrivate;
    struct JobPrivate;
    struct PrinterPrivate;

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

        QList<Job *> const & jobs (void);
        QList<Printer *> printers (void);

        friend class Job;
        friend class Printer;

    signals:
        /** Signals that a new job has been created */
        void jobAdded (Job *);
        /** Signals that one or more jobs have been removed */
        void jobRemoved ();

    private:
        ConveyorPrivate const * m_private;
    };

    class Job : public QObject
    {
        Q_OBJECT

    public:
        Job (Printer * printer, QString const & id);
        Job (Printer * printer, QString const &name, int const &progress);

        int progress();

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
        ~Printer ();

        /** A list of all the jobs the printer has queued */
        QList<Job *> const & jobs ();

        /** A Pointer to the current job */
        Job * currentJob();
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

        Conveyor* conveyor();
		
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

        virtual Job * print       (QString const & inputFile);
        virtual Job * printToFile (QString const & inputFile, QString const & outputFile);
        virtual Job * slice       (QString const & inputFile, QString const & outputFile);

        friend class Conveyor;
        friend class Job;
		
		friend class FakePrinter;

    signals:
        /** Emitted when the connectionStatus changes. 
			Holds the new status */
        void connectionStatusChanged(ConnectionStatus);

        /** Emitted when the printer switches jobs. 
			Holds the new Job */
        void currentJobChanged(Job const *);
		
    public slots:
		/**  */
        virtual void togglePaused();
		/**  */
        virtual void cancelCurrentJob();

	protected:
        Printer
			( Conveyor * convey
			, QString const & name);
			
        Printer 
			( Conveyor * convey
			, QString const & name
			, bool const & canPrint
			, bool const & canPrintToFile
			, ConnectionStatus const & cs
			, QString const & printerType
			, int const & numberOfExtruders
			, bool const & hasHeatedPlatform);
			
    private:
        PrinterPrivate * const m_private;
    };
	
    Address& defaultAddress();
}

#endif // CONVEYOR_H
