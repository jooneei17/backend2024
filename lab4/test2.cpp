#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <iostream>

#include <errno.h>
#include <string.h>

using namespace std;

int main() {

    for(int i = 0; i < 1024; ++i) {
        int s = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if(s < 0) {
            cerr << "socket() failed: " << i << " " << strerror(errno) << endl;
            break;
        }
    }
  
    return 0;

}