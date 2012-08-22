// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "jobremovedmethod.h"
#include "conveyorprivate.h"

#include <QString>
#include <QMetaObject>

#include <QDebug>

namespace conveyor
{
    JobRemovedMethod::JobRemovedMethod
        ( ConveyorPrivate * const conveyorPrivate
        )
        : m_conveyorPrivate(conveyorPrivate)
    { 
    }
    
    JobRemovedMethod::~JobRemovedMethod (void)
    {
    }
    
    Json::Value JobRemovedMethod::invoke (Json::Value const & params)
    {
        qDebug() << "JobRemovedMethod::invoke not implemented. ";
        qDebug() << QString(params.toStyledString().c_str());

        return Json::Value(Json::nullValue);
    }
}
