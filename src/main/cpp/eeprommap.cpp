#include <QString>
#include <QStringList>

#include <json/value.h>
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

    std::vector<int> * EepromMap::getInts(QString path) const
    {
        return this->m_private->getInts(path);
    }

    std::vector<float> * EepromMap::getFloats(QString path) const
    {
        return this->m_private->getFloats(path);
    }

    std::vector<QString> * EepromMap::getStrings(QString path) const
    {
        return this->m_private->getStrings(path);
    }

    void EepromMap::setInts(QString path, std::vector<int> value)
    {
        this->m_private->setInts(path, value);
    }

    void EepromMap::setFloats(QString path, std::vector<float> value)
    {
        this->m_private->setFloats(path, value);
    }

    void EepromMap::setStrings(QString path, std::vector<QString> value)
    {
        this->m_private->setStrings(path, value);
    } 
}
