// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>
#include <QTimer>

#include <conveyor/address.h>
#include <conveyor/conveyor.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    Conveyor *
    Conveyor::connectToDaemon (Address const * address)
    {
        return ConveyorPrivate::connect (address);
    }

    Conveyor::Conveyor
        ( Connection * const connection
        , ConnectionStream * const connectionStream
        , JsonRpc * const jsonRpc
        , ConnectionThread * const connectionThread
        )
        : m_private
            ( new ConveyorPrivate
                ( this
                , connection
                , connectionStream
                , jsonRpc
                , connectionThread
                )
            )
    {
//        // Add poll for printer connect/disconnect
//        QTimer *timer = new QTimer(this);
//        connect(timer, SIGNAL(timeout()), this, SLOT(poll()));
//        timer->start(200);
    }

    Conveyor::~Conveyor (void)
    {
        delete this->m_private;
    }

    const QList<Printer *>& Conveyor::printers()
    {
        return m_private->printers();
    }

    QList<Job *> const &
    Conveyor::jobs (void)
    {
        return m_private->m_jobs;
    }

    /* commented our rather than deleted in case we need to quickly fall back on polling
    void
    Conveyor::poll ()
    {
        QList<ConveyorPrivate::PrinterScanResult> results = m_private->printerScan();

        // TODO: should implement this much more prettily/efficiently
        // without so much loopiness

        // Add any new printers
        for (QList<ConveyorPrivate::PrinterScanResult>::iterator i = results.begin();
             i != results.end(); ++i) {

            // Check if already in existing list of printers
            bool found = false;
            for (QList<Printer*>::iterator j = m_printers.begin();
                 j != m_printers.end(); ++j) {

                if ((*j)->uniqueName() == i->iSerial) {
                    found = true;
                    break;
                }
            }

            // New printer detected, add to internal list and signal
            if (!found) {
                Printer *p = new Printer(this, i->iSerial);
                m_printers.push_back(p);
                emit printerAdded(p);
            }
        }

        // Remove any missing printers
        for (QList<Printer*>::iterator i = m_printers.begin();
             i != m_printers.end(); ++i) {

            // Check if already in existing list of printers
            bool found = false;
            for (QList<ConveyorPrivate::PrinterScanResult>::iterator j =
                     results.begin(); j != results.end(); ++j) {
                if ((*i)->uniqueName() == j->iSerial) {
                    found = true;
                    break;
                }
            }

            // Printer not found, remove from internal list and signal
            if (!found) {
                m_printers.erase(i);
                // TODO, should delete p and NOT signal it
                emit printerRemoved(*i);
            }
        }
    } */
}
