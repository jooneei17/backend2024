#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

#include <iostream>

using namespace std;

int main() {
	int s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
	cout << "Socket ID:" << s << endl;
	close(s); 

    // close 한걸 재사용. 같은 값이 나올 수 있음. (값 같다고 같은 소켓X)
    s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    cout << "Socket ID:" << s << endl;
    close(s);

	return 0;
}

