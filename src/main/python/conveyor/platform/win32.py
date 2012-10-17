# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:ts=4:
# conveyor/src/main/python/conveyor/platform/win32.py
#
# conveyor - Printing dispatch engine for 3D objects and their friends.
# Copyright © 2012 Matthew W. Samsonoff <matthew.samsonoff@makerbot.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import (absolute_import, print_function, unicode_literals)

import ctypes
import ctypes.wintypes

"""
This file contains a bunch of platform tools and defines needed to get windows sockets
working. These are just accessory/helper functions for conveyor.connections on windows
"""


def create_WindowsError(error):
    message = ctypes.wintypes.WinError(error)
    e = WindowsError(error, message)
    return e

_kernel32 = ctypes.WinDLL('kernel32')

# Windows Data Types
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa383751%28v=vs.85%29.aspx

LPCVOID = ctypes.c_void_p
LPDWORD = ctypes.POINTER(ctypes.wintypes.DWORD)
PVOID = ctypes.c_void_p

# 64-bit Windows uses the LLP64 model (unlike almost everything else).


def _win64():
    return 8 == ctypes.sizeof(ctypes.c_void_p)

if _win64():
    ULONG_PTR = ctypes.c_int64
else:
    ULONG_PTR = ctypes.c_ulong

# OVERLAPPED
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms684342%28v=vs.85%29.aspx


class _OVERLAPPED_OFFSET(ctypes.Structure):
    _fields_ = [
        ('Offset', ctypes.wintypes.DWORD),
        ('OffsetHigh', ctypes.wintypes.DWORD),
    ]


class _OVERLAPPED_UNION(ctypes.Union):
    _anonymous_ = ['_offset']
    _fields_ = [
        ('_offset', _OVERLAPPED_OFFSET),
        ('Pointer', PVOID),
    ]


class OVERLAPPED(ctypes.Structure):
    _anonymous_ = ['_union']
    _fields_ = [
        ('Internal', ULONG_PTR),
        ('InternalHigh', ULONG_PTR),
        ('_union', _OVERLAPPED_UNION),
        ('hEvent', ctypes.wintypes.HANDLE),
    ]

LPOVERLAPPED = ctypes.POINTER(OVERLAPPED)

# SECURITY_ATTRIBUTES
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa379560%28v=vs.85%29.aspx


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ('nLength', ctypes.wintypes.DWORD),
        ('lpSecurityDescriptor', ctypes.wintypes.LPVOID),
        ('bInheritHandle', ctypes.wintypes.BOOL),
    ]

LPSECURITY_ATTRIBUTES = ctypes.POINTER(SECURITY_ATTRIBUTES)

# CreateEvent
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms682396%28v=vs.85%29.aspx

CreateEventW = _kernel32.CreateEventW
CreateEventW.restype = ctypes.wintypes.HANDLE
CreateEventW.argtypes = [
    LPSECURITY_ATTRIBUTES,   # lpEventAttributes [in, optional]
    ctypes.wintypes.BOOL,    # bManualReset [in]
    ctypes.wintypes.BOOL,    # bInitialState [in]
    ctypes.wintypes.LPCWSTR,  # lpName [in, optional]
]

# CreateFile
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa363858%28v=vs.85%29.aspx

CreateFileW = _kernel32.CreateFileW
CreateFileW.restype = ctypes.wintypes.HANDLE
CreateFileW.argtypes = [
    ctypes.wintypes.LPCWSTR,  # lpFileName [in]
    ctypes.wintypes.DWORD,   # dwDesiredAccess [in]
    ctypes.wintypes.DWORD,   # dwShareMode [in]
    LPSECURITY_ATTRIBUTES,   # lpSecurityAttributes [in, optional]
    ctypes.wintypes.DWORD,   # dwCreationDisposition [in]
    ctypes.wintypes.DWORD,   # dwFlagsAndAttributes [in]
    ctypes.wintypes.HANDLE,  # hTemplateFile [in, optional]
]

OPEN_EXISTING = 3
FILE_FLAG_OVERLAPPED = 0x40000000L

# CreateNamedPipe
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa365150%28v=vs.85%29.aspx

CreateNamedPipeW = _kernel32.CreateNamedPipeW
CreateNamedPipeW.restype = ctypes.wintypes.HANDLE
CreateNamedPipeW.argtypes = [
    ctypes.wintypes.LPCWSTR,  # lpName [in]
    ctypes.wintypes.DWORD,   # dwOpenMode [in]
    ctypes.wintypes.DWORD,   # dwPipeMode [in]
    ctypes.wintypes.DWORD,   # nMaxInstances [in]
    ctypes.wintypes.DWORD,   # nOutBufferSize [in]
    ctypes.wintypes.DWORD,   # nInBufferSize [in]
    ctypes.wintypes.DWORD,   # nDefaultTimeOut [in]
    LPSECURITY_ATTRIBUTES,   # lpSecurityAttributes [in, optional]
]

