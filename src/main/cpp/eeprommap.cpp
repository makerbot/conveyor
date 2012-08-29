#include <QString>
#include <QStringList>

#include <json/value.h>
#include <jsonrpc.h>
#include <conveyor/eeprommap.h>

#include "eeprommapprivate.h"

namespace conveyor
{
    EepromMap::EepromMap(Json::Value eepromMap)
    {
        this->m_private = new EepromMapPrivate(eepromMap);
    }

    EepromMap::~EepromMap(void)
    {
    }

    Json::Value EepromMap::getEepromMap(void) const
    {
        return this->m_private->getEepromMap();
    }

    int EepromMap::getInt(QString path) const
    {
        return this->m_private->getInt(path);
    }

    QString EepromMap::getString(QString path) const
    {
        return this->m_private->getString(path);
    }

    void EepromMap::setInt(QString path, int value)
    {
        this->m_private->setInt(path, value);
    }

    void EepromMap::setString(QString path, QString value)
    {
        this->m_private->setString(path, value);
    } 
}
