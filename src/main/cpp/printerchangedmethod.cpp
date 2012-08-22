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
        qDebug() << "PrinterChangedMethod::invoke not implemented. ";
        qDebug() << QString(params.toStyledString().c_str());

        return Json::Value(Json::nullValue);
    }
}
