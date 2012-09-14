#include <errno.h>
#include <unistd.h>

int main(int argc, int argv) {
    if (setuid(geteuid()) < 0) {
	perror("Unable to set UID");
	exit(EXIT_FAILURE);
    }

    system("launchctl load /Library/LaunchDaemons/com.makerbot.conveyor.plist");

    exit(EXIT_SUCCESS);
}
