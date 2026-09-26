from pathlib import Path
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler, EmitEvent
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def assemble(context):
    share=Path(get_package_share_directory('vayu_netra_sim'))
    mode=LaunchConfiguration('mode').perform(context)
    if mode not in ('quick','full','test'):raise ValueError('mode must be quick/full/test')
    params={'use_sim_time':True,'config_path':str(share/'config'/('full.yaml' if mode=='full' else 'quick.yaml')),
            'output_dir':LaunchConfiguration('output_dir').perform(context)}
    nodes=[]
    if mode!='test':
        nodes.append(Node(package='ros_gz_bridge',executable='parameter_bridge',name='sensor_bridge',parameters=[{'config_file':str(share/'config/bridge.yaml')}],output='screen'))
    for executable in ['test_fixture' if mode=='test' else 'offboard_controller','mission_manager','perception','thermal_simulator','fusion_triage','mapping','dashboard']:
        extra={}
        if executable=='perception':extra={'perception_mode':LaunchConfiguration('perception').perform(context),'model_path':LaunchConfiguration('model_path').perform(context)}
        env={}
        if executable=='perception' and extra.get('perception_mode')=='yolo':
            site=os.environ.get('VAYU_YOLO_SITE','')
            if not site:raise ValueError('Run setup_yolo.sh and start via run_demo.sh --perception yolo --model PATH')
            env['PYTHONPATH']=site+os.pathsep+os.environ.get('PYTHONPATH','')
        nodes.append(Node(package='vayu_netra_sim',executable=executable,parameters=[params,extra],additional_env=env,output='screen'))
    handlers=[RegisterEventHandler(OnProcessExit(target_action=n,on_exit=[EmitEvent(event=Shutdown(reason='A required SAR process exited; stopping graph'))])) for n in nodes]
    return nodes+handlers


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument('mode',default_value='quick'),DeclareLaunchArgument('perception',default_value='simulated'),DeclareLaunchArgument('model_path',default_value=''),DeclareLaunchArgument('output_dir',default_value='runs/current'),OpaqueFunction(function=assemble)])
