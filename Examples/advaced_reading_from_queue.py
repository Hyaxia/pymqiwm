"""
An example of how to read message from a queue in a more advanced way
provided by the wrapper.

The function `read_messages_while_waiting` has a special parameter called
`seconds_wait_interval`.

When specified, depending on its value, will make the reading function to act in different ways.
"""

from pymqiwm import WMQueue, WMQueueManager

qmgr = WMQueueManager(
    name="TEST",
    conn_info="localhost(1414)"
)
queue = WMQueue(qmgr=qmgr, name="DAVAY")

"""
In this case, we don't specify the `seconds_wait_interval` parameter,
so the reading will be performed until the queue has no more messages in it,
or when the code exits the `for` loop for a different reason.
"""

with qmgr:
    with queue:
        for msg in queue.read_messages_while_waiting():
            print(msg)


"""
In this case, `seconds_wait_interval` is set to 5, which means that the function
will wait 5 seconds from the time it started to read from the queue until a new message arrives.
If no message arrives in the time set, in this case, 5 seconds, the for loop will exit.
"""

with qmgr:
    with queue:
        for msg in queue.read_messages_while_waiting(seconds_wait_interval=5):
            print(msg)


"""
In this case, `seconds_wait_interval` is set to -1, which means that the function will never stop
waiting for new messages to arrive to the queue, which means that unless there is another condition
to exit the for loop, it will run forever.
"""

with qmgr:
    with queue:
        for msg in queue.read_messages_while_waiting(seconds_wait_interval=-1):
            print(msg)

