"""ROS graph exercise with fabricated kinematics and blank RGB. Never launches PX4."""
import math
from rclpy.clock import Clock,ClockType
from rosgraph_msgs.msg import Clock as ClockMessage
from sensor_msgs.msg import Image
from .ros_support import Base,spin,qos_profile_sensor_data


class Fixture(Base):
    def __init__(self):
        super().__init__('test_fixture')
        self.t=0.;self.control={};self.pos=[0.,0.,.25];self.armed=False;self.offboard=False
        self.clock_pub=self.create_publisher(ClockMessage,'/clock',10)
        self.image_pub=self.create_publisher(Image,'/vayu/camera/image',qos_profile_sensor_data)
        self.listen('/vayu/control',lambda c:setattr(self,'control',c))
        self.create_timer(.1,self.tick,clock=Clock(clock_type=ClockType.STEADY_TIME));self.health_ok=True

    def tick(self):
        self.t+=.1;c=ClockMessage();c.clock.sec=int(self.t);c.clock.nanosec=int((self.t-int(self.t))*1e9);self.clock_pub.publish(c)
        before=list(self.pos);action=self.control.get('command')
        if action=='OFFBOARD':self.offboard=True
        if action=='ARM':self.armed=True
        if action=='LAND':
            self.pos[2]=max(.25,self.pos[2]-.08)
            if self.pos[2]<=.25:self.armed=False
        elif self.armed and self.control.get('goal'):
            goal=self.control['goal'];length=math.dist(goal,self.pos);scale=min(1,self.cfg['mission']['search_speed']*.1/max(length,1e-6));self.pos=[p+(g-p)*scale for p,g in zip(self.pos,goal)]
        self.send('/vayu/flight',dict(timestamp=self.t,position=self.pos,valid=True,fresh=True,armed=self.armed,offboard=self.offboard,landed=not self.armed and self.pos[2]<=.25,speed=math.dist(self.pos,before)/.1,battery=None,yaw=0.,quaternion=[.70710678,0.,0.,.70710678],source='KINEMATIC_SOFTWARE_TEST_FIXTURE'))
        im=Image();im.header.stamp=c.clock;im.height=480;im.width=640;im.encoding='rgb8';im.step=1920;im.data=bytes(640*480*3);self.image_pub.publish(im)


def main():spin(Fixture)
