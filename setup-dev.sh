#! /bin/bash

cd ../s3g
scons
cd ../pyserial
scons
cd ../conveyor
/usr/bin/env python setup_conveyor_env.py submodule/conveyor_bins/python ../s3g/dist/ ../pyserial/dist/
