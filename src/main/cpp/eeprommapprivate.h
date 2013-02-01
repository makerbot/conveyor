#ifndef EEPROMMAPPRIVATE_H
#define EEPROMMAPPRIVATE_H

#include <QString>
#include <QStringList>
#include <vector>

#include <jsoncpp/json/value.h>

namespace conveyor
{

    class EepromMapPrivateTestCase;

    class EepromMapPrivate
    {
        public:
            EepromMapPrivate(Json::Value eepromMap);
            ~EepromMapPrivate(void);
            EepromMapPrivate (EepromMapPrivate & other);
            EepromMapPrivate & operator= (EepromMapPrivate & other);
            EepromMapPrivate & operator= (EepromMapPrivate other);
            std::vector<int> * getInt(QString path);
            std::vector<float> * getFloat(QString path);
            std::vector<QString> * getString(QString path) ;
            void setInt(QString path, std::vector<int> value);
            void setFloat(QString path, std::vector<float> value);
            void setString(QString path, std::vector<QString> value);
            Json::Value getEepromMap(void) ;

        private:
            QString m_mainMap;
            Json::Value m_eepromMap;
            QStringList splitPath(QString path) ;
            Json::Value * getEntry(QStringList path);

            friend class EepromMapPrivateTestCase;

    };
}
#endif
