#include <conveyor/exceptions.h>

namespace conveyor {

#ifdef WIN32
#include <winsock2.h>

	SocketError::SocketError(const std::string &msg)
		: std::runtime_error(msg) {
		m_errno = WSAGetLastError();
	}

#else
#include <errno.h>

	SocketError::SocketError(const std::string &msg)
		: std::runtime_error(msg) {
		m_errno = errno;
	}

#endif
}
