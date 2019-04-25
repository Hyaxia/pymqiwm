"""
An example of how to make use of the functions provided by the package to read
message in a more sophisticated way.

In this example we set the `seconds_wait_interval` parameter of `read_messages_while_waiting`
to -1, which means that it will continue to run until we interrupt it.

We create a thread and make it run the function `read_from_queue` while we handle
some other events in the meantime.

The output of the program will be:

>>> b'test1'
>>> b'test2'
>>> 'hey, im just in between'
>>> b'test3'
>>> b'test4'
>>> b'test5'
>>> b'test6'

"""

import time
import threading
from pymqiwm import WMQueue, WMQueueManager

qmgr = WMQueueManager(
    name="TEST",
    conn_info="localhost(1414)"
)

queue = WMQueue(qmgr=qmgr, name="DAVAY")


def read_from_queue():
    with qmgr:
        with queue:
            for msg in queue.read_messages_while_waiting():
                print(msg)
                time.sleep(2)


if __name__ == '__main__':
    with qmgr:
        with queue:
            queue.put("test1")
            queue.put("test2")
            queue.put("test3")
            queue.put("test4")
            queue.put("test5")
            queue.put("test6")

    t = threading.Thread(target=read_from_queue)
    t.start()
    time.sleep(3)
    print("hey, im just in between")

