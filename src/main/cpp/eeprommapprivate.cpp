#include <QString>
#include <QStringList>

#include <json/value.h>
#include <jsonrpc.h>

#include "eeprommapprivate.h"

namespace conveyor
{

    EepromMapPrivate::EepromMapPrivate(EepromMapJson::Value eepromMap)
    {
        Json::Value this->eepromMap = eepromMap;
        QString this->mainMap = "eeprom_map";
    }

    EepromMapPrivate::~EepromMapPrivate(void)
    {
        delete this->eepromMap;
        delete this->mainMap;
    }
    
    int EepromMapPrivate::getInt(QString path) const
    {
        Json::Value theMap = this->getSubMap(path);
        int value = theMap[path[sizeof(path)-1]]["value"];
        return value;
    }

    QString EepromMapPrivate::getString(QString path) const
    {
        Json::Value theMap = this->getSubMap(path);
        QString value = theMap[path[sizeof(path)-1]]["value"];
        return value;
    }

    void EepromMapPrivate::setInt(QString path, int value)
    {
        Json::Value theMap = this->getSubMap(path);
        theMap[path[sizeof(path)-1]]["value"] = value;
    }

    void EepromMapPrivate::setQString(QString path, QString value)
    {
        Json::Value theMap = this->getSubMap(path);
        theMap[path[sizeof(path)-1]]["value"] = value;
    }

    Json::Value EepromMapPrivate::getSubMap(QStringList path) const
    {
        Json::Value theMap = this->eepromMap[this->mainMap];
        QStringList path = this->splitPath(path);
        //-1, since the last part is the actual EEPROM value
        int pathSize = sizeof(path)-1;
        for (int i = 0; i < pathSize; i++)
        {
            Json::Value theMap = theMap[path[i]]["submap"];
        }
        return theMap;
    }

    QStringList EepromMapPrivate::splitPath(QString path) const
    {
        char deliminator = '/';
        QString path = path.split(deliminator);
        return path;
    }

    Json::Value getEepromMap(void) const
    {
        return this->eepromMap;
    }

}
