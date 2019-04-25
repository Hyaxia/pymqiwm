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
    """ Wrapper around a function that makes sure that the connection to the qmgr is active """
    @wraps(func)
    def wrapper(self: QueueManager, *args, **kwargs):
        assert self.is_connected, "Has to be connected to the queue manager"
        return func(self, *args, **kwargs)
    return wrapper


class WMQueueManager(object):
    """

        A wrapper class for the pymqi.QueueManager class.
        Usage:
             >>> qmgr = WMQueueManager(...)

            >>> with qmgr:
                ...
                ...

        Because when we want to connect to the queue manager we use the 'safe_connect' function,
        We wont get exceptions when we try to connect to an already connected qmgr.
        That's why you should always use the context manager, which simplifies the flow.

        Example for conn_info: "host_name(port),another_host(other_port)"

    """

    def __init__(self,
                 name: str,
                 conn_info: str,
                 channel=DEFAULT_CHANNEL,
                 user=None,
                 password=None):
        self._name = name
        self._user = user
        self._password = password
        self._cd = self._get_cd(channel, conn_info)
        self.qmgr = QueueManager(None)

    @property
    def qmgr_name(self) -> str:
        return self._name

    @property
    def conn_info(self) -> str:
        return self.conn_info

    @property
    def user(self) -> str:
        return self._user

    @property
    def connection_details(self) -> CD:
        return self._cd

    @property
    def is_connected(self):
        """ Checks if the connection to the qmgr is active """
        return self.qmgr.is_connected

    def __enter__(self):
        """ Initializes the connection to the qmgr """
        self._safe_connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Makes sure that the connection is closed if its active """
        if self.qmgr.is_connected:
            self.qmgr.disconnect()

    def _safe_connect(self):
        """
        A function for connecting safely to the queue manager.
        If the there is already an open connection to the queue manager, the open connection will be used,
        so the developer does'nt have to deal with the check for the connection.
        """
        opts = self._get_connection_options()
        self.qmgr.connect_with_options(self._name,
                                       user=self._user,
                                       password=self._password,
                                       cd=self._cd,
                                       opts=opts)

    def _get_cd(self, channel, conn) -> CD:
        """
        Initializes a ConnectionDetails object.
        Specifies the transport type, channel type, channel name, and connection string.
        :param channel: The name of the channel to use when connecting to the qmgr.
        :param conn: Connection string to the desired qmgr, example of a conn is above.
        :return: CD object.
        """
        cd = CD()
        cd.ChannelName = channel
        cd.ConnectionName = conn
        cd.ChannelType = MQCHT_CLNTCONN
        cd.TransportType = MQXPT_TCP
        return cd

    def _get_connection_options(self):
        return MQCNO_HANDLE_SHARE_BLOCK

    def _get_pcf(self):
        return PCFExecute(self.qmgr)

    @has_to_be_connected
    def display_queues(self, value_for_search) -> [str]:
        """
        :param value_for_search: For example, "SYSTEM.*" will get all the queues with SYSTEM at the start
        :return: list of found queues or an empty one
        """
        args = {
            MQCA_Q_NAME: value_for_search,
            MQIA_Q_TYPE: MQQT_ALL
        }
        pcf = self._get_pcf()
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
    def display_channels(self, value_for_search) -> [str]:
        """
        :param value_for_search: For example, "SYSTEM.*" will get all the channels with SYSTEM at the start
        :return: list of found channels or an empty one
        """
        args = {MQCACH_CHANNEL_NAME: value_for_search}
        pcf = self._get_pcf()
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
    def create_local_queue(self, name, depth=5000):
        """ Creates a local queue with a name and depth provided """
        args = {
            MQCA_Q_NAME: name,
            MQIA_Q_TYPE: MQQT_LOCAL,
            MQIA_MAX_Q_DEPTH: depth,
        }

        pcf = self._get_pcf()
        pcf.MQCMD_CREATE_Q(args)

    @has_to_be_connected
    def delete_queue(self, name, purge=False):
        """ Deletes a queue by its name """
        args = {
            MQCA_Q_NAME: name,
        }

        if purge:
            args[MQIACF_PURGE] = MQPO_YES

        pcf = self._get_pcf()
        pcf.MQCMD_DELETE_Q(args)

    @has_to_be_connected
    def get_stats_from_queue(self, name) -> dict:
        """ Return dict containing different stats about the queue """
        pcf = self._get_pcf()
        args = {
            MQCA_Q_NAME: name
        }

        queue_stats = pcf.MQCMD_RESET_Q_STATS(args)[0]

        return {
            "time since last queue reset": queue_stats[MQIA_TIME_SINCE_RESET],
            "current depth": queue_stats[MQIA_HIGH_Q_DEPTH],
            "messages red recently": queue_stats[MQIA_MSG_DEQ_COUNT],  # recently - since last reset time
            "messages put recently": queue_stats[MQIA_MSG_ENQ_COUNT]   # recently - since last reset time
        }














