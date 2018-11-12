from functools import wraps
from pymqi import QueueManager, PCFExecute, CD, MQMIError
from pymqiwm.consts import DEFAULT_CHANNEL
from pymqi.CMQC import (
    MQIA_MAX_Q_DEPTH, MQQT_LOCAL, MQIA_MSG_DEQ_COUNT, MQIA_TIME_SINCE_RESET,
    MQIA_HIGH_Q_DEPTH, MQCA_Q_NAME, MQIA_Q_TYPE,
    MQIA_MSG_ENQ_COUNT, MQCHT_CLNTCONN, MQXPT_TCP, MQCNO_HANDLE_SHARE_BLOCK,
    MQQT_ALL, MQRC_UNKNOWN_OBJECT_NAME
)
from pymqi.CMQCFC import MQIACF_PURGE, MQPO_YES, MQCACH_CHANNEL_NAME


def has_to_be_connected(func):
    @wraps(func)
    def wrapper(self: QueueManager, *args, **kwargs):
        assert self.is_connected, "Has to be connected to the queue manager"
        return func(self, *args, **kwargs)
    return wrapper


class WMQueueManager(QueueManager):
    """

        A wrapper class for the pymqi.QueueManager class.
        Usage:
             >>> host = "localhost"
             >>> port = 1414
             >>> qmgr = WMQueueManager(qmgr_name, channel, host, port, user=None, password=None)

            >>> with qmgr:
                ...
                ...

        Because when we want to connect to the queue manager we use the 'safe_connect' function,
        We wont get exceptions when we try to connect to an already connected qmgr.
        That's why you should always use the context manager, which simplifies the flow.

        Example for conn_info: "host_name(port),another_host(other_port)"

    """

    def __init__(self,
                 qmgr_name: str,
                 conn_info: str,
                 channel=DEFAULT_CHANNEL,
                 user=None,
                 password=None):
        super(WMQueueManager, self).__init__(None)
        self.__qmgr_name = qmgr_name
        self.__channel = channel
        self.__user = user
        self.__password = password
        self.__conn_info = conn_info

    @property
    def qmgr_name(self):
        return self.__qmgr_name

    @property
    def conn_info(self):
        return self.conn_info

    @property
    def channel(self):
        return self.__channel

    @property
    def user(self):
        return self.__user

    def __enter__(self):
        self.__safe_connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_connected:
            self.disconnect()

    def __safe_connect(self):
        """
        A function for connecting safely to the queue manager.
        If the there is already an open connection to the queue manager, the open connection will be used,
        so the developer does'nt have to deal with the check for the connection.
        """
        opts = self.__get_connection_options()
        conn_details = self.__get_cd()
        self.connect_with_options(self.__qmgr_name,
                                  user=self.__user,
                                  password=self.__password,
                                  cd=conn_details,
                                  opts=opts)

    def __get_cd(self):
        cd = CD()
        cd.ChannelName = self.__channel
        cd.ConnectionName = self.__conn_info
        cd.ChannelType = MQCHT_CLNTCONN
        cd.TransportType = MQXPT_TCP
        return cd

    def __get_connection_options(self):
        return MQCNO_HANDLE_SHARE_BLOCK

    def __get_pcf(self):
        return PCFExecute(self)

    @has_to_be_connected
    def display_queues(self, value_for_search):
        """
        :param value_for_search: For example, "SYSTEM.*" will get all the queues with SYSTEM at the start
        :return: list of found queues or an empty one
        """
        args = {
            MQCA_Q_NAME: value_for_search,
            MQIA_Q_TYPE: MQQT_ALL
        }
        pcf = self.__get_pcf()
        try:
            response = pcf.MQCMD_INQUIRE_Q(args)
        except MQMIError as e:
            if e.reason == MQRC_UNKNOWN_OBJECT_NAME:
                return []  # No queue found
            else:
                raise  # Exception displaying the queues
        else:
            return [queue_info[MQCA_Q_NAME] for queue_info in response]

    @has_to_be_connected
    def display_channels(self, value_for_search):
        """
        :param value_for_search: For example, "SYSTEM.*" will get all the channels with SYSTEM at the start
        :return: list of found channels or an empty one
        """
        args = {MQCACH_CHANNEL_NAME: value_for_search}
        pcf = self.__get_pcf()
        try:
            response = pcf.MQCMD_INQUIRE_CHANNEL(args)
        except MQMIError as e:
            if e.reason == MQRC_UNKNOWN_OBJECT_NAME:
                return []  # No channels found
            else:
                raise  # Exception displaying channels
        else:
            return [channel_info[MQCACH_CHANNEL_NAME] for channel_info in response]

    @has_to_be_connected
    def create_local_queue(self, queue_name, depth=5000):
        args = {
            MQCA_Q_NAME: queue_name,
            MQIA_Q_TYPE: MQQT_LOCAL,
            MQIA_MAX_Q_DEPTH: depth,
        }

        pcf = self.__get_pcf()
        pcf.MQCMD_CREATE_Q(args)

    @has_to_be_connected
    def delete_queue(self, queue_name, purge=False):
        args = {
            MQCA_Q_NAME: queue_name,
        }

        if purge:
            args[MQIACF_PURGE] = MQPO_YES

        pcf = self.__get_pcf()
        pcf.MQCMD_DELETE_Q(args)

    @has_to_be_connected
    def get_stats_from_queue(self, queue_name):
        """ Return dict containing different stats about the queue """
        pcf = self.__get_pcf()
        args = {
            MQCA_Q_NAME: queue_name
        }

        queue_stats = pcf.MQCMD_RESET_Q_STATS(args)[0]

        return {
            "time since last queue reset": queue_stats[MQIA_TIME_SINCE_RESET],
            "current depth": queue_stats[MQIA_HIGH_Q_DEPTH],
            "messages red recently": queue_stats[MQIA_MSG_DEQ_COUNT],  # recently - since last reset time
            "messages put recently": queue_stats[MQIA_MSG_ENQ_COUNT]   # recently - since last reset time
        }














