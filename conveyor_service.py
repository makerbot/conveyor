
import sys
#override sys.path
sys.path.insert(0,'./src/main/python')
sys.path.insert(0,'./submodule/s3g')

import conveyor
import conveyor.log
import conveyor.server
import conveyor.main


#start logging, fire up ServerMain of the server module
conveyor.log.earlylogging('conveyord')
main = conveyor.server.ServerMain()
code = main.main(sys.argv)

