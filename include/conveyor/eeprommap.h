#ifndef EEPROMMAP_H
#define EEPROMMAP_H

#include <QString>
#include <QStringList>

#include <conveyor/fwd.h>
#include <vector>

#include <jsoncpp/json/value.h>

namespace conveyor
{
    class EepromMap
    {
    public:
        EepromMap(Json::Value eepromMap);
        ~EepromMap(void);

        std::vector<int> * getInt(QString path) const;
        std::vector<float> * getFloat(QString path) const;
        std::vector<QString> * getString(QString path) const;
        void setInt(QString path, std::vector<int> value);
        void setFloat(QString path, std::vector<float> value);
        void setString(QString path, std::vector<QString> value);
        Json::Value getEepromMap(void) const;
    private:
        EepromMapPrivate * m_private;
    };
}
#endif
