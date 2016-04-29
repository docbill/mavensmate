import sys
import handler
import mm.server.lib.endpoints as endpoints
import mm.server.lib.config as server_config
import mm.config as config
from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
server = None

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

def run():
    server_config.setup_logging()
    server_config.debug('---> Starting MavensMate UI server')
    sys.path.insert(0, config.base_path)
    handler.Handler.mappings = endpoints.mappings
    HOST, PORT = "localhost", config.connection.get_plugin_client_setting('mm_server_port', 77777)
    server = ThreadedHTTPServer((HOST, PORT), handler.Handler)
    ip, port = server.server_address
    print "Server running on port: "+str(port)
    server_config.debug("MavensMate UI server running on port: "+str(port))
    server.serve_forever()
    
def stop():
    server_config.debug('shutting down local MavensMate server')
    server.shutdown()
    #os.system("kill -9 `fuser -n tcp 9000`")
