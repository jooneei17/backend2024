#include <chrono>
#include <iostream>
#include <mutex>
#include <thread>

using namespace std;

int sum = 0;
mutex m;
mutex m2;

void f() {
    for(int i = 0; i < 1000; ++i) {
        // m lock m2 lock -> m2 unlock m unlock 순으로 해야 함
        m.lock();
        m2.lock();
        ++sum;
        m.unlock(); 
        m2.unlock();
    }
}

int main() {
    thread t(f);
    for(int i = 0; i < 1000; ++i) {
        m2.lock();
        m.lock();
        ++sum;
        m2.unlock();
        m.unlock();
    }
    t.join();
    cout << "Sum: " << sum << endl;
}