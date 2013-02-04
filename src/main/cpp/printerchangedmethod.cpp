// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "printerchangedmethod.h"
#include "conveyorprivate.h"

#include <QString>
#include <QMetaObject>

#include <QDebug>

namespace conveyor
{
    PrinterChangedMethod::PrinterChangedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }

    PrinterChangedMethod::~PrinterChangedMethod (void)
    {
    }
    
    Json::Value PrinterChangedMethod::invoke (Json::Value const & params)
    {
        QString botId(params["uniqueName"].asString().c_str());

        Printer * printer(m_conveyorPrivate->printerByUniqueName(botId));
        printer->m_private->updateFromJson(params);

        m_conveyorPrivate->emitPrinterChanged(printer);

        return Json::Value(Json::nullValue);
    }
}
