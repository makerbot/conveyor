#include <QString>
#include <QStringList>

#include <json/value.h>
#include <jsonrpc.h>
#include <conveyor/eeprommap.h>

#include "eeprommapprivate.h"

namespace conveyor
{
    EepromMap::EepromMap(Json::Value eepromMap)
      : m_private 
          ( new EepromMapPrivate (eepromMap) ) 
    {
    }

    EepromMap::~EepromMap(void)
    {
    }

    EepromMap EepromMap::getMap(void)
    {
        return this->m_private->getEepromMap();
    }

    int EepromMap::getInt(QString path)
    {
        return this->m_private->getInt(path);
    }

    QString EepromMap::getString(QString path)
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
