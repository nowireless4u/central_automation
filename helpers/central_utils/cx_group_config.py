import logging
from pycentral.url_utils import ConfigurationUrl, urlJoin
from pycentral.base_utils import console_logger
from central_utils.url_util import UrlObj

urls = UrlObj()
logger = console_logger("CONFIGURATION")

class CXConfiguration(object):
    """A Python class to manage CX configuration.
    """
    def get_vlan_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_VLAN["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_vlan_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_VLAN["POST"], group_name)
        resp = conn.command(apiMethod="POST", apiPath=path)
        return resp

    def get_int_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_INT["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_int_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_INT["POST"], group_name)
        resp = conn.command(apiMethod="POST", apiPath=path)
        return resp

    def get_lag_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_LAG["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_lag_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_LAG["POST"], group_name)
        resp = conn.command(apiMethod="POST", apiPath=path)
        return resp

    def get_loop_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_LOOP["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_loop_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_LOOP["POST"], group_name)
        resp = conn.command(apiMethod="POST", apiPath=path)
        return resp

    def get_prop_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_PROP["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_prop_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_PROP["POST"], group_name)
        resp = conn.command(apiMethod="POST", apiPath=path)
        return resp

    def get_syslog_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_SYSLOG["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_syslog_configuration(self, conn, group_name: str):

        path = urlJoin(urls.CX_SYSLOG["POST"], group_name)
        resp = conn.command(apiMethod="POST", apiPath=path)
        return resp

    
