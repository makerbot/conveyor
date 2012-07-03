
import sys
#override sys.path
sys.path.insert(0,'./src/main/python')
sys.path.insert(0,'./submodule/s3g')

import conveyor
import conveyor.log
import conveyor.client
import conveyor.main


#start logging, fire up ServerMain of the server module
conveyor.log.earlylogging('conveyord')
main = conveyor.client.ClientMain()
code = main.main(sys.argv)

