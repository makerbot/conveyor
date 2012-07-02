
import sys
import conveyor
import conveyor.log
import conveyor.server
import conveyor.main

#override sys.path
sys.path.append('src/main/python')
sys.path.append('submodule/s3g')

#start logging, fire up ServerMain of the server module
conveyor.log.earlylogging('conveyord')
main = conveyor.server.ServerMain()
code = main.main(sys.argv)

