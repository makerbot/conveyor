// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SLICERCONFIGURATIONPRIVATE_H
#define SLICERCONFIGURATIONPRIVATE_H (1)

#include <QObject>
#include <QString>

#include <jsoncpp/json/value.h>

#include <conveyor/fwd.h>

#include <conveyor/slicers.h>

namespace conveyor
{
    /**
       Settings for the Skeinforge and MiracleGrue slicers
     */
    class SlicerConfigurationPrivate
    {
    public:
        static SlicerConfiguration * defaultConfiguration(
            SlicerConfiguration::Preset preset);

        /// Unpack a configuration serialized to JSON
        SlicerConfigurationPrivate(Json::Value &);

        /// Serialize configuration as JSON
        Json::Value toJSON() const;

        SlicerConfiguration::Slicer slicer() const;
        QString slicerName() const;

        SlicerConfiguration::Extruder extruder() const;

        bool raft() const;
        bool supports() const;

        double infill() const;
        double layerHeight() const;
        unsigned shells() const;

        unsigned extruderTemperature() const;
        unsigned platformTemperature() const;

        unsigned printSpeed() const;
        unsigned travelSpeed() const;

        void setSlicer(SlicerConfiguration::Slicer slicer);
        void setExtruder(SlicerConfiguration::Extruder extruder);

        void setRaft(bool raft);
        void setSupports(bool supports);

        void setInfill(double infill);
        void setLayerHeight(double height);
        void setShells(unsigned shells);

        void setExtruderTemperature(unsigned temperature);
        void setPlatformTemperature(unsigned temperature);

        void setPrintSpeed(unsigned speed);
        void setTravelSpeed(unsigned speed);

        void setProfilePath(const QString &path);

        SlicerConfiguration::Slicer m_slicer;
        SlicerConfiguration::Extruder m_extruder;

        bool m_raft;
        bool m_supports;

        double m_infill;
        double m_layerHeight;
        unsigned m_shells;

        unsigned m_extruderTemperature;
        unsigned m_platformTemperature;

        unsigned m_printSpeed;
        unsigned m_travelSpeed;

        QString m_profilePath;
    };
}

#endif // SLICERCONFIGURATIONPRIVATE
