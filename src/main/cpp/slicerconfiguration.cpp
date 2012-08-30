#include <conveyor.h>

using namespace conveyor;

SlicerConfiguration *
SlicerConfiguration::miracleGrueDefaults(__attribute__((unused)) Quality quality)
{
    SlicerConfiguration * const config(new SlicerConfiguration(QString()));
    return config;
}

SlicerConfiguration *
SlicerConfiguration::skeinforgeDefaults(__attribute__((unused)) Quality quality)
{
    SlicerConfiguration * const config(new SlicerConfiguration(QString()));
    return config;
}

SlicerConfiguration::SlicerConfiguration(const QString &) :
    m_slicer(MiracleGrue),
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

Json::Value SlicerConfiguration::toJSON() const
{
    const std::string slicer(slicerName().toStdString());
    Json::Value root;

    // Slicer name and min/max versions
    root["slicer"]["slicerName"] = slicer;
    switch (m_slicer) {
    case Skeinforge:
        root["slicer"]["minVersion"] = "50.0.0.0";
        root["slicer"]["maxVersion"] = "50.0.0.0";
        break;

    case MiracleGrue:
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

SlicerConfiguration::Slicer SlicerConfiguration::slicer() const
{
    return m_slicer;
}

QString SlicerConfiguration::slicerName() const
{
    switch (m_slicer) {
    case Skeinforge:
        return "Skeinforge";
    case MiracleGrue:
        return "MiracleGrue";
    default:
        return QString();
    }
}

SlicerConfiguration::Extruder SlicerConfiguration::extruder() const
{
    return m_extruder;
}

QString SlicerConfiguration::extruderName() const
{
    switch (m_extruder) {
    case Left:
        return "Left";
    case Right:
        return "Right";
    default:
        return QString();
    }
}

bool SlicerConfiguration::raft() const
{
    return m_raft;
}

bool SlicerConfiguration::supports() const
{
    return m_supports;
}

double SlicerConfiguration::infill() const
{
    return m_infill;
}

double SlicerConfiguration::layerHeight() const
{
    return m_layerHeight;
}

unsigned SlicerConfiguration::shells() const
{
    return m_shells;
}

unsigned SlicerConfiguration::extruderTemperature() const
{
    return m_extruderTemperature;
}

unsigned SlicerConfiguration::platformTemperature() const
{
    return m_platformTemperature;
}

unsigned SlicerConfiguration::printSpeed() const
{
    return m_printSpeed;
}

unsigned SlicerConfiguration::travelSpeed() const
{
    return m_travelSpeed;
}

void SlicerConfiguration::setSlicer(Slicer slicer)
{
    m_slicer = slicer;
}

void SlicerConfiguration::setExtruder(Extruder extruder)
{
    m_extruder = extruder;
}

void SlicerConfiguration::setRaft(bool raft)
{
    m_raft = raft;
}

void SlicerConfiguration::setSupports(bool supports)
{
    m_supports = supports;
}

void SlicerConfiguration::setInfill(double infill)
{
    m_infill = infill;
}

void SlicerConfiguration::setLayerHeight(double height)
{
    m_layerHeight = height;
}

void SlicerConfiguration::setShells(unsigned shells)
{
    m_shells = shells;
}

void SlicerConfiguration::setExtruderTemperature(unsigned temperature)
{
    m_extruderTemperature = temperature;
}

void SlicerConfiguration::setPlatformTemperature(unsigned temperature)
{
    m_platformTemperature = temperature;
}

void SlicerConfiguration::setPrintSpeed(unsigned speed)
{
    m_printSpeed = speed;
}

void SlicerConfiguration::setTravelSpeed(unsigned speed)
{
    m_travelSpeed = speed;
}
