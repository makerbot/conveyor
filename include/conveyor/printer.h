// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_PRINTER_H
#define CONVEYOR_PRINTER_H (1)

#include <QList>
#include <QObject>
#include <QString>
#include <QScopedPointer>

#include <conveyor/fwd.h>
#include <conveyor/connectionstatus.h>

namespace conveyor
{
    class SlicerConfiguration;

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

        Conveyor * conveyor ();

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

        virtual Job * print (QString const & inputFile,
                             const SlicerConfiguration & slicer_conf);

        virtual Job * printToFile (QString const & inputFile, QString const & outputFile,
                                   const SlicerConfiguration & slicer_conf);

        virtual Job * slice (QString const & inputFile, QString const & outputFile,
                             const SlicerConfiguration & slicer_conf);

    signals:
        void changed (void);

    public slots:
        virtual void togglePaused();

        virtual void cancelCurrentJob();

    private:
        Printer (Conveyor * conveyor, QString const & uniqueName);

        QScopedPointer <PrinterPrivate> m_private;

        void emitChanged (void);

        friend class Conveyor;
        friend class ConveyorPrivate;
        friend class FakePrinter;
        friend class Job;
        friend class JobPrivate;
    };
}

#endif
