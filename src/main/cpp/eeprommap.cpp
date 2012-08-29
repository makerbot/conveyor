#include <QString>
#include <QStringList>

#include <json/value.h>
#include <jsonrpc.h>
#include <conveyor/eeprommap.h>

#include "eeprommapprivate.h"

namespace conveyor
{
    EepromMap::EepromMap(Json::Value eepromMap)
      : e_private ( new EepromMapPrivate (eepromMap) ) 
    {
    }

    EepromMap::~EepromMap(void)
    {
    }

    EepromMap getMap(void)
    {
      return this->e_private.getEepromMap();
    }

    int EepromMap::getInt(QString path)
    {
        return this->e_private.getInt(path);
    }

    QString EepromMap::getString(QString path)
    {
        return this->e_private.getString(path);
    }

    void EepromMap::setInt(QString path, int value)
    {
        this->e_private.setInt(path, value);
    }

    void EepromMap::setString(QString path, QString value)
    {
        this->e_private.setString(path, value);
    } 
}
