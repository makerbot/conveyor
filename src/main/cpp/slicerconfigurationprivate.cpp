#include "slicerconfigurationprivate.h"

namespace conveyor
{

    SlicerConfiguration *
    SlicerConfigurationPrivate::defaultConfiguration(Quality quality)
    {
        SlicerConfiguration * const config(new SlicerConfiguration(QString()));

        switch(quality)
        {
        case SlicerConfiguration::LowQuality:
            config->setSlicer(SlicerConfiguration::MiracleGrue);
            config->setLayerHeight(.3);
            break;
        case SlicerConfiguration::MediumQuality:
            config->setSlicer(SlicerConfiguration::MiracleGrue);
            break;
        case SlicerConfiguration::HighQuality:
            config->setSlicer(SlicerConfiguration::Skeinforge);
            break;
        }
        return config;
    }

    SlicerConfigurationPrivate::SlicerConfiguration(Json::Value &) :
        m_slicer(SlicerConfiguration::MiracleGrue),
        m_extruder(Left),
        m_raft(true),
        m_supports(false),
        m_infill(0.90),
        m_layerHeight(0.2),
        m_shells(3),
        m_extruderTemperature(220),
        m_platformTemperature(220),
        m_printSpeed(80),
        m_travelSpeed(150)
    {
        // TODO
    }

    Json::Value SlicerConfigurationPrivate::toJSON() const
    {
        const std::string slicer(slicerName().toStdString());
        Json::Value root;

        // Slicer name and min/max versions
        root["slicer"]["slicerName"] = slicer;
        switch (m_slicer) {
        case SlicerConfiguration::Skeinforge:
            root["slicer"]["minVersion"] = "50.0.0.0";
            root["slicer"]["maxVersion"] = "50.0.0.0";
            break;

        case SlicerConfiguration::MiracleGrue:
            root["slicer"]["minVersion"] = "0.0.4.0";
            root["slicer"]["maxVersion"] = "0.0.5.0";
            break;
        }

        // The rest is formatted to match MiracleGrue's config

        root[slicer]["doRaft"] = m_raft;
        root[slicer]["doSupport"] = m_supports;

        // "extruder" section
        switch (m_extruder) {
        case Left:
            root[slicer]["extruder"]["defaultExtruder"] = 0;
            break;

        case Right:
            root[slicer]["extruder"]["defaultExtruder"] = 1;
            break;
        }

        root[slicer]["infillDensity"] = m_infill;
        root[slicer]["layerHeight"] = m_layerHeight;
        root[slicer]["numberOfShells"] = m_shells;
        root[slicer]["rapidMoveFeedRateXY"] = m_travelSpeed;

        const char *profiles[] = {"insets",
                                  "infill",
                                  "firstlayer",
                                  "outlines"};

        for (int i = 0; i < 4; ++i) {
            root[slicer]["extrusionProfiles"][profiles[i]]["temperature"] =
                m_extruderTemperature;
            root[slicer]["extrusionProfiles"][profiles[i]]["feedrate"] =
                m_printSpeed;
        }

        // Nothing variable here, not sure if needed?
        for (int i = 0; i < 2; ++i) {
            root["extruderProfiles"][i]["firstLayerExtrusionProfile"] = "firstlayer";
            root["extruderProfiles"][i]["insetsExtrusionProfile"] = "insets";
            root["extruderProfiles"][i]["infillsExtrusionProfile"] = "infill";
            root["extruderProfiles"][i]["outlinesExtrusionProfile"] = "outlines";
        }

        // TODO: not in miracle.conf?
        root[slicer]["platformTemperature"] = m_platformTemperature;

        return root;
    }

    SlicerConfiguration::Slicer SlicerConfigurationPrivate::slicer() const
    {
        return m_slicer;
    }

    QString SlicerConfigurationPrivate::slicerName() const
    {
        switch (m_slicer) {
        case SlicerConfiguration::Skeinforge:
            return "Skeinforge";
        case SlicerConfiguration::MiracleGrue:
            return "MiracleGrue";
        default:
            return QString();
        }
    }

    SlicerConfiguration::Extruder SlicerConfigurationPrivate::extruder() const
    {
        return m_extruder;
    }

    QString SlicerConfigurationPrivate::extruderName() const
    {
        switch (m_extruder) {
        case SlicerConfiguration::Left:
            return "Left";
        case SlicerConfiguration::Right:
            return "Right";
        default:
            return QString();
        }
    }

    bool SlicerConfigurationPrivate::raft() const
    {
        return m_raft;
    }

    bool SlicerConfigurationPrivate::supports() const
    {
        return m_supports;
    }

    double SlicerConfigurationPrivate::infill() const
    {
        return m_infill;
    }

    double SlicerConfigurationPrivate::layerHeight() const
    {
        return m_layerHeight;
    }

    unsigned SlicerConfigurationPrivate::shells() const
    {
        return m_shells;
    }

    unsigned SlicerConfigurationPrivate::extruderTemperature() const
    {
        return m_extruderTemperature;
    }

    unsigned SlicerConfigurationPrivate::platformTemperature() const
    {
        return m_platformTemperature;
    }

    unsigned SlicerConfigurationPrivate::printSpeed() const
    {
        return m_printSpeed;
    }

    unsigned SlicerConfigurationPrivate::travelSpeed() const
    {
        return m_travelSpeed;
    }

    void SlicerConfigurationPrivate::setSlicer(SlicerConfiguration::Slicer slicer)
    {
        m_slicer = slicer;
    }

    void SlicerConfigurationPrivate::setExtruder(SlicerConfiguration::Extruder extruder)
    {
        m_extruder = extruder;
    }

    void SlicerConfigurationPrivate::setRaft(bool raft)
    {
        m_raft = raft;
    }

    void SlicerConfigurationPrivate::setSupports(bool supports)
    {
        m_supports = supports;
    }

    void SlicerConfigurationPrivate::setInfill(double infill)
    {
        m_infill = infill;
    }

    void SlicerConfigurationPrivate::setLayerHeight(double height)
    {
        m_layerHeight = height;
    }

    void SlicerConfigurationPrivate::setShells(unsigned shells)
    {
        m_shells = shells;
    }

    void SlicerConfigurationPrivate::setExtruderTemperature(unsigned temperature)
    {
        m_extruderTemperature = temperature;
    }

    void SlicerConfigurationPrivate::setPlatformTemperature(unsigned temperature)
    {
        m_platformTemperature = temperature;
    }

    void SlicerConfigurationPrivate::setPrintSpeed(unsigned speed)
    {
        m_printSpeed = speed;
    }

    void SlicerConfigurationPrivate::setTravelSpeed(unsigned speed)
    {
        m_travelSpeed = speed;
    }
}
