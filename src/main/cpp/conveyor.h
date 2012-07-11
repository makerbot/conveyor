// vim:cindent:cino=\:0:et:fenc=utf-8:ff=unix:sw=4:ts=4:

#ifndef CONVEYOR_H
#define CONVEYOR_H (1)

#include <QList>
#include <QObject>
#include <QSharedPointer>

namespace conveyor
{
    class Address;
    class Conveyor;
    class Job;
    class Printer;

    struct ConveyorPrivate;
    struct JobPrivate;
    struct PrinterPrivate;

    typedef QSharedPointer<Conveyor> ConveyorPointer;
    typedef QSharedPointer<Job> JobPointer;
    typedef QSharedPointer<Printer> PrinterPointer;

    class Address : public QObject
    {
        Q_OBJECT
    };

    class Conveyor : public QObject
    {
        Q_OBJECT

    public:
        explicit Conveyor (Address const & address);

        QList<JobPointer>     jobs     (void);
        QList<PrinterPointer> printers (void);

        friend class Job;
        friend class Printer;

    private:
        ConveyorPrivate const * m_private;
    };

    class Job : public QObject
    {
        Q_OBJECT

    public:
        Job (PrinterPointer printerPointer, QString const & id);

        friend class Conveyor;
        friend class Printer;

    private:
        JobPrivate * const m_private;
    };

    class Printer : public QObject
    {
        Q_OBJECT

    public:
        Printer (ConveyorPointer conveyorPointer, QString const & name);

        QList<JobPointer> jobs (void);

        JobPointer print       (QString const & inputFile);
        JobPointer printToFile (QString const & inputFile, QString const & outputFile);
        JobPointer slice       (QString const & inputFile, QString const & outputFile);

        friend class Conveyor;
        friend class Job;

    private:
        PrinterPrivate * const m_private;
    };
}

#endif
