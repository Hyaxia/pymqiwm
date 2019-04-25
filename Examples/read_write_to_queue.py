"""
Most basic interaction with a queue.
Writing a message to the queue, and reading it.

Notice that the handling of the different modes that the queue
is open is abstracted from the user and is handled behind the scenes.
"""

from pymqiwm import WMQueue, WMQueueManager

qmgr = WMQueueManager(
    name="TEST",
    conn_info="localhost(1414)"
)
queue = WMQueue(qmgr=qmgr, name="DAVAY")

with qmgr:
    with queue:
        queue.put("Test message")
        print(queue.get())


