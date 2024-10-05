#include <arpa/inet.h> 
#include <sys/socket.h> 
#include <sys/types.h>
#include <string.h>
#include <unistd.h>

#include <iostream>
#include <string>

using namespace std;

int main() {
    int s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s < 0) return 1; 

    string buf = "Hello World";
    struct sockaddr_in sin; 
    
    memset(&sin, 0, sizeof(sin)); 
    sin.sin_family = AF_INET; 
    sin.sin_port = htons(10001);
    // sin.sin_port = htons(10000+121); 
    sin.sin_addr.s_addr = inet_addr("127.0.0.1"); 

    int numBytes = sendto(s, buf.c_str(), buf.length(), 
        0, (struct sockaddr *) &sin, sizeof(sin));

    cout << "Sent: " << numBytes << endl;

    char buf2[65536];
    memset(&sin, 0, sizeof(sin));
    socklen_t sin_size = sizeof(sin);
    numBytes = recvfrom(s, buf2, sizeof(buf2), 0, 
        (struct sockaddr *) &sin, &sin_size); // 실제 사용한 사이즈 알기 위해 sin_size의 주소를 받아옴
        // 내가 넘겨주는 구조체는 struct sockaddr * 이고, 실제 사용한 사이즈는 몇 바이트인지 sizeof(sin)해서 알려줘!
    cout << "Recevied: " << numBytes << endl;
    cout << "From " << inet_ntoa(sin.sin_addr) << endl;
    
    memset(&sin, 0, sizeof(sin));
    sin_size = sizeof(sin);
    int resut = getsockname(s, (sockaddr *) &sin, &sin_size);
    // sockname(이름) = Ip 주소 + port 번호임. 
    if(resut == 0) { // 정상적 종료시 0
        cout << "My addr: " << inet_ntoa(sin.sin_addr) << endl;
        cout << "My port: " << ntohs(sin.sin_port) << endl; // network to host short
    }

    close(s);
    return 0;
}