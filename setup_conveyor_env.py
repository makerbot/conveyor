import os
import os.path
import platform
import sys
import subprocess

python_version = ".".join(sys.version.split()[0].split(".")[0:2])

req_eggs = [
  'mock-1.0.1',
  'lockfile-0.9.1',
  'argparse-1.2.1',
  'unittest2-0.5.1',
  'python_daemon-1.6',
  'pyserial-2.7_mb2.1',
  'makerbot_driver-0.1.1'
]

req_eggs = [egg + '-py' + python_version + '.egg' for egg in req_eggs]
print req_eggs

opt_eggs = [
  'conveyor-2.0.0'
]

opt_eggs = [egg + '-py' + python_version + '.egg' for egg in opt_eggs]

def find_egg(paths, egg):
  for path in paths:
    egg_in_path = os.path.join(path, egg)
    if os.path.exists(egg_in_path):
      return egg_in_path
  return None

python_exe = sys.executable
env_dir = 'virtualenv'
if '2.6' == python_version:
  env_dir += '26'

search_paths = sys.argv[1:]
  
virtualenv_command = [
  python_exe,
  'virtualenv.py',
  '--never-download'
]

for path in search_paths:
  virtualenv_command.append('--extra-search-dir=' + path)

virtualenv_command.append(env_dir)

try:
  env = os.environ
  if 'darwin' == sys.platform:
    release, version_info, machine = platform.mac_ver()
    subdirectory = os.path.abspath('.'.join(release.split('.')[:2]))
    env['PATH'] = os.pathsep.join(env['PATH'].split(os.pathsep) + [subdirectory])
  subprocess.check_call(virtualenv_command, env=env)
except subprocess.CalledProcessError as e:
  print 'something went wrong calling virtualenv:'
  print e
  print '\nDid you forget to pass the path to the setuptools egg?'
  sys.exit(2)


if 'win32' == sys.platform:
  virtualenv_easy_install = os.path.join(env_dir, 'Scripts', 'easy_install.exe')
else:
  virtualenv_easy_install = os.path.join(env_dir, 'bin', 'easy_install')
e_install = [virtualenv_easy_install, '-q']


missing_required_eggs = False
try:
  for egg in req_eggs:
    egg_found = find_egg(search_paths, egg)
    if egg_found != None:
      subprocess.check_call(e_install + [egg_found])
    else:
      print 'egg ' + egg + ' not found'
      missing_required_eggs = True
except subprocess.CalledProcessError as e:
  print 'something went wrong installing the required eggs'
  sys.exit(4)
  
try:
  for egg in opt_eggs:
    egg_found = find_egg(search_paths, egg)
    if egg_found != None:
      subprocess.check_call(e_install + [egg_found])
    else:
      print 'skipping egg ' + egg
except subprocess.CalledProcessError as e:
  print 'something went wrong installing the optional eggs'
  sys.exit(5)

if missing_required_eggs:
  print 'Some of the required eggs were not found.'
  print '\nDid you forget to pass search paths for those eggs?'
  sys.exit(6)
