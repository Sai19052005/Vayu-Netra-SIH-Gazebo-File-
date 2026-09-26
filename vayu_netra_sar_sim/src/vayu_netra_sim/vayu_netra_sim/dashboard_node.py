import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from .ros_support import Base, spin


def handler_for(state, page):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path=='/api/state':
                data=json.dumps(state,allow_nan=False).encode();kind='application/json'
            elif self.path in ('/','/index.html'):
                data=page;kind='text/html; charset=utf-8'
            else:self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type',kind)
            self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
        def log_message(self,*args):pass
    return Handler


class DashboardNode(Base):
    def __init__(self):
        super().__init__('dashboard')
        self.state={'banner':'AUTONOMOUS SAR SIMULATION','mission':{},'flight':{},'map':{},'metrics':{}}
        for topic,key in [('/vayu/mission','mission'),('/vayu/flight','flight'),('/vayu/map','map'),('/vayu/perception_metrics','metrics')]:
            self.listen(topic,lambda x,k=key:self.state.update({k:x,'updated_wall':time.time()}))
        page=(Path(get_package_share_directory('vayu_netra_sim'))/'web/index.html').read_bytes()
        port=self.declare_parameter('dashboard_port',8080).value
        self.server=ThreadingHTTPServer(('127.0.0.1',port),handler_for(self.state,page))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.health_ok=True
        self.get_logger().info(f'Dashboard: http://127.0.0.1:{port} (local only)')

    def destroy_node(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
        return super().destroy_node()


def main():spin(DashboardNode)
