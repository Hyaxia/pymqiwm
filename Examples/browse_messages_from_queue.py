"""
An example of how to browse messages from a queue.

Browsing message from the queue means that you get a look at them
but they stay in the queue until someone reads them.

The function `browse_messages` is using the generator mechanism,
which means that only a single message at a time is saved in memory,
giving us an efficient way to browsing the messages.
"""

from pymqiwm import WMQueue, WMQueueManager

qmgr = WMQueueManager(
    name="TEST",
    conn_info="localhost(1414)"
)
queue = WMQueue(qmgr=qmgr, name="DAVAY")

with qmgr:
    with queue:
        for msg in queue.browse_messages():
            print(msg)


