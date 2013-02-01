#include <QString>
#include <QStringList>
#include <vector>
#include <jsoncpp/json/value.h>

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

    EepromMapPrivate::EepromMapPrivate(EepromMapPrivate & other)
    {
      this->m_eepromMap = other.m_eepromMap;
    }

    EepromMapPrivate & EepromMapPrivate::operator= (EepromMapPrivate & other)
    {
      this->m_eepromMap = other.m_eepromMap;
      return *this;
    }

    EepromMapPrivate & EepromMapPrivate::operator= (EepromMapPrivate other)
    {
      this->m_eepromMap = other.m_eepromMap;
      return *this;
    }
    
    std::vector<int> * EepromMapPrivate::getInt(QString path)
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theEntry(*this->getEntry(split_path));
        Json::Value gotValues(theEntry["value"]);
        std::vector<int> * return_values = new std::vector<int>;
        for (Json::ArrayIndex i = 0; i < gotValues.size(); ++i)
        {
            return_values->push_back(gotValues[i].asInt());
        }
        return return_values;
    }

    std::vector<float> * EepromMapPrivate::getFloat(QString path)
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theEntry(*this->getEntry(split_path));
        Json::Value gotValues(theEntry["value"]);
        std::vector<float> * return_values = new std::vector<float>;
        for (Json::ArrayIndex i = 0; i < gotValues.size(); ++i)
        {
            return_values->push_back(gotValues[i].asFloat());
        }
        return return_values;
    }

    std::vector<QString> * EepromMapPrivate::getString(QString path) 
    {
        QStringList split_path = this->splitPath(path);
        Json::Value theEntry(*this->getEntry(split_path));
        Json::Value gotValues(theEntry["value"]);
        std::vector<QString> * return_values = new std::vector<QString>;
        for (Json::ArrayIndex i = 0; i < gotValues.size(); ++i)
        {
            return_values->push_back(QString(gotValues[i].asCString()));
        }
        return return_values;
    }

    void EepromMapPrivate::setInt(QString path, std::vector<int> inValue)
    {
        QStringList split_path = this->splitPath(path);
        Json::Value * theEntry = this->getEntry(split_path);
        Json::Value * oldValues = &((*theEntry)["value"]);
        for (unsigned i = 0; i < inValue.size(); ++i)
        {
            (*oldValues)[i] = Json::Value(inValue[i]);
        }
    }

    void EepromMapPrivate::setFloat(QString path, std::vector<float> inValue)
    {
        QStringList split_path = this->splitPath(path);
        Json::Value * theEntry = this->getEntry(split_path);
        Json::Value * oldValues = &((*theEntry)["value"]);
        for (unsigned i = 0; i < inValue.size(); ++i)
        {
            (*oldValues)[i] = Json::Value(inValue[i]);
        }
    }

    void EepromMapPrivate::setString(QString path, std::vector<QString> inValue)
    {
        //Get the correct map
        QStringList split_path = this->splitPath(path);
        Json::Value * theEntry = this->getEntry(split_path);
        Json::Value * oldValues = &((*theEntry)["value"]);
        for (unsigned i = 0; i < inValue.size(); ++i)
        {
            (*oldValues)[i] = Json::Value(inValue[i].toStdString());
        }
    }

    Json::Value * EepromMapPrivate::getEntry(QStringList path) 
    {
        Json::Value * theMap = &(this->m_eepromMap[this->m_mainMap.toStdString()]);
        //-1, since the last part is the actual EEPROM value
        for (int i = 0; i < path.size()-1; ++i)
        {
            theMap = &((*theMap)[path[i].toStdString()]["sub_map"]);
        }
        theMap = &((*theMap)[path[path.size()-1].toStdString()]);
        return theMap;
    }

    QStringList EepromMapPrivate::splitPath(QString path) 
    {
        char deliminator = '/';
        return path.split(deliminator);
    }

    Json::Value EepromMapPrivate::getEepromMap(void) 
    {
        return this->m_eepromMap;
    }
}
