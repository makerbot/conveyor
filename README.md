# conveyor

the conveyor module handles machine connections and is the commnunication link bewtween Makerware UI and makerbot_driver

##Repository Setup
To run conveyor from the command line, you must also clone the s3g (makerbot_driver) repository. If you want to slice models, you must also clone the Miracle-Grue Repository or the Skeinforge repository.  These repositorys must be installed at the same folder level as conveyor. To use Miracle-Grue, you must build a miracle-grue binary.  Instructions for this are contained in the Miracle Grue repository.  

##VirtualEnv
Due to makerbot_driver's dependency on our (Makerbot Industries) own version of pyserial, and for the sake of not polluting your own system that may have the 'true' version of pyserial installed, you must invoke conveyor inside a virtualenv.  We provide the necessary files to operate inside a VirtualEnv that will install all dependencies for you without polluting your own machine.  

First, obtain a copy of our version of pyserial.  This can be done VIA git.  On the same directory level as makerbot_driver, in a terminal window issue:

    git clone git@github.com:makerbot/pyserial.git

Dependent submodules must be up to date to run the virutalenv.  In the root directory of makerbot_driver, issue:
  
    git submodule update --init

To create the VirtualEnv, inside the root directory of the makerbot_driver folder, issue:

    python virtualenv.py virtualenv

To configure the VirtualEnv, navigate to the root directory of the makerbot_driver driver and, in a terminal issue:

    ./setup.sh

To activate the VirtualEnv, in the root directory of the makerbot_driver driver, issue:

    . virtualenv/bin/activate

##Additional Conveyor dependencies
Conveyor relies on submodules.  Set these up using:

    git submodule update --init

Then get the pyserial egg using:

    cd submodule/conveyor_bins
    easy_install pyserial-2.7_mb2.1-py2.7.egg

Note the pyserial egg can also be activated from the makerbot_driver directory using the same process.  This is an option if there are any issues running the install in the conveyor directory.

##Running Conveyor
Conveyor has a server-client organization.  The conveyor server runs continually, and the conveyor client makes requests to the server. You can run both the server and client processes in the same command line terminal, but it is often advantageous to run them in  separate terminals.

To start the conveyor_service, from the top level of the conveyor directory, run:

    python conveyor_service.py  -c conveyor-dev.conf --nofork

conveyor-dev.conf is the configuration file used for the dev configuration.  This file describes the repository dependecies described at the top.  Install versions of Makerware have an alternate conf file.  If you want to print debug messages while running the conveyor server, use the flag '-l  DEBUG'.  

Run the conveyor client in a seperate terminal.  first activate the virtual env.  from the top level of the conveyor directory, run:

    . virtualenv/bin/activate

There are a number of client operations that can be performed.  To print to a connected bot, run:

    python conveyor_cmdline_client.py -c conveyor-dev.conf print 'intputfile'

To build a model to an s3g/x3g file, use:

    python conveyor_cmdline_client.py -c conveyor-dev.conf printtofile 'inputfile' 'outputfile'

These commands will run with default configurations.  To view configuration options for an operation, use the -h flag.  To see a list of operations run:

    python conveyor_cmdline_clieny.py -c conveyor-dev.conf list


Logging messages while running conveyor are stored in the conveyord.log file, located at the top level of the conveyor directory.  


