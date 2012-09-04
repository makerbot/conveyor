// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_JOBSTATUS_H
#define CONVEYOR_JOBSTATUS_H (1)

namespace conveyor
{
    enum JobState
        { PENDING
        , RUNNING
        , STOPPED
        };

    enum JobConclusion
        { ENDED
        , FAILED
        , CANCELED
        , NOTCONCLUDED
        };
}

#endif
