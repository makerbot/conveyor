# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:

import os.path

env = Environment()

if 'QTDIR' not in env:
    moc = env.WhereIs('moc-qt4') or env.WhereIs('moc4') or env.WhereIs('moc')
    if moc:
        env['QTDIR'] = os.path.dirname(os.path.dirname(moc))

env.Tool('qt4', toolpath=[Dir('#/src/main/scons/')])
env.EnableQt4Modules(['QtCore', 'QtTest'])
env.Append(CCFLAGS='-g')
env.Append(CCFLAGS='-pedantic')
env.Append(CCFLAGS='-Wall')
env.Append(CCFLAGS='-Wextra')
env.Append(CCFLAGS='-Wno-variadic-macros')
env.Append(CCFLAGS='-Wno-long-long')
env.Append(CCFLAGS='-Werror') # I <3 -Werror. It is my favorite -W flag.

cppenv = env.Clone()
cppenv.Append(CPPPATH=Dir('#/obj/src/main/cpp/'))
libconveyor = cppenv.Library('jsonrpc', Glob('#/obj/src/main/cpp/*.cpp'))

'''
testenv = cppenv.Clone()
testenv.AlwaysBuild('check')
testenv.Append(LIBS=libjsonrpc)
for node in Glob('#/obj/src/test/cpp/test-*.cpp'):
    root, ext = os.path.splitext(os.path.basename(node.abspath))
    test = testenv.Program(root, [node])
    alias = testenv.Alias('check', [test], test[0].abspath)
    testenv.AlwaysBuild(alias)
'''
