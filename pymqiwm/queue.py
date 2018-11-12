from contextlib import suppress
from pymqi import Queue
from pymqi import MQMIError
from pymqi import MD, GMO
from pymqi.CMQC import (MQIA_CURRENT_Q_DEPTH, MQRC_NO_MSG_AVAILABLE,
                        MQRC_NOT_OPEN_FOR_INPUT, MQRC_NOT_OPEN_FOR_OUTPUT,
                        MQMI_NONE, MQGMO_WAIT, MQGMO_FAIL_IF_QUIESCING,
                        MQGMO_BROWSE_NEXT, MQWI_UNLIMITED, MQGI_NONE,
                        MQCI_NONE, MQOO_BROWSE)


class WMQueue(object):
    """

        A wrapper class for the pymqi.Queue class.

        Usage:

             >>> queue = WMQueue(qmgr=..., queue_name=...)

             >>> with queue:
             >>>     ...

    """

    def __init__(self, qmgr, queue_name: str):
        self.name = queue_name
        self.qmgr = qmgr
        self.queue = Queue(qmgr, queue_name)

    def __enter__(self):
        assert self.qmgr.is_connected, "Has to be connected to the queue manager"
        self.queue.open(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.queue.close()

    """
    For the following operators, the usage is:
         >>> queue = WMQueue(qmgr=..., queue_name=...)
         >>> with queue:
         >>>    if queue > 50:
         >>>        print("depth is higher than 50")
    The example above is specific for the greater than operator
    """

    def __eq__(self, other):
        return self.depth() == other

    def __ne__(self, other):
        return self.depth() != other

    def __gt__(self, other):
        return self.depth() > other

    def __lt__(self, other):
        return self.depth() < other

    def __ge__(self, other):
        return self.depth() >= other

    def __le__(self, other):
        return self.depth() <= other

    def put(self, msg, *opts):
        """
        A function that lets you perform the 'put' action without worrying about anything.
        If the queue is not open for performing the 'put' action, it will reset the open options accordingly.
        Usage:
         >>> queue = WMQueue(qmgr=..., queue_name=...)
         >>> with queue:
         >>>     queue.put(msg="Test")
        :param msg: The body of the message that will be written to the queue
        :param opts: can be specified for further instructions.
        :type msg: str
        """
        try:
            self.queue.put(msg, *opts)
        except MQMIError as e:
            if e.reason == MQRC_NOT_OPEN_FOR_OUTPUT:
                self.__reset_open_options()
                self.queue.put(msg, *opts)
                return
            raise

    def get(self, max_length=None, *opts):
        """
        A function that lets you perform the 'get' action without worrying about anything.
        If the queue is not open for performing the 'get' action, it will reset the open options accordingly.
        If there are no messages to pull from the queue it will only raise the exception.
        Usage:
         >>> queue = WMQueue(qmgr=..., queue_name=...)
         >>> with queue:
         >>>     message = queue.get()
        :param max_length: max can length can be set for the message that is being red
        :param opts: can be specified for further instructions.
        :type max_length: int or None
        :return: Option 1: A message from the queue
                 Option 2: None meaning that there are no more messages in the queue
        """
        try:
            message = self.queue.get(max_length, *opts)
        except MQMIError as e:
            if e.reason == MQRC_NO_MSG_AVAILABLE:
                return  # no message was found in the queue
            elif e.reason == MQRC_NOT_OPEN_FOR_INPUT:  # if queue was not open for reading
                self.__reset_open_options()
                return self.queue.get(max_length, *opts)
            raise
        else:
            return message

    def depth(self):
        return self.queue.inquire(MQIA_CURRENT_Q_DEPTH)

    def read_messages_while_waiting(self, seconds_wait_interval=0, max_length=None):
        """
        Yields messages that are being red from the queue.
        Handles any "No more message on the queue" errors.
        Usage:
         >>> queue = WMQueue(qmgr=..., queue_name=...)
         >>> with queue:
         >>>     for message in queue.read_messages_while_waiting(5):
         >>>         # will wait 5 seconds before exiting the for loop
         >>>         print(str(message))
        :param max_length: max length of a message that will be red from the queue
        :param seconds_wait_interval:
                        IF not specified:  Will exit as soon as there are no messages left on queue.
                        IF -1 specified: Will enter into an infinite loop yielding any message that enters the queue.
                        ELSE : Will wait the time specified before exiting the loop.
        :type seconds_wait_interval: int
        :type max_length: int
        """
        keep_running = True

        gmo = self.__get_and_wait_gmo(abs(seconds_wait_interval) * 1000)
        md = self.__get_message_descriptor()

        while keep_running:
            try:
                message = self.get(max_length, md, gmo)  # Wait up to gmo.WaitInterval for a new message.
                yield message
                self.__reset_md(md)  # Reset the md so we can reuse the same 'md' object again.

            except MQMIError as e:
                if e.reason == MQRC_NO_MSG_AVAILABLE:  # if no msg available in queue
                    if seconds_wait_interval != -1:
                        keep_running = False
                else:
                    raise

    def browse_messages(self, max_length=None):
        """
        Lets you browse the messages that are on the queue atm by yielding them.
        Stops after it goes over all of the messages in the queue.
        Browsing a message does not mean the message will be red form the queue.
        Usage:
         >>> queue = WMQueue(qmgr=..., queue_name=...)
         >>> with queue:
         >>>     for message in queue.browse_messages():
         >>>         print(str(message))
        :param max_length: Max length of message located on the queue that will be red
        :type max_length: int
        :return:
        """
        self.__reset_open_options(MQOO_BROWSE)

        keep_running = True

        gmo = self.__browse_messages_gmo()
        md = self.__get_message_descriptor()

        while keep_running:
            try:
                message = self.get(max_length, md, gmo)
                yield message
                self.__reset_md(md)
            except MQMIError as e:
                if e.reason == MQRC_NO_MSG_AVAILABLE:
                    keep_running = False  # There are no more messages on the queue to browse
                else:
                    raise  # there was an error browsing the queue

    def __get_message_descriptor(self):
        return MD()

    def __reset_md(self, md: MD):
        md.MsgId = MQMI_NONE
        md.CorrelId = MQCI_NONE
        md.GroupId = MQGI_NONE

    def __get_and_wait_gmo(self, wait_interval):
        gmo = GMO()
        gmo.Options = MQGMO_WAIT | MQGMO_FAIL_IF_QUIESCING
        gmo.WaitInterval = wait_interval  # 5000 = 5 seconds
        return gmo

    def __browse_messages_gmo(self):
        gmo = GMO()
        gmo.Options = MQGMO_BROWSE_NEXT
        gmo.WaitInterval = MQWI_UNLIMITED
        return gmo

    def __reset_open_options(self, *open_opts):
        with suppress(Exception):
            self.queue.close()
        self.queue.open(self.name, *open_opts)
