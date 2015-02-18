# Copyright (c) 2013 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import sys
import threading

from server_protocol import *
from status_server_protocol import *

from twisted.internet import reactor, ssl
from twisted.python import log

from autobahn.twisted.websocket import WebSocketServerFactory, listenWS

DEFAULT_PORT = 9000
DEFAULT_PORT_STATUS = DEFAULT_PORT + 1

class Server:

    def _start_status_server(self, debug):
        """
        not-secure server that is used to report errors (such as invalid certificate) and validate that server exists.

        :param debug: bool
        """
        if debug:
            log.startLogging(sys.stdout)

        ws_port = os.environ.get("TANK_PORT_STATUS", DEFAULT_PORT_STATUS)

        factory = WebSocketServerFactory("ws://localhost:%d" % ws_port, debug=debug, debugCodePaths=debug)

        factory.protocol = StatusServerProtocol
        factory.setProtocolOptions(allowHixie76=True, echoCloseCodeReason=True)
        listener = listenWS(factory)

    def _start_server(self, debug=False, keys_path="resources/keys"):
        """
        Start shotgun web server, listening to websocket connections.

        :param debug: Boolean Show debug output. Will also Start local web server to test client pages.
        """

        ws_port = os.environ.get("TANK_PORT", DEFAULT_PORT)
        keys_path = os.environ.get("TANK_DESKTOP_CERTIFICATE", keys_path)

        # SSL server context: load server key and certificate
        self.context_factory = ssl.DefaultOpenSSLContextFactory(os.path.join(keys_path, "server.key"),
                                                               os.path.join(keys_path, "server.crt"))

        self.factory = WebSocketServerFactory("wss://localhost:%d" % ws_port, debug=debug, debugCodePaths=debug)

        self.factory.protocol = ServerProtocol
        self.factory.setProtocolOptions(allowHixie76=True, echoCloseCodeReason=True)
        self.listener = listenWS(self.factory, self.context_factory)

    def start(self, debug=False, keys_path="resources/keys", start_reactor=False):
        """
        Start shotgun web server, listening to websocket connections.

        :param debug: Boolean Show debug output. Will also Start local web server to test client pages.
        :param start_reactor: Boolean Start threaded reactor
        """
        if debug:
            log.startLogging(sys.stdout)

        self._start_server(debug, keys_path)
        self._start_status_server(debug)

        if start_reactor:
            def start():
                reactor.run(installSignalHandlers=0)

            t = threading.Thread(target=start)
            t.start()