# conveyor

the conveyor module handles machine connections

##VirtualEnv
Due to makerbot_driver's dependency on our (Makerbot Industries) own version of pyserial, and for the sake of not polluting your own system that may have the 'true' version of pyserial installed, we suggest invoking makerbot_driver inside a virtualenv.  We provide the necessary files to operate inside a VirtualEnv that will install all dependencies for you without polluting your own machine.  

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

##AVRDude

makerbot_driver uses AVRDude to upload firmware to the machine.  Because AVRDude is platform
specific, the user needs to copy over the correct AVRDude executable to makerbot_driver/Firmware.

On all platforms, the protocol for invoking AVRDude is to first search for a local AVRDude executable.
In the event that no local binary is found, we attempt to invoke an AVRDude defined in the user's path.

###Mac and Windows Distributions

Running the copy_avrdude.py script will copy the correct avrdude executable from conveyor_bins.
To execute:

    python copy_avrdude.py

###Linux Distributions

On linux systems, we request that the user use a distribution service (i.e. 'apt-get') to pull
down AVRDude.

##Machine Connection

To connect to a machine, you will need the following module:

* [pySerial](http://pypi.python.org/pypi/pyserial).

To run the unit tests, you will need the following modules:

* [Mock](http://pypi.python.org/pypi/mock) (Note: Use version 0.8 or greater)
* [unittest2](http://pypi.python.org/pypi/unittest2) (Python 2.6 and earlier)

## Example: Connecting to a Replicator
Import both the makerbot_driver module and pyserial:

```python
import makerbot_driver, serial
```

Create an makerbot_driver object, and attach it to a serial port:

```python
r = makerbot_driver.s3g()
file = serial.Serial(port, 115200, timeout=1)
r.writer = makerbot_driver.Writer.StreamWriter(file)
```

_Note: Replace port with your serial port (example: '/dev/tty.usbmodemfd121')_

Home the x, y, and z axes:

```python
r.find_axes_maximums(['x', 'y'], 500, 60)
r.find_axes_minimums(['z'], 500, 60)
r.recall_home_positions(['x', 'y', 'z', 'a', 'b'])
```

Instruct the machine to move in a square pattern:

```python
r.queue_extended_point([2000,0,5000,0,0], 400)
r.queue_extended_point([2000,2000,5000,0,0], 400)
r.queue_extended_point([0,2000,5000,0,0], 400)
r.queue_extended_point([0,0,5000,0,0], 400)
```

_Note: All points are in steps, and all speeds are in DDA. This is s3g, not gcode!_

Now, instruct the machine to heat toolhead 0, wait up to 5 minutes for it to reach temperature, then extrude for 12.5 seconds:

```python
r.set_toolhead_temperature(0, 220)
r.wait_for_tool_ready(0,100,5*60)
r.queue_extended_point([0,0,5000,-5000,0], 2500)
```

Finally, don't forget to turn off the toolhead heater, and disable the stepper motors:

```python
r.set_toolhead_temperature(0,0)
r.toggle_axes(['x','y','z','a','b'],False)
```

Those are the basics of how to control a machine. For more details, consult the [s3g protocol](https://github.com/makerbot/s3g/blob/master/doc/s3g_protocol.markdown) and the [s3g source](https://github.com/makerbot/s3g/blob/master/s3g/s3g.py).

# Data types
There are a few specific data formats that are used throughout this module, that warrant further explanation here.

## Points
Points come in two flavors: regular and extended.

Regular points are expressed as a list of x, y, and z coordinates:

    [x, y, z]

Extended points are expressed as a list of x, y, a, and b coordinates:

    [x, y, z, a, b]

## Axes Lists
There are several commands that require a list of axes as input.  This parameter is passed as a python list of strings, where each axis is its own separate string.  To pass in all axes:

    ['x', 'y', 'z', 'a', 'b']

# Error handling
The makerbot_driver module will raise an exception if it encounters a problem during transmission. Conditions, such as timeouts, bad packets being received from the bot and poorly formatted parameters all can cause the makerbot_driver module to raise exceptions.  Some of these states are recoverable, while some require a machine restart.  We can categorize makerbot_driver's error states into the following:

TODO: This is largely duplicated in the errors.py doc, consider rewriting as a summary of the base error types only.

## Buffer Overflow Error (used internally)
A Buffer Overflow Error is raised when the machine has full buffer.

## Retryable Errors (used internally)
Retryable Errors are non-catastrophic errors raised by makerbot_driver.  While alone they cannot cause makerbot_driver to terminate, an aggregate of 5 errors will cause makerbot_driver to quit.

    Packet Decode Errors
    Generic Errors
    CRC Mismatch Errors
    Timeout Errors

## Packet Decode Errors (used internally):
Packet decode errors are raised if there is a problem evaluating a return packet from an s3g Host:

    Bad Packet Lengths
    Bad Packet Field Lenghts
    Bad Packet CRCs
    Bad Packet Headers

## Transmission Errors:
Transmission Errors are thrown when more than 5 Retryable Errors are raised.

## Protocol Errors
These errors are caused by ostensibly well formed packets returned from the machine, but with incorrect data:

    Bad Heat Element Ready Responses
    Bad EEPROM Read/Write Lengths
    UnrecognizedResponseError

## Parameter Errors
Parameter errors are raised when imporperly formatted arguments are passed into an s3g function.

    Bad Point Length
    EEPROM Read/Write length too long
    Bad Tool Index
    Bad button name

## ToolBusError (used internally):
Tool Bus errors are raised when the machine cannot communicate with its toolbus.

    Downstream Timeout Error
    Tool Lock Error

## Other Errors
Bot generated errors will throw their own specific errors, such as:

    SD Card Errors
    Extended Stop Errors
    Build Cancel Errors

## GCode Errors
GCode errors are thrown when reading through a GCode file and parsing out g/m codes and comments.
Cause By:

    Improperly Formatted Comments
    Bad Codes
    Codes That Are Repeated Multiple Times On A Single Line
    M And G Codes Present On The Same Line
   
## External Stop Error
An External Stop Error is raised when an external thread sets the External Stop Flag in makerbot_driver.Writer.StreamWriter to true, which terminates the Stream Writer's packet sending process.
 
## S3G Stream Reading Errors
These errors are thrown when the makerbot_driver module encounters errors during makerbot_driver stream parsing.  
Caused By:

    Encoded Strings Above The Max Payload Length


# Contributing
Contributions are welcome to this project! All changes must be in the style of the project, and include unit tests that are as complete as possible. Place all source code in the s3g/ directory, and all tests in the tests/ directory. Before submitting a patch, ensure that all unit tests pass by running the unit test script:

```python
python unit_tests.py
```
