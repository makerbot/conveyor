// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#include "conveyor/conveyor.h"
#include "conveyor/log.h"

#include "printerprivate.h"

#include "conveyorprivate.h"

#include <stdexcept>

#include <QString>
#include <QStringList>

namespace conveyor
{
    PrinterPrivate::PrinterPrivate
        ( Conveyor * const conveyor
        , Printer * const printer
        , QString const & uniqueName
        )
        : m_conveyor (conveyor)
        , m_printer (printer)
        , m_uniqueName (uniqueName)
        , m_state (Printer::kInvalid)
        , m_canPrint(false)
        , m_canPrintToFile(false)
        , m_hasHeatedPlatform(false)
        , m_numberOfToolheads(0)
        , m_buildVolumeXmin(0)
        , m_buildVolumeYmin(0)
        , m_buildVolumeZmin(0)
        , m_buildVolumeXmax(0)
        , m_buildVolumeYmax(0)
        , m_buildVolumeZmax(0)
    {
    }

    static Printer::State stateFromString(const std::string &str) {
        if (str == "DISCONNECTED") {
            return Printer::kDisconnected;
        } else if (str == "BUSY") {
            return Printer::kBusy;
        } else if (str == "IDLE") {
            return Printer::kIdle;
        } else if (str == "OPERATION") {
            return Printer::kOperation;
        } else if (str == "PAUSED") {
            return Printer::kPaused;
        } else {
            LOG_ERROR << "Invlaid machine state string: "
                      << str << std::endl;
            return Printer::kInvalid;
        }
    }

