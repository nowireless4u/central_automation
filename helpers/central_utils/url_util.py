
class UrlObj(object):

    DEVICE = {
        "ADD": "/platform/device_inventory/v1/devices"  
    }
    AP = {
        "GET_ALL": "/monitoring/v2/aps",
        "DETAILS": "/monitoring/v1/aps",
        "DELETE": "/monitoring/v1/apsserial"
    }
    SW = {
        "GET_ALL": "/monitoring/v2/switches",
        "DETAILS": "/monitoring/v1/switches",
        "DELETE": "/monitoring/v1/switches"
    }
    AP_CONFIGURATION = {
        "GET": "/configuration/v1/ap_cli",
        "REPLACE": "/configuration/v1/ap_cli"
    }
    CX_VLAN = {
        "GET": "/configuration/v1/switch/cx/vlans",
        "REPLACE": "/configuration/v1/switch/cx/vlans"
    }
    CX_INT = {
        "GET": "/configuration/v1/switch/cx/interfaces",
        "REPLACE": "/configuration/v1/switch/cx/interfaces"
    }
    CX_LAG = {
        "GET": "/configuration/v1/switch/cx/lags",
        "REPLACE": "/configuration/v1/switch/cx/lags"
    }
    CX_LOOP = {
        "GET": "/configuration/v1/switch/cx/loop-prevention",
        "REPLACE": "/configuration/v1/switch/cx/loop-prevention"
    }
    CX_PROP = {
        "GET": "/configuration/v1/switch/cx/properties",
        "REPLACE": "/configuration/v1/switch/cx/properties"
    }
    CX_SYSLOG = {
        "GET": "/configuration/v1/switch/cx/syslog",
        "REPLACE": "/configuration/v1/switch/cx/syslog"
    }

