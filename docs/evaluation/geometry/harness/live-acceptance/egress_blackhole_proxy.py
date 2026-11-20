"""Egress recorder for the local-only live acceptance run.

Listens on 127.0.0.1:<port>, is set as HTTP(S)_PROXY/ALL_PROXY for the backend process (NO_PROXY=loopback), records
every request line / CONNECT target as one JSON line, and refuses it (403). An empty log after the run means no
proxy-respecting client in the backend tried to leave the host; raw-socket egress is covered separately by sampling
the process TCP table (see the run report).

usage: python egress_blackhole_proxy.py <port> <log.jsonl>
"""

import json
import socketserver
import sys
import time


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline(4096).decode("latin-1", "replace").strip()
        if not line:
            return
        with open(sys.argv[2], "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.time(), "peer": self.client_address[0], "request": line}) + "\n")
        self.wfile.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")


if __name__ == "__main__":
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", int(sys.argv[1])), Handler) as srv:
        srv.serve_forever()
