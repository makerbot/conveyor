// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef JOBPRIVATE_H
#define JOBPRIVATE_H

#include <conveyor.h>

namespace conveyor
{
    class JobPrivate
    {
    public:
        JobPrivate
            ( Conveyor * conveyor
            , Job * job
            , int const & id
            );

        void updateFromJson (Json::Value const &);

        void cancel (void);
        
        Conveyor * const m_conveyor;
        Job * const m_job;
        Printer * m_printer;
        int m_id;
        QString m_name;
        JobState m_state;
        JobConclusion m_conclusion;
        QString m_currentStepName;
        int m_currentStepProgress;
    };
}

#endif
