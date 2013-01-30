#include <QString>
#include <QStringList>

#include <jsoncpp/json/value.h>
#include <conveyor/eeprommap.h>
#include <vector>

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

    std::vector<int> * EepromMap::getInt(QString path) const
    {
        return this->m_private->getInt(path);
    }

    std::vector<float> * EepromMap::getFloat(QString path) const
    {
        return this->m_private->getFloat(path);
    }

    std::vector<QString> * EepromMap::getString(QString path) const
    {
        return this->m_private->getString(path);
    }

    void EepromMap::setInt(QString path, std::vector<int> value)
    {
        this->m_private->setInt(path, value);
    }

    void EepromMap::setFloat(QString path, std::vector<float> value)
    {
        this->m_private->setFloat(path, value);
    }

    void EepromMap::setString(QString path, std::vector<QString> value)
    {
        this->m_private->setString(path, value);
    } 
}
