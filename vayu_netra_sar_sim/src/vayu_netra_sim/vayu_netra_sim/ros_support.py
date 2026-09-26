import json
import time
import rclpy
from rclpy.node import Node
from rclpy.clock import Clock, ClockType
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from .configuration import load


def topic(name, cls, direction='out'):
    version = getattr(cls, 'MESSAGE_VERSION', 0)
    return f'/fmu/{direction}/{name}'+(f'_v{version}' if version else '')


class Base(Node):
    def __init__(self, name):
        super().__init__(name)
        self.cfg = load(self.declare_parameter('config_path', '').value)
        self.output_dir = self.declare_parameter('output_dir', 'runs/current').value
        self.pub_cache = {}
        self.health_ok = False
        self.create_timer(.5, self.health, clock=Clock(clock_type=ClockType.STEADY_TIME))

    def now_s(self): return self.get_clock().now().nanoseconds/1e9

    def send(self, name, value):
        if name not in self.pub_cache:
            self.pub_cache[name] = self.create_publisher(String, name, 20)
        self.pub_cache[name].publish(String(data=json.dumps(value, allow_nan=False)))

    def listen(self, name, callback):
        def receive(msg):
            try: callback(json.loads(msg.data))
            except (ValueError, KeyError, TypeError) as exc:
                self.get_logger().error(f'Rejected {name}: {exc}')
        return self.create_subscription(String, name, receive, 20)

    def health(self):
        self.send('/vayu/health',dict(node=self.get_name(),ok=self.health_ok,timestamp=self.now_s()))


def spin(factory):
    rclpy.init()
    node = None
    try:
        node = factory()
        rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally:
        if node is not None: node.destroy_node()
        if rclpy.ok(): rclpy.shutdown()
