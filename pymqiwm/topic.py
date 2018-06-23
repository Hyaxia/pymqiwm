from pymqi import Topic


class WMTopic(object):
    def __init__(self, queue_manager, topic_name=None, topic_string=None, topic_desc=None, open_opts=None):
        super(WMTopic, self).__init__(queue_manager, topic_name, topic_string, topic_desc, open_opts)
        self.topic_name = topic_name
        self.qmgr = queue_manager
        self.topic_string = topic_string
        self.topic_desc = topic_desc
        self.open_opts = open_opts

    def publish(self, msg):
        pass

"""
NOT FINISHED YET
"""

