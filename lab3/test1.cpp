#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

#include <iostream>

using namespace std;

int main() {
	int s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	// if (s < 0) {
	// 	cerr << "socket() error\n";
	// 	return 1;
	// }
	cout << "Socket ID:" << s << endl;

	close(s); // 리소스 해제
	return 0;
}

