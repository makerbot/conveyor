// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_JOBSTATUS_H
#define CONVEYOR_JOBSTATUS_H (1)

namespace conveyor
{
    enum JobStatus
        { QUEUED
        , STARTING
        , PRINTING
        , ENDING
        , FINISHED
        , CANCELLED
        , PAUSED
        };
}

#endif
