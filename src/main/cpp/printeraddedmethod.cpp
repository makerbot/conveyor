// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "printeraddedmethod.h"
#include "conveyorprivate.h"

#include <QString>
#include <QMetaObject>

namespace conveyor
{
    PrinterAddedMethod::PrinterAddedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    PrinterAddedMethod::~PrinterAddedMethod (void)
    {
    }
    
    Json::Value PrinterAddedMethod::invoke (Json::Value const & params)
    {
        QString botId(params["uniqueName"].asString().c_str());

        Printer * printer(m_conveyorPrivate->printerByUniqueName(botId));
        printer->m_private->updateFromJson(params);

        m_conveyorPrivate->emitPrinterAdded(printer);
        
        return Json::Value(Json::nullValue);
    }
}
