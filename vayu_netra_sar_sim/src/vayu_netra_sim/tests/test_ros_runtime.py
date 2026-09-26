"""Opt-in target-machine startup/topic smoke test. Never represented as passed when skipped."""
import os,time
import pytest


def test_live_ros_topics():
    if os.environ.get('VAYU_ROS_INTEGRATION')!='1':pytest.skip('Requires running Jazzy SAR graph; set VAYU_ROS_INTEGRATION=1')
    rclpy=pytest.importorskip('rclpy')
    from std_msgs.msg import String
    rclpy.init();node=rclpy.create_node('vayu_runtime_pytest');received=[]
    subscription=node.create_subscription(String,'/vayu/mission',lambda msg:received.append(msg.data),10)
    try:
        deadline=time.monotonic()+15
        while not received and time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.1)
        assert received,'No mission publisher data received'
        assert 'mission_manager' in node.get_node_names()
    finally:node.destroy_node();rclpy.shutdown()
