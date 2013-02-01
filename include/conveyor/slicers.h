// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef SLICERS_H
#define SLICERS_H (1)

#include <QObject>
#include <QString>

#include <jsoncpp/json/value.h>

#include <conveyor/fwd.h>

namespace conveyor
{
    /**
       Settings for the Skeinforge and MiracleGrue slicers
     */
    class SlicerConfiguration
    {
    public:
        enum Slicer {
            Skeinforge,
            MiracleGrue
        };

        enum Preset {
            LowPreset,
            MediumPreset,
            HighPreset,
            SkeinforgePreset
        };

        enum Extruder {
            Left,
            Right,
            LeftAndRight
        };

        static SlicerConfiguration * defaultConfiguration(Preset preset);

        /// Unpack a configuration serialized to JSON
        SlicerConfiguration(Json::Value &);

        /// Serialize configuration as JSON
        Json::Value toJSON() const;

        Slicer slicer() const;
        QString slicerName() const;

        Extruder extruder() const;

        bool raft() const;
        bool supports() const;

        double infill() const;
        double layerHeight() const;
        unsigned shells() const;

        unsigned extruderTemperature() const;
        unsigned platformTemperature() const;

        unsigned printSpeed() const;
        unsigned travelSpeed() const;

        void setSlicer(Slicer slicer);
        void setExtruder(Extruder extruder);

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

    private:
        SlicerConfigurationPrivate * const m_private;
    };
}

#endif
