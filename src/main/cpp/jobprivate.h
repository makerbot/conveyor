// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef JOBPRIVATE_H
#define JOBPRIVATE_H

#include <conveyor.h>

namespace conveyor
{
    class JobPrivate
    {
    public:
        QString m_displayName;
        QString m_uniqueName;
        int m_progress;
        JobStatus m_Status;
    };
}

#endif
