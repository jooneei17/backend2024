import datetime
import sys
import threading
import time

sum = 0

def f1():
    global sum
    print('f1 id:', threading.get_ident())
    print('f1 native id:', threading.get_native_id())
    for i in range(10 * 1000 * 1000):
        sum += 1
    time.sleep(10)

def main(argv):
    global sum

    print('main id:', threading.get_ident())
    print('main native id:', threading.get_native_id())

    print('Local time', datetime.datetime.now())
    print('UTC', datetime.datetime.utcnow())

    t = threading.Thread(target=f1)
    t.start()

    print('t id:', t.ident)
    print('t native id:', t.native_id)

    for i in range(10 * 1000 * 1000):
        sum += 1

    t.join()
    print('Sum', sum)