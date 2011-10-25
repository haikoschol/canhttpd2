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

import cherrypy

__author__ = 'Haiko Schol'
__email__ = 'hs@haikoschol.com'
__copyright__ = 'Copyright 2011, Haiko Schol'
__license__ = 'MIT'
__version__ = '0.1.0'


default_config = {
    u'testmode': True,
}


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


class CanBusProxy(object):
    """
    CherryPy class that exposes the CAN-Bus proxy interface.
    """
    def __init__(self, config):
        self.config = config

    @cherrypy.expose
    def index(self):
        """
        Show some information about the running server."
        """
        cfg_list = ['<li>%s: %s</li>' %
                    (k, self.config[k]) for k in self.config.keys()]
        return '''<html>
<title>CAN-Bus Proxy</title>
    <body>
        <h1>CAN-Bus Proxy up and running.</h1>
        <h2>Proxy URL</h2>
        <pre>http://127.0.0.1:8080/proxy?value=0x23</pre>
        <h2>Configuration</h2>
        <ul>
        %s
        </ul>
    </body>
</html>''' % '\n'.join(cfg_list)

    @cherrypy.expose
    def proxy(self, value = None):
        if not value: return ''
        try:
            numvalue = int(value, 0)
        except:
            error = 'Integer value expected.'
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            cherrypy.response.status = '400 %s' % error
            return error

        if not self.config['testmode']:
            # TODO send numvalue to CAN-Bus
            pass

        cherrypy.log('CANHTTPD2 Value <%s> has been sent onto CAN-Bus.' % value)
        return None


def main():
    cfg = load_config('config.json')
    cherrypy.quickstart(CanBusProxy(cfg))


if __name__=='__main__':
    main()
