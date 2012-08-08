#ifndef CONVEYORPRIVATE_H
#define CONVEYORPRIVATE_H

#include "conveyor.h"

namespace conveyor
{
    struct ConveyorPrivate
    {
		QList<Job *> m_jobs;
    };

    struct JobPrivate
    {
        QString m_displayName;
        QString m_uniqueName;
        int m_progress;
        JobStatus m_Status;
    };

    struct PrinterPrivate
    {
        QString m_displayName;
        QString m_uniqueName;
        QString m_printerType;
        QList<Job *> m_jobs;
        bool m_canPrint;
        bool m_canPrintToFile;
        bool m_hasPlatform;
        Conveyor * m_Conveyor;
        int m_numberOfToolheads;
        ConnectionStatus m_connectionStatus;
    };
	
} //conveyor

#endif //CONVEYORPRIVATE_H