PIPE_ACCESS_DUPLEX = 0x00000003L
PIPE_TYPE_MESSAGE = 0x00000004L
PIPE_READMODE_MESSAGE = 0x00000002L
PIPE_WAIT = 0x00000000L
PIPE_UNLIMITED_INSTANCES = 255


# ConnectNamedPipe
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa365146%28v=vs.85%29.aspx

ConnectNamedPipe = _kernel32.ConnectNamedPipe
ConnectNamedPipe.restype = ctypes.wintypes.HANDLE
ConnectNamedPipe.argtypes = [
    ctypes.wintypes.HANDLE,  # hNamedPipe [in]
    LPOVERLAPPED,           # lpOverlapped [in, out, optional]
]

# GetLastError
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms679360%28v=vs.85%29.aspx

GetLastError = _kernel32.GetLastError
GetLastError.restype = ctypes.wintypes.DWORD
GetLastError.argtypes = []

# GetOverlappedResult
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms683209%28v=vs.85%29.aspx

GetOverlappedResult = _kernel32.GetOverlappedResult
GetOverlappedResult.restype = ctypes.wintypes.BOOL
GetOverlappedResult.argtypes = [
    ctypes.wintypes.HANDLE,  # hFile [in]
    LPOVERLAPPED,           # lpOverlapped [in]
    LPDWORD,                # lpNumberOfBytesTransferred [out]
    ctypes.wintypes.BOOL,   # bWait [in]
]

# ReadFile
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa365467%28v=vs.85%29.aspx

ReadFile = _kernel32.ReadFile
ReadFile.restype = ctypes.wintypes.BOOL
ReadFile.argtypes = [
    ctypes.wintypes.HANDLE,  # hFile [in]
    ctypes.wintypes.LPVOID,  # lpBuffer [out]
    ctypes.wintypes.DWORD,  # nNumberOfBytesToRead [in]
    LPDWORD,                # lpNumberOfBytesRead [out, optional]
    LPOVERLAPPED,           # lpOverlapped [in, out, optional]
]

# SetNamedPipeHandleState
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa365787%28v=vs.85%29.aspx

SetNamedPipeHandleState = _kernel32.SetNamedPipeHandleState
SetNamedPipeHandleState.restype = ctypes.wintypes.HANDLE
SetNamedPipeHandleState.argtypes = [
    ctypes.wintypes.HANDLE,  # hNamedPipe [in]
    LPDWORD,                # lpMode [in, optional]
    LPDWORD,                # lpMaxCollectionCount [in, optional]
    LPDWORD,                # lpCollectDataTimeout [in, optional]
]

# WaitForSingleObject
# http://msdn.microsoft.com/en-us/library/windows/desktop/ms687032%28v=vs.85%29.aspx

WaitForSingleObject = _kernel32.WaitForSingleObject
WaitForSingleObject.restype = ctypes.wintypes.DWORD
WaitForSingleObject.argtypes = [
    ctypes.wintypes.HANDLE,  # hHandle [in]
    ctypes.wintypes.DWORD,  # dwMilliseconds [in]
]

WAIT_ABANDONED = 0x00000080L
WAIT_OBJECT_0 = 0x00000000L
WAIT_TIMEOUT = 0x00000102L
WAIT_FAILED = 0xFFFFFFFFL

# WriteFile
# http://msdn.microsoft.com/en-us/library/windows/desktop/aa365747%28v=vs.85%29.aspx

WriteFile = _kernel32.WriteFile
WriteFile.restype = ctypes.wintypes.BOOL
WriteFile.argtypes = [
    ctypes.wintypes.HANDLE,  # hFile [in]
    ctypes.wintypes.LPCVOID,  # lpBuffer [in]
    ctypes.wintypes.DWORD,   # nNumberOfBytesToWrite [in]
    LPDWORD,                 # lpNumberOfBytesWritten [out, optional]
    LPOVERLAPPED,            # lpOverlapped [in, out, optional]
]

# Constants: winbase.h
INFINITE = 0xFFFFFFFFL
INVALID_HANDLE_VALUE = ctypes.wintypes.HANDLE(-1).value

# Constants: winerror.h
ERROR_BROKEN_PIPE = 109L
ERROR_MORE_DATA = 234L
ERROR_PIPE_CONNECTED = 535L
ERROR_IO_PENDING = 997L

# Constants: winnt.h
GENERIC_READ = 0x80000000L
GENERIC_WRITE = 0x40000000L
