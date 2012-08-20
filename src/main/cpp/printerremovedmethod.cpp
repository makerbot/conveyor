// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "printerremovedmethod.h"
#include "conveyorprivate.h"

#include <QString>
#include <QMetaObject>

namespace conveyor
{
    PrinterRemovedMethod::PrinterRemovedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    PrinterRemovedMethod::~PrinterRemovedMethod (void)
    {
    }
    
    Json::Value PrinterRemovedMethod::invoke (Json::Value const & params)
    {
        QString botId(params["id"].asCString());

        Printer * printer(m_conveyorPrivate->printerByUniqueName(botId));

        m_conveyorPrivate->emitPrinterRemoved(printer);
        
        return Json::Value(Json::nullValue);
    }
}
