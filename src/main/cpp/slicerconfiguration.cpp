#include <conveyor.h>

using namespace conveyor;

SlicerConfiguration::SlicerConfiguration(const QString &) :
    m_slicer(MiracleGrue),
    m_raft(true),
    m_supports(false),
    m_infill(90),
    m_layerHeight(0.2),
    m_shells(3),
    m_leftExtruderTemperature(220),
    m_rightExtruderTemperature(220),
    m_platformTemperature(220),
    m_printSpeed(80),
    m_travelSpeed(150)
{
    // TODO
}

Json::Value SlicerConfiguration::toJSON() const
{
    Json::Value root;

    root["slicer"] = slicerName().toStdString();
    root["raft"] = m_raft;
    root["supports"] = m_supports;
    root["infill"] = m_infill;
    root["layerHeight"] = m_layerHeight;
    root["shells"] = m_shells;
    root["leftExtruderTemperature"] = m_leftExtruderTemperature;
    root["rightExtruderTemperature"] = m_rightExtruderTemperature;
    root["platformTemperature"] = m_platformTemperature;
    root["printSpeed"] = m_printSpeed;
    root["travelSpeed"] = m_travelSpeed;

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

unsigned SlicerConfiguration::leftExtruderTemperature() const
{
    return m_leftExtruderTemperature;
}

unsigned SlicerConfiguration::rightExtruderTemperature() const
{
    return m_rightExtruderTemperature;
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

void SlicerConfiguration::setLeftExtruderTemperature(unsigned temperature)
{
    m_leftExtruderTemperature = temperature;
}

void SlicerConfiguration::setRightExtruderTemperature(unsigned temperature)
{
    m_rightExtruderTemperature = temperature;
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
