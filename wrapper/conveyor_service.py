
import sys
#override sys.path

import conveyor
import conveyor.log
import conveyor.server
import conveyor.main


#start logging, fire up ServerMain of the server module
conveyor.log.earlylogging('conveyord')
main = conveyor.server.ServerMain()
code = main.main(sys.argv)
exit(code) 
