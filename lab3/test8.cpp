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

    struct sockaddr_in sin;
    memset(&sin, 0, sizeof(sin)); 
    sin.sin_family = AF_INET; 
    sin.sin_addr.s_addr = INADDR_ANY; 
    sin.sin_port = htons(10000+121); // 바인딩
    if (bind(s, (struct sockaddr *) &sin, sizeof(sin)) < 0) {
        cerr << strerror(errno) << endl;
        return 0;
    }

    cout << "Server listening on port " << sin.sin_port << endl;

    while(true) {
        char buf[65536] = "";
        memset(buf, 0, sizeof(buf));

        socklen_t sin_size = sizeof(sin);

        int numBytes = recvfrom(s, buf, sizeof(buf), 0, (struct sockaddr *) &sin, &sin_size);
        cout << "Received: " << numBytes << endl;
        cout << "From: " << inet_ntoa(sin.sin_addr) << ":" << ntohs(sin.sin_port) << endl;
        cout << "buf:" << buf << endl;

        char buf2[numBytes];
        strcpy(buf2, buf);

        numBytes = sendto(s, buf2, sizeof(buf2), 0, (struct sockaddr *)&sin, sizeof(sin));

        cout << "Sent: " << numBytes << endl; 

        memset(&sin, 0, sizeof(sin));
        sin_size = sizeof(sin);
        int result = getsockname(s, (sockaddr *)&sin, &sin_size);
        if(result == 0) {
            cout << "My addr: " << inet_ntoa(sin.sin_addr) << endl;
            cout << "My port: " << ntohs(sin.sin_port) << endl;
        }
        
    }

    close(s);
    return 0;
}