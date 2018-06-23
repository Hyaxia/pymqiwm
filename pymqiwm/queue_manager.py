from typing import List
from functools import wraps
from logger import Logger
from pymqi import MQMIError, CMQC, CMQCFC
from pymqi import QueueManager, PCFExecute, CD
from pymqiwm.consts import DEFAULT_CHANNEL
from pymqi.CMQC import MQCA_Q_NAME, MQIA_MAX_Q_DEPTH, MQIA_Q_TYPE, MQQT_LOCAL, MQIA_MSG_DEQ_COUNT, \
    MQIA_TIME_SINCE_RESET, MQIA_HIGH_Q_DEPTH, MQIA_MSG_ENQ_COUNT
from pymqi.CMQCFC import MQIACF_PURGE, MQPO_YES
from pymqiwm.logging_messages import *


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

            qmgr = MQueueManager(qmgr_name, channel, host, port, user, password)

            with qmgr:
                ...
                ...

        Because when we want to connect to the queue manager we use the 'safe_connect' function,
        We wont get exceptions when we try to connect to an already connected qmgr.
        That's why you should always use the context manager, which simplifies the flow.

    """

    def __init__(self, qmgr_name: str, conn_info: str, channel=DEFAULT_CHANNEL, user=None, password=None):
        super(WMQueueManager, self).__init__(None)
        self.qmgr_name = qmgr_name
        self.channel = channel
        self.user = user
        self.password = password
        self.conn_info = conn_info

    def __get_cd(self) -> CD:
        cd = CD()
        cd.ChannelName = self.channel
        cd.ConnectionName = self.conn_info
        cd.ChannelType = CMQC.MQCHT_CLNTCONN
        cd.TransportType = CMQC.MQXPT_TCP
        return cd

    def safe_connect(self):
        try:
            opts = self.__get_connection_options()
            self.connect_with_options(self.qmgr_name, cd=self.__get_cd(), user=self.user,
                                      password=self.password, opts=opts)
            Logger.info(QMGR_CONNECTION_INFO.format(self.qmgr_name))
        except MQMIError as e:
            if e.reason == CMQC.MQRC_HOST_NOT_AVAILABLE:
                Logger.error(QMGR_CONNECTION_ERROR.format(self.qmgr_name, self.conn_info, str(e)))
                raise (QMGR_CONNECTION_ERROR.format(self.qmgr_name, self.conn_info, str(e)))

    def __get_connection_options(self):
        return CMQC.MQCNO_HANDLE_SHARE_BLOCK

    def __get_pcf(self):
        return PCFExecute(self)

    def __enter__(self):
        self.safe_connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_connected:
            self.disconnect()

    @has_to_be_connected
    def display_queues(self, value_for_search) -> List[str]:
        """
        :param value_for_search: For example, "SYSTEM.*" will get all the queues with SYSTEM at the start
        :return: list of found queues or an empty one
        """
        args = {
            CMQC.MQCA_Q_NAME: value_for_search,
            CMQC.MQIA_Q_TYPE: CMQC.MQQT_ALL
        }
        pcf = self.__get_pcf()
        try:
            response = pcf.MQCMD_INQUIRE_Q(args)
        except MQMIError as e:
            if e.reason == CMQC.MQRC_UNKNOWN_OBJECT_NAME:
                Logger.info(NO_QUEUES_FOUND_INFO)
                return []
            else:
                Logger.error(DISPLAY_QUEUE_ERROR.format(self.qmgr_name))
                raise
        else:
            for queue_info in response:
                queue_name = queue_info[CMQC.MQCA_Q_NAME]
                Logger.info(QUEUE_FOUND_INFO.format(queue_name))
            return [queue_info[CMQC.MQCA_Q_NAME] for queue_info in response]

    @has_to_be_connected
    def display_channels(self, value_for_search):
        """
        :param value_for_search: For example, "SYSTEM.*" will get all the channels with SYSTEM at the start
        :return: list of found channels or an empty one
        """
        args = {CMQCFC.MQCACH_CHANNEL_NAME: value_for_search}
        pcf = self.__get_pcf()
        try:
            response = pcf.MQCMD_INQUIRE_CHANNEL(args)
        except MQMIError as e:
            if e.reason == CMQC.MQRC_UNKNOWN_OBJECT_NAME:
                Logger.info(NO_CHANNELS_FOUND_INFO.format(value_for_search))
                return []
            else:
                Logger.info(CHANNEL_DISPLAY_ERROR.format(self.qmgr_name))
                raise
        else:
            for channel_info in response:
                channel_name = channel_info[CMQCFC.MQCACH_CHANNEL_NAME]
                Logger.info(CHANNEL_FOUND_INFO.format(channel_name))
            return [channel_info[CMQCFC.MQCACH_CHANNEL_NAME] for channel_info in response]

    @has_to_be_connected
    def create_local_queue(self, queue_name, depth=5000):
        try:
            args = {
                MQCA_Q_NAME: queue_name,
                MQIA_Q_TYPE: MQQT_LOCAL,
                MQIA_MAX_Q_DEPTH: depth,
            }

            pcf = self.__get_pcf()
            pcf.MQCMD_CREATE_Q(args)
            Logger.info(CREATED_QUEUE_INFO.format(queue_name, self.qmgr_name))
        except MQMIError as e:
            Logger.error(CREATE_QUEUE_ERROR.format(queue_name, self.qmgr_name, str(e)))
            raise

    @has_to_be_connected
    def delete_queue(self, queue_name, purge=False):
        try:
            args = {
                MQCA_Q_NAME: queue_name,
            }

            if purge:
                args[MQIACF_PURGE] = MQPO_YES

            pcf = self.__get_pcf()
            pcf.MQCMD_DELETE_Q(args)
            Logger.info(DELETED_QUEUE_INFO.format(queue_name, self.qmgr_name))
        except MQMIError as e:
            Logger.error(DELETE_QUEUE_ERROR.format(queue_name, self.qmgr_name, str(e)))
            raise

    @has_to_be_connected
    def get_stats_from_queue(self, queue_name):
        try:
            pcf = self.__get_pcf()
            args = {
                MQCA_Q_NAME: queue_name
            }

            queue_stats = pcf.MQCMD_RESET_Q_STATS(args)[0]

            Logger.info(QUEUE_RESET_INFO.format(queue_name))

            return {
                "time since last queue reset": queue_stats[MQIA_TIME_SINCE_RESET],
                "current depth": queue_stats[MQIA_HIGH_Q_DEPTH],
                "messages red since last queue reset": queue_stats[MQIA_MSG_DEQ_COUNT],
                "messages put since last queue reset": queue_stats[MQIA_MSG_ENQ_COUNT]
            }
        except MQMIError as e:
            Logger.error(QUEUE_RESET_ERROR.format(queue_name, self.qmgr_name, str(e)))
            raise














