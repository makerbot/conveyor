# vim:ai:et:ff=unix:fileencoding=utf-8:sw=4:syntax=python:ts=4:
#
# Top-level SConstruct file for conveyor.
#

AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')

env = Environment()

env.Command('virtualenv', 'setup.sh', './setup.sh')

if run_test:
    env.Command('test', 'test.sh', '. virtualenv/bin/activate; ./test.sh')

## For building C++/Qt creation
#SConscript('SConscript', variant_dir='obj', duplicate=1)
