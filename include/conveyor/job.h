// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_JOB_H
#define CONVEYOR_JOB_H (1)

#include <QList>
#include <QObject>
#include <QString>

#include <conveyor/fwd.h>
#include <conveyor/jobstatus.h>

namespace conveyor
{
    class Job : public QObject
    {
        Q_OBJECT

    public:
        Job (Printer * printer, QString const & id);
        Job (Printer * printer, QString const & name, int progress);

        int progress (void);

        JobStatus jobStatus (void) const;

    signals:
        void JobPercentageChanged (int percent); // TODO: rename to progressChanged

        /** Emitted when the jobStatus changes */
        void jobStatusChanged (JobStatus);

    private:
        JobPrivate * const m_private;

        friend class Conveyor;
        friend class ConveyorPrivate;
        friend class Printer;
        friend class PrinterPrivate;
    };
}

#endif
