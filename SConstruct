#
# Top-level SConstruct file for conveyor.
#

AddOption('--test', action='store_true', dest='test')
run_test = GetOption('test')

env = Environment()

env.Command('virtualenv', 'setup.sh', './setup.sh')

if run_test:
    env.Command('test', 'test.sh', '. virtualenv/bin/activate; ./test.sh')

