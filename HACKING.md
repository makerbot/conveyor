Conveyor
========

Conveyor is our new printing dispatch system. This is a client/server system for dispatching
Printer related tasks into dispatchable lambda calculus, to make a fast and easy
system for chaining tasks, etc.


Prerequisites
-------------

* Python 2.7 (Python 2.6 acceptable) 

On Ubuntu these dependencies can be installed by issuing this command:
        $ sudo apt-get install python-dev

On Mac these dependencies can be installed by ???:

On Windows these dependencies can be installed by downloading the Python 2.7 MSI package :
	


Configuration
-------------
To create the environment the setup scripts download and install several packages. 
TRICKY: we use a custom pyserial module that may not be good for general installs, so it should only
be installed in our own virtualenv space. 

On Ubuntu/Mac use `setup.sh` to download pip packages, and create and configure the virtualenv:
        $ source ./setup.sh
To activate the virtualenv, and set env. variables, use setup as well:
        $ source ./setup.sh

On Windows use `setup.bat` to download pip packages, and create and configure the virtualenv:
        C:\> setup.bat
To activate the virtualenv, and setup environemnt varibles, use setup as well:
        C:\> setup.bat
	

Unit Tests
----------
On Ubuntu/Mac Run the test suite:
        $ ./test.sh
On Windows the test suite:
        $ ./test.bat
        


Run conveyord ( Conveyor Service Daemon )
-------------

conveyord is the Conveyor Service Daemon. This process runs in the background and dispatches
tasks to various engines/processes/tasks based on recipe. 

The file `conveyor.conf` contains configuration information for the 
deamon service. This configuration is designed to let you run `conveyord` out of the source tree. It writes the socket, log file, and PID file to the current
directory.

In Linux/Mac To launch the service daemon in userland, use 
        $ python conveyord.py -c conveyor.conf

In Windows you must specify to 'nofork' and the win32 config due to some OS restrictions.  
        $ python conveyord.py -c conveyor-win32.conf --nofork

The daemon will detach from the controlling terminal and run in the background.
You can prevent that by running it with the `--nofork` option:
        $ ./conveyord -c conveyor.conf --nofork

The daemon also accepts a command-line option to specify the log level:
        $ ./conveyord -c conveyor.conf -l DEBUG


What Threads Are Running in conveyord?
--------------------------------------

Linux/Mac: 
`conveyord` will log the active threads when it receives a `SIGUSR1` (on
platforms that have `SIGUSR1`):

        $ kill -USR1 `cat conveyord.pid`

'conveyord' will also create a lock file at a location sepecified in the configuration file's 'common' section, under the key 'daemon_lock'. If that lock file exists, 
it indicates that conveyord is running, and may accept jobs


To stop conveyord running (kill it!) 
--------------
The conveyord registers it's pid (process id) in a file in the running directory.
To kill it, simply kill it via the stored pid using: 

        $ kill `cat conveyord.pid`



Run conveyorc ( Conveyor Commandline Client )
-------------
Once the daemon is running you can connect to it using a command line client. to 
run various operations. 


View client options: 
---------------
To see what options are available in your client, you can simply run 
        $ python conveyor.py -c conveyor.conf -h 

Printing and slicing 
---------------
A couple of common uses for conveyor client are to: 

Print a 'thing' directory to a s3g file:
        $ python conveyor.py -c conveyor.conf printtofile src/test/thing/rfc-4.1/ output.s3g

Convert a gcode file into an s3g file:
        $ python conveyor.py -c conveyor.conf printtofile ./src/test/gcode/single.gcode test.s3g

Slice a stl file into a gcode file: 
		$ python conveyor_cmdline_client.py -c conveyor.conf slice ./src/test/stl/single.stl test.gcode
        
