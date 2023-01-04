import logging
from pycentral.url_utils import ConfigurationUrl, urlJoin
from pycentral.base_utils import console_logger
from central_utils.url_util import UrlObj

urls = UrlObj()
logger = console_logger("CONFIGURATION")

class APConfiguration(object):
    """A Python class to manage AP configuration.
    """
    def get_ap_configuration(self, conn, group_name: str):
        """Get existing AP settings

        :param conn: Instance of class:`pycentral.ArubaCentralBase` to make an API call.
        :type conn: class:`pycentral.ArubaCentralBase`
        :param serial_number: Serial number of an AP. Example: CNBRHMV3HG
        :type serial_number: str
        :return: Response as provided by 'command' function in class:`pycentral.ArubaCentralBase`.
        :rtype: dict
        """
        path = urlJoin(urls.AP_CONFIGURATION["GET"], group_name)
        resp = conn.command(apiMethod="GET", apiPath=path)
        return resp

    def replace_ap_configuration(self, conn, group_name: str, ap_configuration_data: dict):
        """Update Existing AP Settings

        :param conn: Instance of class:`pycentral.ArubaCentralBase` to make an API call.
        :type conn: class:`pycentral.ArubaCentralBase`
        :param serial_number: Serial number of an AP. Example: CNBRHMV3HG
        :type serial_number: str
        :param ap_settings_data: Data to update ap settings. \n
            * keyword hostname: Name string to set to the AP \n
            * keyword ip_address: IP Address string to set to AP. Should be set to "0.0.0.0" if AP get IP from DHCP. \n
            * keyword zonename: Zonename string to set to AP \n
            * keyword achannel: achannel string to set to AP \n
            * keyword atxpower: atxpower string to set to AP \n
            * keyword gchannel: gchannel string to set to AP \n
            * keyword gtxpower: gtxpower string to set to AP \n
            * keyword dot11a_radio_disable: dot11a_radio_disable string to set to AP \n
            * keyword dot11g_radio_disable: dot11g_radio_disable string to set to AP \n
            * keyword usb_port_disable: usb_port_disable string to set to AP \n
        :type ap_settings_data: dict
        :return: Response as provided by 'command' function in class:`pycentral.ArubaCentralBase`.
        :rtype: dict
        """
        path = urlJoin(urls.AP_CONFIGURATION["REPLACE"], group_name)
        data = ap_configuration_data
        resp = conn.command(apiMethod="POST", apiPath=path, apiData=data)
        return resp