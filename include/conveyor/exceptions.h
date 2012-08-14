#ifndef CONVEYOR_EXCEPTIONS_H
#define CONVEYOR_EXCEPTIONS_H

#include <stdexcept>

namespace conveyor {
	class SocketError : public std::runtime_error {
	public:
		SocketError(const std::string &msg) : std::runtime_error(msg) {}
	};

	class SocketCreateError : public SocketError {
	public:
		SocketCreateError() : SocketError("Unable to create socket") {}
	};

	class HostLookupError : public SocketError {
	public:
		HostLookupError(const std::string &host) 
			: SocketError("Unable to lookup host" + host) {}
	};

	class SocketConnectError : public SocketError {
	public:
		SocketConnectError(const std::string &host, const int)
			: SocketError("Unable to connect to " + host) { };
	};

	class SocketIOError : public SocketError {
	public:
		SocketIOError() : SocketError("IO error on socket") { }
	};

	class SocketWriteError : public SocketIOError {
	public: 
		//TODO: smarter error
		SocketWriteError(int) : SocketIOError() { }
	};

	class SocketReadError : public SocketIOError {
	public: 
		//TODO: smarter error
		SocketReadError(int) : SocketIOError() { }
	};

}

#endif
