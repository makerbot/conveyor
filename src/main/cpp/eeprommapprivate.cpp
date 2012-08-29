#include <QString>
#include <QStringList>

#include <json/value.h>
#include <jsonrpc.h>

#include "eeprommapprivate.h"

namespace conveyor
{
    EepromMapPrivate::EepromMapPrivate(Json::Value eepromMap)
    : m_mainMap ("eeprom_map")
    , m_eepromMap (eepromMap)
    {
    }

    EepromMapPrivate::~EepromMapPrivate(void)
    {
    }
    
    int EepromMapPrivate::getInt(QString path) const
    {
        QStringList path = this->splitPath(path)
        Json::Value theMap = this->getSubMap(path);
        int value = theMap[path.size()-1]["value"];
        return value;
    }

    QString EepromMapPrivate::getString(QString path) const
    {
        QStringList path = this->splitPath(path)
        Json::Value theMap = this->getSubMap(path);
        QString value = theMap[path.size()-1]["value"];
        return value;
    }

    void EepromMapPrivate::setInt(QString path, int value)
    {
        QStringList path = this->splitPath(path)
        Json::Value theMap = this->getSubMap(path);
        theMap[path.size()-1]["value"] = value;
    }

    void EepromMapPrivate::setQString(QString path, QString value)
    {
        QStringList path = this->splitPath(path)
        Json::Value theMap = this->getSubMap(path);
        theMap[path.size()-1]["value"] = value;
    }

    Json::Value EepromMapPrivate::getSubMap(QStringList path) const
    {
        Json::Value theMap = this->m_eepromMap[this->m_mainMap];
        int pathSize = path.size();
        //-1, since the last part is the actual EEPROM value
        for (int i = 0; i < pathSize-1; i++)
        {
            Json::Value theMap = theMap[path[i]]["submap"];
        }
        return theMap;
    }

    QStringList EepromMapPrivate::splitPath(QString path) const
    {
        char deliminator = '/';
        QStringList path = path.split(deliminator);
        return path;
    }

    Json::Value EepromMapPrivate::getEepromMap(void) const
    {
        return this->m_eepromMap;
    }
}
