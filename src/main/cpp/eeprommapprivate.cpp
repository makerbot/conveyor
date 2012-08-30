#include <QString>
#include <QStringList>

#include <vector>

#include <json/value.h>

#include "eeprommapprivate.h"

namespace conveyor
{
    EepromMapPrivate::EepromMapPrivate(Json::Value eepromMap)
    : m_eepromMap (eepromMap)
    {
      this->m_mainMap = QString("eeprom_map");
    }

    EepromMapPrivate::~EepromMapPrivate(void)
    {
    }
    
    std::vector<int> EepromMapPrivate::getInt(QString path) const
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theMap = this->getSubMap(split_path);
        Json::Value values = theMap[split_path[split_path.size()-1].toStdString()]["value"];
        std::vector<int> return_values;
        for (Json::ArrayIndex i = 0; i < values.size(); i++)
        {
            return_values.push_back(values[i].asInt());
        }
        return return_values;
    }

    std::vector<QString> EepromMapPrivate::getString(QString path) const
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theMap = this->getSubMap(split_path);
        Json::Value values = theMap[split_path[split_path.size()-1].toStdString()]["value"];
        std::vector<QString> return_values;
        for (Json::ArrayIndex i = 0; i < values.size(); i++)
        {
            return_values[i].push_back(QString(values[i].asCString()));
        }
        return return_values;
    }

    void EepromMapPrivate::setInt(QString path, std::vector<int> value)
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theMap = this->getSubMap(split_path);
        Json::Value newValue = new Json::Value(Json::arrayValue);
        newValue.resize(value.size());
        for (Json::ArrayIndex i = 0; i < value.size(); i++)
        {
            newValue.append(Json::Value(value[i]));
        }
        theMap[split_path[split_path.size()-1].toStdString()]["value"] = newValue;
    }

    void EepromMapPrivate::setString(QString path, std::vector<QString> value)
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theMap = this->getSubMap(split_path);
        Json::Value newValue = new Json::Value(Json::arrayValue);
        newValue.resize(value.size());
        for (Json::ArrayIndex i = 0; i < value.size(); i++)
        {
            newValue.append(Json::Value(value[i].toStdString()));
        }
        theMap[split_path[split_path.size()-1].toStdString()]["value"] = newValue;
    }

    Json::Value EepromMapPrivate::getSubMap(QStringList path) const
    {
        Json::Value theMap = this->m_eepromMap[this->m_mainMap.toStdString()];
        //-1, since the last part is the actual EEPROM value
        for (int i = 0; i < path.size()-1; i++)
        {
            Json::Value theMap = (Json::Value)theMap[path[i].toStdString()]["submap"];
        }
        return theMap;
    }

    QStringList EepromMapPrivate::splitPath(QString path) const
    {
        char deliminator = '/';
        QStringList split_path = path.split(deliminator);
        return split_path;
    }

    Json::Value EepromMapPrivate::getEepromMap(void) const
    {
        return this->m_eepromMap;
    }
}
