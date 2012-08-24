// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "jobaddedmethod.h"
#include "conveyorprivate.h"

#include <QString>
#include <QMetaObject>

#include <QDebug>

namespace conveyor
{
    JobAddedMethod::JobAddedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    JobAddedMethod::~JobAddedMethod (void)
    {
    }
    
    Json::Value JobAddedMethod::invoke (Json::Value const & params)
    {
        qDebug() << "JobAddedMethod::invoke not implemented. ";
        qDebug() << QString(params.toStyledString().c_str());

        return Json::Value(Json::nullValue);
    }
}
