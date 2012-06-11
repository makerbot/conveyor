Conveyor
========

Conveyor is our new printing dispatch system.

Prerequisites
-------------

* Python 2.7
* Virtualenv

On Ubuntu these dependencies can be installed by issuing this command:

        $ sudo apt-get install python-dev python-virtualenv python-serial

Configuration
-------------

Use `setup.sh` to create and configure the virtualenv:

        $ ./setup.sh

Activate the virtualenv:

        $ . virtualenv/bin/activate

Unit Tests
----------

Run the test suite:

        $ ./test.sh

Run conveyord
-------------

The file `conveyor-user.conf` is designed to let you run `conveyord` out of the
source tree. It writes the socket, log file, and PID file to the current
directory.

        $ ./conveyord -c conveyor-user.conf

The daemon will detach from the controlling terminal and run in the background.
You can prevent that by running it with the `--nofork` option:

        $ ./conveyord -c conveyor-user.conf --nofork

The daemon also accepts a command-line option to specify the log level:

        $ ./conveyord -c conveyor-user.conf -l DEBUG

What Threads Are Running in conveyord?
--------------------------------------

`conveyord` will log the active threads when it receives a `SIGUSR1` (on
platforms that have `SIGUSR1`):

        $ kill -USR1 `cat conveyord.pid`

Kill conveyord
--------------

        $ kill `cat conveyord.pid`

Print and Slice
---------------

Once the daemon is running you can print and slice[*]:

        $ ./conveyor -c conveyor-user.conf print src/test/thing/rfc-4.1/

        $ ./conveyor -c conveyor-user.conf printtofile src/test/thing/rfc-4.1/ output.s3g

        $ ./conveyor -c conveyor-user.conf slice src/test/thing/rfc-4.1/ output.gcode

[*] These commands may or may not actually do anything right now.
