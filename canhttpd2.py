#!/usr/bin/env python
# # -*- coding: utf-8 -*-

"""
canhttpd2 is a proxy that forwards data received via HTTP to CAN-Bus.
The HTTP side uses CherryPy and the CAN-Bus side uses a USB adapter
by PEAK-System Technik GmbH.
"""

import os.path
try:
    import simplejson as json
except ImportError:
    import json
import sys

import cherrypy

import PCANBasic as pcan

__author__ = 'Haiko Schol'
__email__ = 'hs@haikoschol.com'
__copyright__ = 'Copyright 2011, Haiko Schol'
__license__ = 'MIT'
__version__ = '0.1.0'


default_config = {
    'canbus_channel': 1,
    'canbus_baudrate': '250K',
    'canbus_mode': 'extended',
    'canbus_id': '0x41414141'
}


class InvalidConfigurationException(Exception):
    pass


def load_config(filename):
    """
    Return a dict containing configuration data.

    filename - name of the config file to load

    Try to load and parse a file with the given name.
    If the file doesn't exist, write one with default values.
    If the file exists and parsing fails, throw exception.
    """
    if not os.path.exists(filename):
        with file(filename, 'w') as cfgfile:
            json.dump(default_config, cfgfile, indent = 2)
        return default_config

    with file(filename, 'r+') as cfgfile:
        cfg = json.load(cfgfile)
        dirty = False

        for key in default_config.keys():
            if key not in cfg:
                cfg[key] = default_config[key]
                dirty = True

        if dirty:
            cfgfile.seek(0)
            json.dump(cfg, cfgfile)

    return cfg


def get_channel(channel):
    """
    Convert a number to a PCANBasic constant for selecting a CAN-Bus channel.

    channel - int, or string containing an int
    """
    channel = int(channel)
    channel_range = range(1, 9)

    if channel not in channel_range:
        raise InvalidConfigurationException(
            '%s is not a valid CAN-Bus channel. Legal values are: %s'
            % (channel, channel_range))

    return getattr(pcan, 'PCAN_USBBUS%s' % channel)


def get_baudrate(baudrate):
    """
    Convert a number to a PCANBasic constant for selecting the baud rate.

    baudrate - string containing a legal baud rate value (e.g. '800K').
    """
    if isinstance(baudrate, unicode):
        baudrate = baudrate.encode('utf-8')
    baudrate = baudrate.upper()

    legal_values = ['1M', '800K', '500K', '250K', '125K', '100K', '95K', '83K',
                    '50K', '47K', '33K', '20K', '10K', '5K']

    if baudrate not in legal_values:
        raise InvalidConfigurationException(
            'CANHTTPD2 <%s> is not a legal baud rate value. Legal values are: %s'
            % (baudrate, str(legal_values)))

    return getattr(pcan, 'PCAN_BAUD_%s' % baudrate)


def get_mode(mode):
    """
    Return a PCANBasic constant that denotes standard or extended mode.
    """
    if isinstance(mode, unicode):
        mode = mode.encode('utf-8')
    mode = mode.upper()

    if mode == 'STANDARD': return pcan.PCAN_MODE_STANDARD
    elif mode == 'EXTENDED': return pcan.PCAN_MODE_EXTENDED
    else:
        raise InvalidConfigurationException(
            '<%s> is not a valid mode name. Legal values are: standard, extended'
            % mode)

    
class TestModeCanBus(object):
    """
    Dummy class for simulating CAN-Bus access in test mode.
    """
    def Initialize(self, *args, **kwargs):
        cherrypy.log('CANHTTPD2 TestModeCanBus.Initialize()')
        return pcan.PCAN_ERROR_OK

    def Uninitialize(self, *args, **kwargs):
        cherrypy.log('CANHTTPD2 TestModeCanBus.Uninitialize()')

    def Write(self,  *args, **kwargs):
        cherrypy.log('CANHTTPD2 TestModeCanBus.Write()')
        return pcan.PCAN_ERROR_OK


