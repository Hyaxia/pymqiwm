"""
An example of how to use the qmgr and create a local queue
with the name "TEST" and depth of 111.
"""

from pymqiwm import WMQueueManager

qmgr = WMQueueManager(
    name="TEST",
    conn_info="localhost(1414)"
)

with qmgr:
    qmgr.create_local_queue(name="TEST", depth=111)

