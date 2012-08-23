// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "jobchangedmethod.h"
#include "conveyorprivate.h"

#include <QString>
#include <QMetaObject>

#include <QDebug>

namespace conveyor
{
    JobChangedMethod::JobChangedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    JobChangedMethod::~JobChangedMethod (void)
    {
    }
    
    Json::Value JobChangedMethod::invoke (Json::Value const & params)
    {
        qDebug() << "JobChangedMethod::invoke not implemented. ";
        qDebug() << QString(params.toStyledString().c_str());

        return Json::Value(Json::nullValue);
    }
}
