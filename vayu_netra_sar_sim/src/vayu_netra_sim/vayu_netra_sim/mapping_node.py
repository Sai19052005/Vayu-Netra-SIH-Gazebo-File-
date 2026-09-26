import time
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from .ros_support import Base, spin, qos_profile_sensor_data
from .report_generator import Recorder


class MappingNode(Base):
    def __init__(self):
        super().__init__('mapping')
        self.recorder=Recorder(self.cfg);self.mission={};self.image_seen=0
        self.listen('/vayu/flight',self.flight);self.listen('/vayu/triage',self.recorder.observation)
        self.listen('/vayu/events',lambda e:self.recorder.events.append(e))
        self.listen('/vayu/mission',self.status)
        self.create_subscription(Image,'/vayu/camera/image',lambda _:setattr(self,'image_seen',time.monotonic()),qos_profile_sensor_data)
        self.markers=self.create_publisher(MarkerArray,'/vayu/map_markers',10)
        self.create_timer(.5,self.snapshot);self.health_ok=True

    def flight(self,f):
        if f.get('valid') and f.get('fresh'):
            self.recorder.pose(f['timestamp'],f['position'],self.mission.get('state')=='SEARCH',time.monotonic()-self.image_seen<2)

    def status(self,m):self.mission=m;self.recorder.status=m['state']

    def snapshot(self):
        self.send('/vayu/map',self.recorder.report())
        self.recorder.save(self.output_dir)
        array=MarkerArray()
        for i,o in enumerate(self.recorder.incidents.values()):
            if o['local_position'] is None:continue
            marker=Marker();marker.header.frame_id='map';marker.header.stamp=self.get_clock().now().to_msg()
            marker.ns='incidents';marker.id=i;marker.type=Marker.TEXT_VIEW_FACING;marker.action=Marker.ADD
            marker.pose.position.x=float(o['local_position'][0]);marker.pose.position.y=float(o['local_position'][1]);marker.pose.position.z=2.
            marker.pose.orientation.w=1.;marker.scale.z=.6;marker.color.r=1.;marker.color.g=.5;marker.color.a=1.
            marker.text=f"{o['id']} {o.get('priority','?')}";array.markers.append(marker)
        grid=Marker();grid.header.frame_id='map';grid.ns='search';grid.id=0;grid.type=Marker.LINE_STRIP;grid.action=Marker.ADD
        grid.pose.orientation.w=1.;grid.scale.x=.1;grid.color.g=.8;grid.color.b=1.;grid.color.a=1.
        grid.points=[Point(x=float(p[0]),y=float(p[1]),z=float(p[2])) for p in self.mission.get('search_grid',[])]
        array.markers.append(grid);self.markers.publish(array)

    def destroy_node(self):
        if self.recorder.status not in ('COMPLETE','ABORTED'):self.recorder.status='INTERRUPTED'
        self.recorder.save(self.output_dir)
        return super().destroy_node()


def main():spin(MappingNode)
