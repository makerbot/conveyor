#ifndef EEPROMMAP_H
#define EEPROMMAP_H

#include <QString>
#include <QStringList>

#include <conveyor/fwd.h>
#include <vector>

#include <json/value.h>

namespace conveyor
{
    class EepromMap
    {
    public:
        EepromMap(Json::Value eepromMap);
        ~EepromMap(void);

        std::vector<int> * getInts(QString path) const;
        std::vector<float> * getFloats(QString path) const;
        std::vector<QString> * getStrings(QString path) const;
        void setInts(QString path, std::vector<int> value);
        void setFloats(QString path, std::vector<float> value);
        void setStrings(QString path, std::vector<QString> value);
        Json::Value getEepromMap(void) const;
    private:
        EepromMapPrivate * m_private;
    };
}
#endif
