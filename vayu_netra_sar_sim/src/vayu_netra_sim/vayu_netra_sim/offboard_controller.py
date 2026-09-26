"""PX4 transport and independent setpoint watchdog. Use only with the package SITL."""
import math
import time
from rclpy.clock import Clock, ClockType
from px4_msgs.msg import (VehicleLocalPosition, VehicleStatus, VehicleLandDetected,
                         VehicleAttitude, BatteryStatus, VehicleCommandAck,
                         VehicleCommand, OffboardControlMode, TrajectorySetpoint)
from .ros_support import Base, spin, topic, qos_profile_sensor_data
from .coordinates import enu_to_ned, ned_to_enu


class OffboardController(Base):
    def __init__(self):
        super().__init__('offboard_controller')
        self.messages, self.seen, self.control = {}, {}, None
        self.control_time, self.last_command = 0., 0.
        self.offset, self.reset, self.ramped = None, None, None
        self.clock_value, self.clock_changed = 0., time.monotonic()
        self.bad_reset = False
        for name, cls in [('vehicle_local_position',VehicleLocalPosition),('vehicle_status',VehicleStatus),
                          ('vehicle_land_detected',VehicleLandDetected),('vehicle_attitude',VehicleAttitude),
                          ('battery_status',BatteryStatus),('vehicle_command_ack',VehicleCommandAck)]:
            self.create_subscription(cls, topic(name,cls), lambda msg,n=name:self.receive(n,msg), qos_profile_sensor_data)
        self.heartbeat_pub = self.create_publisher(OffboardControlMode,topic('offboard_control_mode',OffboardControlMode,'in'),10)
        self.setpoint_pub = self.create_publisher(TrajectorySetpoint,topic('trajectory_setpoint',TrajectorySetpoint,'in'),10)
        self.command_pub = self.create_publisher(VehicleCommand,topic('vehicle_command',VehicleCommand,'in'),10)
        self.listen('/vayu/control',self.accept)
        self.create_timer(.05,self.tick,clock=Clock(clock_type=ClockType.STEADY_TIME))

    def receive(self, name, msg):
        self.messages[name], self.seen[name] = msg, time.monotonic()
        if name=='vehicle_command_ack':
            self.send('/vayu/command_ack',dict(command=msg.command,result=msg.result,timestamp=self.now_s()))

    def accept(self, c):
        goal=c.get('goal')
        if goal is not None and (len(goal)!=3 or not all(math.isfinite(x) for x in goal)):
            raise ValueError('Invalid setpoint')
        self.control, self.control_time = c, time.monotonic()

    def command(self, action):
        if time.monotonic()-self.last_command < 1: return
        m=VehicleCommand();m.timestamp=int(self.now_s()*1e6)
        m.target_system=1;m.target_component=1;m.source_system=255;m.source_component=191;m.from_external=True
        if action=='OFFBOARD':m.command=VehicleCommand.VEHICLE_CMD_DO_SET_MODE;m.param1=1.;m.param2=6.
        elif action=='ARM':m.command=VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM;m.param1=1.
        elif action=='LAND':m.command=VehicleCommand.VEHICLE_CMD_NAV_LAND
        else: return
        self.command_pub.publish(m);self.last_command=time.monotonic()

    def tick(self):
        wall, now=time.monotonic(),self.now_s()
        if now!=self.clock_value:self.clock_value,self.clock_changed=now,wall
        clock_ok=now>0 and wall-self.clock_changed<2
        required=['vehicle_local_position','vehicle_status','vehicle_land_detected','vehicle_attitude']
        fresh=clock_ok and all(wall-self.seen.get(n,0)<self.cfg['mission']['feedback_timeout'] for n in required)
        p=self.messages.get('vehicle_local_position');s=self.messages.get('vehicle_status');l=self.messages.get('vehicle_land_detected');q=self.messages.get('vehicle_attitude');b=self.messages.get('battery_status')
        valid=bool(p and p.xy_valid and p.z_valid and p.v_xy_valid and p.v_z_valid and p.xy_global and p.z_global)
        if valid:
            # Fixed tangent frame referenced to world spherical_coordinates, not arbitrary local NED origin.
            lat,lon,alt=self.cfg['origin'];phi=math.radians(lat);a=6378137.;e2=.00669437999014
            n=a/math.sqrt(1-e2*math.sin(phi)**2);mer=a*(1-e2)/(1-e2*math.sin(phi)**2)**1.5
            self.offset=[math.radians(p.ref_lon-lon)*(n+alt)*math.cos(phi),math.radians(p.ref_lat-lat)*(mer+alt),p.ref_alt-alt]
            reset=(p.xy_reset_counter,p.z_reset_counter,p.heading_reset_counter)
            if self.reset is not None and self.reset!=reset and s and s.arming_state==2:self.bad_reset=True
            self.reset=reset
        position=[ned_to_enu([p.x,p.y,p.z])[i]+self.offset[i] for i in range(3)] if valid and self.offset else None
        if position is not None and not all(math.isfinite(x) for x in position):valid=False;position=None
        battery=b.remaining if b and wall-self.seen.get('battery_status',0)<4 and math.isfinite(b.remaining) and b.remaining>=0 else None
        f=dict(timestamp=now,pose_timestamp=p.timestamp/1e6 if p else None,position=position,
               valid=valid and not self.bad_reset,fresh=fresh,armed=bool(s and s.arming_state==2),
               offboard=bool(s and s.nav_state==14),landed=bool(l and l.landed),
               yaw=math.pi/2-p.heading if p and math.isfinite(p.heading) else 0.,
               quaternion=list(q.q) if q else None,
               attitude_timestamp=q.timestamp/1e6 if q else None,
               speed=math.sqrt(p.vx*p.vx+p.vy*p.vy+p.vz*p.vz) if valid else 0.,battery=battery,
               source='PX4_SITL_FEEDBACK',battery_source='PX4_SIMULATED_BATTERY' if battery is not None else 'UNAVAILABLE')
        self.send('/vayu/flight',f);self.health_ok=fresh
        c=self.control
        if c is None: return
        stale=wall-self.control_time>1 or not fresh or self.bad_reset
        if stale:
            if f['armed']:self.command('LAND')
            return  # stop offboard heartbeat; PX4 COM_OF_LOSS_T/COM_OBL_RC_ACT are the fallback
        if c.get('command'):self.command(c['command'])
        if c.get('stream') and c.get('goal') is not None and position is not None:
            if self.ramped is None:self.ramped=list(position)
            goal=c['goal'];delta=[goal[i]-self.ramped[i] for i in range(3)];length=math.sqrt(sum(x*x for x in delta))
            step=min(1.,self.cfg['mission']['search_speed']*.05/max(length,1e-6))
            # Do not let commanded trajectory get more than2m ahead of feedback.
            if math.dist(self.ramped,position)<2:self.ramped=[self.ramped[i]+delta[i]*step for i in range(3)]
            hb=OffboardControlMode();hb.timestamp=int(now*1e6);hb.position=True;self.heartbeat_pub.publish(hb)
            sp=TrajectorySetpoint();sp.timestamp=int(now*1e6)
            sp.position=enu_to_ned([self.ramped[i]-self.offset[i] for i in range(3)])
            sp.velocity=[float('nan')]*3;sp.acceleration=[float('nan')]*3;sp.jerk=[float('nan')]*3
            # Fixed eastward heading provides repeatable nadir frame geometry.
            sp.yaw=math.pi/2;sp.yawspeed=float('nan');self.setpoint_pub.publish(sp)
        else:self.ramped=None


def main():spin(OffboardController)
