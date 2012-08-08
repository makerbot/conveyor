#ifndef FAKEPRINTER_H
#define FAKEPRINTER_H (1)

#include <QTimer>

#include "conveyor.h"

namespace conveyor
{
    class FakePrinter : public Printer
    {
            Q_OBJECT
    public:
        FakePrinter
			( Conveyor * convey
			, QString const & name);
		
        FakePrinter
			( Conveyor * convey
			, QString const & name
			, bool const & canPrint
			, bool const & canPrintToFile
			, ConnectionStatus const & cs
			, QString const & printerType
			, int const & numberOfExtruders
			, bool const & hasHeatedPlatform);
		
        void startCurrentJob();
        void stopCurrentJob();
        void startRandomConnectionStatus();
        void stopRandomConnectionStatus();
		
        Job * print       (QString const & inputFile);
        Job * printToFile (QString const & inputFile, QString const & outputFile);
        Job * slice       (QString const & inputFile, QString const & outputFile);
		
    private slots:
        void emitRandomConnectionStatus();
		
    public slots:
        virtual void togglePaused();
        virtual void cancelCurrentJob();

    private:
        QTimer m_jobTimer;
        QTimer m_connectionTimer;
    };
}

#endif // FAKEPRINTER_H