def make_canbus(cfg, testmode):
    """
    Factory function for creating an object that provides access to the CAN-Bus.

    cfg - configuration, such as CAN-Bus channel and identifier
    testmode - if True, return a dummy object, that doesn't really send data
    to the CAN-Bus
    """
    if testmode:
        canbus = TestModeCanBus()
    else:
        canbus = pcan.PCANBasic()

    try:
        canbus.canbus_id = int(cfg['canbus_id'], 16)
    except ValueError:
        raise InvalidConfigurationException(
            '<%s> is not a valid CAN-Bus ID. Hex number expected.'
            % cfg['canbus_id'])
    
    canbus.canbus_channel = get_channel(cfg['canbus_channel'])
    canbus.canbus_baudrate = get_baudrate(cfg['canbus_baudrate'])
    canbus.canbus_mode = get_mode(cfg['canbus_mode'])

    res = canbus.Initialize(canbus.canbus_channel,
                            canbus.canbus_baudrate,
                            IOPort=canbus.canbus_mode)

    if res != pcan.PCAN_ERROR_OK:
        cherrypy.log('CAN-Bus initialization FAILED! Error: %s' % str(res))
        cherrypy.engine.exit()
    return canbus


class CanBusProxy(object):
    """
    CherryPy class that exposes the CAN-Bus proxy interface.
    """
    def __init__(self, load_config, testmode = False):
        """
        Make a CanBusProxy instance.

        load_config - callable to load configuration data
        testmode - if you, don't really send data onto the CAN-Bus
        """
        self.load_config = load_config
        self.testmode = testmode
        self.canbus = None
        cherrypy.engine.subscribe('start', self.on_start)
        cherrypy.engine.subscribe('stop', self.on_stop)

    def on_start(self):
        """
        Do initialization on CherryPy engine startup.
        """
        self.config = self.load_config()
        self.canbus = make_canbus(self.config, self.testmode)

    def on_stop(self):
        """
        Do cleanup on CherryPy engine shutdown/restart.
        """
        if self.canbus:
            self.canbus.Uninitialize(self.canbus.canbus_channel)
    
    @cherrypy.expose
    def index(self):
        """
        Show some information about the running server."
        """
        cfg_list = ['<li>%s: %s</li>' %
                    (k, self.config[k]) for k in sorted(self.config.keys())]
        return '''<html>
<title>CAN-Bus Proxy</title>
    <body>
        <h1>CAN-Bus Proxy up and running.</h1>
        <h2>Proxy URL</h2>
        <a href="http://127.0.0.1:8080/proxy?value=0x23">
        http://127.0.0.1:8080/proxy?value=0x23
        </a>
        <h2>Configuration</h2>
        <ul>
        %s
        </ul>
    </body>
</html>''' % '\n'.join(cfg_list)

    @cherrypy.expose
    def crossdomain_xml(self):
        """
        Return an 'anything goes' crossdomain.xml.
        """
        cherrypy.response.headers['Content-Type'] = 'application/xml'
        return '''<?xml version="1.0"?>
<cross-domain-policy>
        <allow-access-from domain="*" />
        <allow-access-from domain="*.macromedia.com" secure="false" />
        <allow-access-from domain="*.adobe.com" secure="false" />
</cross-domain-policy>'''

    @cherrypy.expose
    def proxy(self, value = None):
        if not value: return None
        try:
            numvalue = int(value, 0)
        except ValueError:
            error = 'Integer value expected.'
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            cherrypy.response.status = '400 %s' % error
            return error

        errmsg = 'CANHTTPD2 Sending value <%s> to CAN-Bus FAILED! Error: %s'
        try:
            msg = pcan.TPCANMsg()
            msg.ID = self.canbus.canbus_id
            msg.LEN = 8
            msg.MSGTYPE = self.canbus.canbus_mode
            msg.DATA[0] = numvalue
            
            res = self.canbus.Write(self.canbus.canbus_channel, msg)

            if res != pcan.PCAN_ERROR_OK:
                cherrypy.log(errmsg % (value, str(res)))
            else:
                cherrypy.log('CANHTTPD2 Value <%s> has been sent onto CAN-Bus.'
                             % value)
        except Exception, e:
            cherrypy.log(errmsg % (value, str(e)))
        return None


def main(cfgfilename, args):
    cherrypy.config.update({'server.socket_host': '127.0.0.1'})
    tm = False
    if '-test' in args:
        tm = True

    canbus_proxy = CanBusProxy(lambda: load_config(cfgfilename), testmode=tm)
    cherrypy.quickstart(canbus_proxy)


if __name__=='__main__':
    main('config.json', sys.argv)
