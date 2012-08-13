// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>

#include <conveyor/address.h>
#include <conveyor/conveyor.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    Conveyor *
    Conveyor::connect (Address const * const address)
    {
        ConveyorPrivate * const private_ (ConveyorPrivate::connect (address));
        Conveyor * const conveyor (new Conveyor (private_));
        return conveyor;
    }

    Conveyor::Conveyor (ConveyorPrivate * const private_)
        : m_private (private_)
    {
    }

    Conveyor::~Conveyor (void)
    {
        delete this->m_private;
    }

    QList<Job *> const &
    Conveyor::jobs (void)
    {
        return m_private->m_jobs;
    }

    QList<Printer *> const &
    Conveyor::printers (void)
    {
        static QList<Printer *> list;
        return list;
    }
}
