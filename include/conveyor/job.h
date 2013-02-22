// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_JOB_H
#define CONVEYOR_JOB_H (1)

#include <QList>
#include <QMutex>
#include <QObject>
#include <QScopedPointer>
#include <QString>

#include <conveyor/fwd.h>
#include <conveyor/jobstatus.h>

namespace Json {
class Value;
}

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

        void updateFromJson(Json::Value const &);

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

        // Important: all access to m_jobPrivate should take the
        // m_jobPrivateMutex
        mutable QMutex m_jobPrivateMutex;
        QScopedPointer <JobPrivate> m_jobPrivate;

        void emitChanged (void);
        void emitConcluded (void);

        friend class ConveyorPrivate;
    };

    QString jobTypeToHumanString(const Job::Type type);
}

#endif
