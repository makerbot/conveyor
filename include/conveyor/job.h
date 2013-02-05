// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_JOB_H
#define CONVEYOR_JOB_H (1)

#include <QList>
#include <QObject>
#include <QScopedPointer>
#include <QString>

#include <conveyor/fwd.h>
#include <conveyor/jobstatus.h>

namespace conveyor
{
    class Job : public QObject
    {
        Q_OBJECT

    public:
        enum Type {
            kPrint,
            kPrintToFile,
            kSlice,
            kInvalidType
        };

        class Progress {
         public:
          Progress();

          /// Name of the current progress step
          QString m_name;

          /// Percentage of the current progress step in the range [0, 100]
          int m_progress;
        };

        class Failure {
         public:
          Failure();

          /// True if the Job failed, false otherwise
          ///
          /// The other Failure fields should not be used if m_failed
          /// is false.
          bool m_failed;

          QString m_exception;
          int m_code;
          QString m_slicerLog;
        };

        ~Job (void);

        int id (void) const;

        QString name (void) const;
        JobState state (void) const;
        JobConclusion conclusion (void) const;

        QString machineName() const;
        QString profileName() const;

        Progress progress() const;

        Failure failure() const;

        Type type() const;

    public slots:
        void cancel (void);
        void pause (void);
        
    signals:
        void changed (const Job *);

        // Emitted when the job's conclusion changes from NOTCONCLUDED
        void concluded (const Job *job);

    private:
        Job (Conveyor * conveyor, int const & id);

        QScopedPointer <JobPrivate> m_private;

        void emitChanged (void);
        void emitConcluded (void);

        friend class Conveyor;
        friend class ConveyorPrivate;
        friend class JobAddedMethod;
        friend class JobChangedMethod;
        friend class JobPrivate;
        friend class Printer;
        friend class PrinterPrivate;
    };

    QString jobTypeToHumanString(const Job::Type type);
}

#endif
