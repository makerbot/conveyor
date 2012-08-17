// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "printeraddedmethod.h"

#include <QDebug>

namespace conveyor
{
    PrinterAddedMethod::PrinterAddedMethod (ConveyorPrivate * const conveyorPrivate)
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    PrinterAddedMethod::~PrinterAddedMethod (void)
    {
    }
    
    Json::Value PrinterAddedMethod::invoke (Json::Value const & params)
    {
        qDebug() << QString(params.toStyledString().c_str());
        
        return Json::Value(Json::nullValue);
    }
}
