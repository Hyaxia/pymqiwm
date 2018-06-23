from logger import Logger
from pymqi import Queue
from pymqi import MQMIError
from pymqi import MD, GMO, CMQC
from pymqi.CMQC import MQIA_CURRENT_Q_DEPTH, MQRC_NO_MSG_AVAILABLE, MQRC_NOT_OPEN_FOR_INPUT, MQRC_NOT_OPEN_FOR_OUTPUT
from pymqiwm.queue_manager import WMQueueManager
from pymqiwm.logging_messages import *


class WMQueue(Queue):
    """

        A wrapper class for the pymqi.Queue class.

        Usage:

            queue = MQueue(qmgr, queue_name)

            with queue:
                ...
                ...
                for message in queue.get_messages_while_waiting():
                    ...
                    #Process the messages from the queue
                    ...

    """

    def __init__(self, qmgr: WMQueueManager, queue_name: str):
        self.queue_descriptor = queue_name
        self.qmgr = qmgr
        self.queue_name = queue_name
        assert qmgr.is_connected, "Queue manager object has to be connected"
        super(WMQueue, self).__init__(qmgr, queue_name)
        Logger.info(QUEUE_CONNECTION_INFO.format(self.queue_name))

    def safe_put(self, msg, *opts):
        """
        A function that lets you perform the 'put' action without worrying about anything.
        If the queue is not open for performing the 'put' action, it will reset the open options accordingly.
        If there will be an error it will log it and raise it.
        :param msg: The body of the message that will be written to the queue
        :param opts: can be specified for further instructions.
        """
        try:
            self.put(msg, *opts)
        except MQMIError as e:
            if e.reason == MQRC_NOT_OPEN_FOR_OUTPUT:
                self.__reset_open_options()
                self.put(msg, *opts)
                return
            Logger.error(PUT_MESSAGE_ERROR.format(self.queue_name, str(e)))
            raise

    def safe_get(self, max_length=None, *opts):
        """
        A function that lets you perform the 'get' action without worrying about anything.
        If the queue is not open for performing the 'get' action, it will reset the open options accordingly.
        If there are no messages to pull from the queue it will only raise the exception.
        If there is another error, it will log it and raise it.
        :param max_length: max can length can be set for the message that is being red
        :param opts: can be specified for further instructions.
        :return:
        """
        try:
            message = self.get(max_length, *opts)
        except MQMIError as e:
            if e.reason == MQRC_NO_MSG_AVAILABLE:
                raise
            elif e.reason == MQRC_NOT_OPEN_FOR_INPUT:
                self.__reset_open_options()
                message = self.get(max_length, *opts)
                return message
            Logger.error(GET_MESSAGE_ERROR.format(self.queue_name, str(e)))
            raise
        else:
            return message

    def safe_open(self, q_desc, *opts):
        """
        A function that lets you perform the 'open' action.
        The function will log any error that rises and raise it.
        :param q_desc: String that contains the name of the queue, or an object descriptor of the queue.
        :param opts: open options.
        """
        try:
            self.open(q_desc, *opts)
        except Exception as e:
            Logger.error(OPEN_QUEUE_ERROR.format(self.queue_name, str(e)))
            raise

    def get_current_depth(self):
        """
        A function that returns the current depth of the queue
        :return:
        """
        try:
            return self.inquire(MQIA_CURRENT_Q_DEPTH)
        except MQMIError as e:
            Logger.error(DEPTH_ERROR.format(self.queue_name))
            raise

    def get_messages_while_waiting(self, seconds_wait_interval=0):
        """
        Yields messages that are being red from the queue.
        It will handle any "No more message on the queue" errors.
        ^It will log any error that raises if its not the one above^
        :param seconds_wait_interval:
                        IF not specified:  Will exit as soon as there are no messages left on queue.
                        IF -1 specified: Will enter into an infinite loop yielding any message that enters the queue.
                        ELSE : Will wait the time specified before exiting the loop.
        """
        self.__reset_open_options()

        keep_running = True

        gmo = self.__get_and_wait_gmo(abs(seconds_wait_interval) * 1000)
        md = self.__get_message_descriptor()

        while keep_running:
            try:
                message = self.safe_get(None, md, gmo)  # Wait up to gmo.WaitInterval for a new message.
                yield message
                self.__reset_md(md)  # Reset the md so we can reuse the same 'md' object again.

            except MQMIError as e:
                if e.reason == CMQC.MQRC_NO_MSG_AVAILABLE:
                    if seconds_wait_interval != -1:
                        keep_running = False
                else:
                    Logger.error(READING_WAITING_ERROR.format(self.queue_name))
                    raise

    def browse_messages(self):
        """
        Lets you browse the messages that are on the queue atm by yielding them.
        Stops after it goes over all of the messages in the queue.
        Logs any errors that rise beside the one above^
        :return:
        """
        self.__reset_open_options(CMQC.MQOO_BROWSE)

        keep_running = True

        gmo = self.__browse_messages_gmo()
        md = self.__get_message_descriptor()

        while keep_running:
            try:
                message = self.safe_get(None, md, gmo)
                yield message
                self.__reset_md(md)
            except MQMIError as e:
                if e.reason == CMQC.MQRC_NO_MSG_AVAILABLE:
                    keep_running = False  # There are no more messages on the queue to browse
                else:
                    Logger.error(BROWSE_MESSAGES_ERROR.format(self.queue_name))
                    raise  # there was an error browsing the queue

    def __get_message_descriptor(self):
        return MD()

    def __reset_md(self, md: MD):
        md.MsgId = CMQC.MQMI_NONE
        md.CorrelId = CMQC.MQCI_NONE
        md.GroupId = CMQC.MQGI_NONE

    def __get_and_wait_gmo(self, wait_interval):
        gmo = GMO()
        gmo.Options = CMQC.MQGMO_WAIT | CMQC.MQGMO_FAIL_IF_QUIESCING
        gmo.WaitInterval = wait_interval  # 5000 = 5 seconds
        return gmo

    def __browse_messages_gmo(self):
        gmo = GMO()
        gmo.Options = CMQC.MQGMO_BROWSE_NEXT
        gmo.WaitInterval = CMQC.MQWI_UNLIMITED
        return gmo

    def __reset_open_options(self, *open_opts):
        try:
            self.close()
        except:
            pass
        self.safe_open(self.queue_name, *open_opts)



