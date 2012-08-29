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

    EepromMap getMap(void)
    {
      return m_private->getEepromMap();
    }

    int EepromMap::getInt(QString path)
    {
        return m_private->getInt(path);
    }

    QString EepromMap::getString(QString path)
    {
        return m_private->getString(path);
    }

    void EepromMap::setInt(QString path, int value)
    {
        m_private->setInt(path, value);
    }

    void EepromMap::setString(QString path, QString value)
    {
        m_private->setString(path, value);
    } 
}
