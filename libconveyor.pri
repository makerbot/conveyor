#-------------------------------------------------
# QMake project include file
#
# include( libconveyor.pri ) in your pro file
# to include the conveyor libraries.
#
#-------------------------------------------------

win32 {
LIBS += $$PWD/bin/conveyor.dll

PRE_TARGETDEPS += $$PWD/bin/conveyor.dll
} else {
LIBS += $$PWD/bin/libconveyor.so

PRE_TARGETDEPS += $$PWD/bin/libconveyor.so
}

INCLUDEPATH += $$PWD/src/main/cpp
