// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include <QUuid>
#include <QDebug>
#include <QStringList>

#include <conveyor.h>
#include <conveyor/exceptions.h>

#include "conveyorprivate.h"
#include "jobprivate.h"
#include "printerprivate.h"

namespace conveyor
{
    FirmwareVersion::FirmwareVersion()
        : m_error(kFirmwareVersionNotReceived)
        , m_major(-1)
        , m_minor(-1) {
    }

    QString FirmwareVersion::str() const
    {
        switch (m_error) {
        case kFirmwareVersionOK:
          return QObject::tr("%1.%2").arg(QString().setNum(m_major),
                                          QString().setNum(m_minor));
        case kFirmwareVersionNotReceived:
          return QObject::tr("Firmware version not received");
        case kFirmwareVersionNotInteger:
          return QObject::tr("Firmware version not an integer");
        case kFirmwareVersionTooSmall:
          return QObject::tr("Firmware version is too small");
        }
        return QObject::tr("Unknown error in firmware version");
    }

    void ToolTemperature::updateFromJson
    	( QMap<QString, Temperature> &tmap
        , const Json::Value &json)
    {
        tmap.clear();
        const Json::Value::Members names(json.getMemberNames());
        const int len = names.size();
        for (int i = 0; i < len; ++i) {
            const std::string &name(names[i]);
            tmap[name.c_str()] = json[name].asFloat();
        }
    }

    Printer::Printer
        ( Conveyor * const conveyor
        , QString const & uniqueName
        )
        : m_private
            ( new PrinterPrivate (conveyor, this, uniqueName)
            )
    {
    }

    Printer::~Printer ()
    {
    }

    QList<Job *>
    Printer::jobs ()
    {
        const QList<Job *> all_jobs(m_private->m_conveyor->jobs());
        QList<Job *> result;

        // Filter the list of jobs to just those jobs whose printer
        // matches this printer
        const int len = all_jobs.size();
        for (int i = 0; i < len; ++i) {
            Job * j = all_jobs[i];
            // TODO: any reason why this should use uniqueName rather
            // than the Printer address?
            if (j->m_private->m_printer == this)
                result.append(j);
        }

        return result;
    }

    Job *
    Printer::currentJob ()
    {
        QList<Job *> j = jobs();
        if(j.isEmpty())
            return 0;
        else
            return j.first();
    }

    QString const &
    Printer::displayName () const
    {
        return m_private->m_displayName;
    }

    QString const &
    Printer::uniqueName () const
    {
        return m_private->m_uniqueName;
    }

    QStringList const &
    Printer::machineNames () const
    {
        return m_private->m_machineNames;
    }

    QString const &
    Printer::printerType () const
    {
        return m_private->m_printerType;
    }

    bool
    Printer::canPrint () const
    {
        return m_private->m_canPrint;
    }

    bool Printer::hasHeatedPlatform() const
    {
        return m_private->m_hasHeatedPlatform;
    }

    bool
    Printer::canPrintToFile () const
    {
        return m_private->m_canPrintToFile;
    }

    int Printer::numberOfExtruders() const
    {
        return m_private->m_numberOfToolheads;
    }

    ConnectionStatus
    Printer::connectionStatus () const
    {
        return m_private->m_connectionStatus;
    }

    QString
    Printer::connectionStatusString () const
    {
        QString status;

        switch(m_private->m_connectionStatus)
        {
        case CONNECTED:
            status = "Connected";
            break;
        case NOT_CONNECTED:
            status = "Not Connected";
            break;
        }

        return status;
    }

    const ToolTemperature &
    Printer::toolTemperature () const
    {
        return m_private->m_toolTemperature;
    }

    float
    Printer::buildVolumeXmin() const
    {
        return m_private->m_buildVolumeXmin;
    }

    float
    Printer::buildVolumeYmin() const
    {
        return m_private->m_buildVolumeYmin;
    }

    float
    Printer::buildVolumeZmin() const
    {
        return m_private->m_buildVolumeZmin;
    }

    float
    Printer::buildVolumeXmax() const
    {
        return m_private->m_buildVolumeXmax;
    }

    float
    Printer::buildVolumeYmax() const
    {
        return m_private->m_buildVolumeYmax;
    }

    float
    Printer::buildVolumeZmax() const
    {
        return m_private->m_buildVolumeZmax;
    }

    const FirmwareVersion &
    Printer::firmwareVersion() const
    {
        return m_private->m_firmwareVersion;
    }

    Conveyor * 
    Printer::conveyor()
    {
        return m_private->m_conveyor;
    }

    Job *
    Printer::print (QString const & inputFile
                    , const SlicerConfiguration & slicer_conf
                    , QString const & material
                    , bool const skipStartEnd)
    {
        Job * const result (this->m_private->print (inputFile,
                                                    slicer_conf,
                                                    material,
                                                    skipStartEnd));
        return result;
    }

    Job *
    Printer::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const skipStartEnd
        , QString const & printToFileType
        )
    {
        Job * const result (this->m_private->printToFile (inputFile,
                                                          outputFile,
                                                          slicer_conf,
                                                          material,
                                                          skipStartEnd,
                                                          printToFileType));
        return result;
    }

    Job *
    Printer::slice
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const withStartEnd
        )
    {
        Job * const result (this->m_private->slice (inputFile,
                                                    outputFile,
                                                    slicer_conf,
                                                    material,
                                                    withStartEnd));
        return result;
    }

    void
    Printer::jog
        ( float x
        , float y
        , float z
        , float a
        , float b
        , float f
        )
    {
        QString message("Printer::jog x=%1 y=%2 z=%3 a=%4 b=%5 f=%6");
        message = message.arg(x).arg(y).arg(z).arg(a).arg(b).arg(f);
        throw NotImplementedError(message.toStdString());
    }

    void
    Printer::emitChanged (void)
    {
        emit changed();
    }
}
