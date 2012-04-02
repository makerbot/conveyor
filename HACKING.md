Conveyor
========

Conveyor is our new printing dispatch system.

Prerequisites
-------------

    * Python 2.7
    * Virtualenv

On Ubuntu these dependencies can be installed by issuing this command:

        $ sudo apt-get install python-dev python-virtualenv

Configuration
-------------

Use `setup.sh` to create and configure the virtualenv:

        $ ./setup.sh

Activate the virtualenv:

        $ . virtualenv/bin/activate

Unit Tests
----------

Some of the tests require that a toolpath generator and printer are available
over D-Bus. These test will fail when the services are not available, but most
other tests will run correctly.

The toolpath generator and printer services are available from the "service"
branch of ReplicatorG.

Start a toolpath generator process:

        $ cd ReplicatorG-service
        $ ant run -Drun.arguments="toolpathGenerator --bus-name com.makerbot.ToolpathGenerator0"

Start a printer process:

        $ cd ReplicatorG-service
        $ ant run -Drun.arguments="printer --bus-name com.makerbot.Printer0"

These particular bus names are required for the test suite.

Run the test suite:

        $ ./test.sh

The current D-Bus services are unable to detect and report various sorts of
errors. The test suite may report success even if your actual print fails.

NOTE: older versions of unittest (i.e., those before Python 2.7's unittest2)
have trouble finding the tests.
