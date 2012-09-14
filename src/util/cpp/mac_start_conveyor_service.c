#include <errno.h>
#include <unistd.h>
#include <stdlib.h>

int main(int argc, int argv) {
    if (setuid(geteuid()) < 0) {
	perror("Unable to set UID");
	exit(EXIT_FAILURE);
    }

    int ret = system("launchctl load /Library/LaunchDaemons/com.makerbot.conveyor.plist");

    if (ret < 0) {
	perror("Error in system call");
	exit(EXIT_FAILURE);
    }

    exit(ret);
}
