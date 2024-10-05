#include <arpa/inet.h> // inet_addr
#include <sys/socket.h> // sendto, inet_addr
#include <sys/types.h>
#include <string.h> // c string
#include <unistd.h>

#include <iostream>
#include <string> // c++ string

using namespace std;

int main() {
    int s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (s < 0) return 1; // 에러 나는지 확인(0아니면 다 에러)

    string buf = "Hello World";
    
    struct sockaddr_in sin; // 구조체
    memset(&sin, 0, sizeof(sin)); // 구조체 주소에다, 0으로 채워, 구조체 변수 크기만큼
    sin.sin_family = AF_INET; // sock address in의 약자 = sin, internet address family
    sin.sin_port = htons(10000); // 포트 번호 기재할 때 htons 사용
    sin.sin_addr.s_addr = inet_addr("127.0.0.1"); 
    // 문자열을 4byte정수로 만들어야 함. inet_addr이 해줌, && 이미 Network byte order로 리턴해줌. 변환필요X

    int numBytes = sendto(s, buf.c_str(), buf.length(), // 보낼 데이터 포인터, 길이, 옵션(0으로 줌), 누구한테 보내야 하는지
    0, (struct sockaddr *) &sin, sizeof(sin));

    cout << "Sent: " << numBytes << endl;

    close(s);
    return 0;
}