    void
    PrinterPrivate::updateFromJson(Json::Value const & json)
    {
        QString const uniqueName(json["uniqueName"].asCString());
        QString const displayName(json["displayName"].asCString());
        bool const canPrint(json["canPrint"].asBool());
        bool const canPrintToFile(json["canPrintToFile"].asBool());
        QString const printerType(QString(json["printerType"].asCString()));
        int const numberOfToolheads(json["numberOfToolheads"].asInt());
        const Printer::State state(stateFromString(json["state"].asString()));
        bool const hasHeatedPlatform(json["hasHeatedPlatform"].asBool());
        QStringList machineNames;
        for(Json::ArrayIndex i = 0; i < json["machineNames"].size(); ++i)
        {
            machineNames << QString(json["machineNames"][i].asCString());
        }
        QString const profileName(
            QString::fromUtf8(json["profile_name"].asCString()));

        float buildVolumeXmin, buildVolumeYmin, buildVolumeZmin,
              buildVolumeXmax, buildVolumeYmax, buildVolumeZmax;

        const std::string buildVolumeKey("build_volume");
        if (json.isMember(buildVolumeKey)) {
            if (json[buildVolumeKey].isArray() &&
                json[buildVolumeKey].size() == 3 &&
                json[buildVolumeKey][0].isNumeric() &&
                json[buildVolumeKey][1].isNumeric() &&
                json[buildVolumeKey][2].isNumeric()) {
              const float buildVolume[3] = {
                json[buildVolumeKey][0].asFloat(),
                json[buildVolumeKey][1].asFloat(),
                json[buildVolumeKey][2].asFloat()
              };
              buildVolumeXmin = buildVolume[0] / -2.0f;
              buildVolumeXmax = buildVolume[0] / 2.0f;

              buildVolumeYmin = buildVolume[1] / -2.0f;
              buildVolumeYmax = buildVolume[1] / 2.0f;

              buildVolumeZmin = 0;
              buildVolumeZmax = buildVolume[2];
            } else {
              LOG_ERROR << "Invalid build_volume: "
                        << json.toStyledString() << std::endl;
            }
        } else {
          LOG_ERROR << "Missing build_volume"
                    << json.toStyledString() << std::endl;
        }

        enum {
          kStateChangeConnected,
          kStateChangeDisconnected,
          kStateNotChanged
        } stateChanged = kStateNotChanged;

        if ((m_state == Printer::kInvalid ||
             m_state == Printer::kDisconnected) &&
            state != Printer::kInvalid &&
            state != Printer::kDisconnected) {
          stateChanged = kStateChangeConnected;
            
        }

        if ((m_state != Printer::kInvalid &&
             m_state != Printer::kDisconnected) &&
            (state == Printer::kInvalid ||
             state == Printer::kDisconnected)) {
          stateChanged = kStateChangeDisconnected;
        }

        m_uniqueName = uniqueName;
        m_displayName = displayName;
        m_machineNames = machineNames;
        m_state = state;
        m_canPrint = canPrint;
        m_canPrintToFile = canPrintToFile;
        m_printerType = printerType;
        m_profileName = profileName;
        m_numberOfToolheads = numberOfToolheads;
        m_hasHeatedPlatform = hasHeatedPlatform;
        m_buildVolumeXmin = buildVolumeXmin;
        m_buildVolumeYmin = buildVolumeYmin;
        m_buildVolumeZmin = buildVolumeZmin;
        m_buildVolumeXmax = buildVolumeXmax;
        m_buildVolumeYmax = buildVolumeYmax;
        m_buildVolumeZmax = buildVolumeZmax;

        // Get firmware version
        const std::string firmwareVersionKey("firmware_version");
        if (json.isMember(firmwareVersionKey)) {
          if (json[firmwareVersionKey].isInt()) {
            const int combinedVersion(json[firmwareVersionKey].asInt());
            if (combinedVersion < 100) {
              // At least a three digit number is expected
              m_firmwareVersion.m_error = kFirmwareVersionTooSmall;
            } else {
              m_firmwareVersion.m_major = combinedVersion / 100;
              m_firmwareVersion.m_minor = (combinedVersion
                                           - m_firmwareVersion.m_major * 100);
              m_firmwareVersion.m_error = kFirmwareVersionOK;
            }
          } else {
            m_firmwareVersion.m_error = kFirmwareVersionNotInteger;
          }
        }
        
        // Temperature of extruder(s) and platform(s)
        if (json.isMember("temperature")) {
            const Json::Value &temperature(json["temperature"]);
            if (temperature.isMember("tools")) {
                ToolTemperature::updateFromJson(m_toolTemperature.tools,
                                                temperature["tools"]);
            }
            if (temperature.isMember("heated_platforms")) {
                ToolTemperature::updateFromJson(m_toolTemperature.heated_platforms,
                                                temperature["heated_platforms"]);
            }
        }

        // Wait to emit signals until all state has been updated
        switch (stateChanged) {
          case kStateChangeConnected:
            m_conveyor->m_private->emitPrinterAdded(m_printer);
            break;

          case kStateChangeDisconnected:
            m_conveyor->m_private->emitPrinterRemoved(m_printer);
            break;

          case kStateNotChanged:
            break;
        }
    }

    Job *
    PrinterPrivate::print (QString const & inputFile
                           , const SlicerConfiguration & slicer_conf
                           , QString const & material
                           , bool const hasStartEnd)
    {
        Job * const result
            ( this->m_conveyor->m_private->print
                ( this->m_printer
                , inputFile
                , slicer_conf
                , material
                , hasStartEnd
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::printToFile
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const hasStartEnd
        , QString const & printToFileType
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->printToFile
                ( this->m_printer
                , inputFile
                , outputFile
                , slicer_conf
                , material
                , hasStartEnd
                , printToFileType
                )
            );
        return result;
    }

    Job *
    PrinterPrivate::slice
        ( QString const & inputFile
        , QString const & outputFile
        , const SlicerConfiguration & slicer_conf
        , QString const & material
        , bool const addStartEnd
        )
    {
        Job * const result
            ( this->m_conveyor->m_private->slice
                ( this->m_printer
                , inputFile
                , outputFile
                , slicer_conf
                , material
                , addStartEnd
                )
            );
        return result;
    }
}
