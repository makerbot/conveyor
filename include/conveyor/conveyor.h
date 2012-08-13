// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_CONVEYOR_H
#define CONVEYOR_CONVEYOR_H (1)

#include <QList>
#include <QObject>

#include <conveyor/fwd.h>

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
        Conveyor (ConveyorPrivate * private_);

        ConveyorPrivate * const m_private;

        friend class Job;
        friend class JobPrivate;
        friend class Printer;
        friend class PrinterPrivate;

		QList<Printer *> m_printers;

	private slots:
        void poll();
    };
}

#endif
