#ifndef EEPROMMAPPRIVATE_H
#define EEPROMMAPPRIVATE_H

#include <QString>
#include <QStringList>
#include <vector>

#include <json/value.h>

namespace conveyor
{

    class EepromMapPrivateTestCase;

    class EepromMapPrivate
    {
        public:
            EepromMapPrivate(Json::Value eepromMap);
            ~EepromMapPrivate(void);
            std::vector<int> getInt(QString path) const;
            std::vector<QString> getString(QString path) const;
            void setInt(QString path, std::vector<int> value);
            void setString(QString path, std::vector<QString> value);
            Json::Value getEepromMap(void) const;

        private:
            QString m_mainMap;
            Json::Value m_eepromMap;
            QStringList splitPath(QString path) const;
            Json::Value getSubMap(QStringList path) const;

            friend class EepromMapPrivateTestCase;

    };
}
#endif
