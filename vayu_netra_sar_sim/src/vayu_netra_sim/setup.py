from pathlib import Path
from setuptools import setup, find_packages
name='vayu_netra_sim'
data=[('share/ament_index/resource_index/packages',['resource/'+name]),('share/'+name,['package.xml'])]
for directory in ['launch','config','worlds','models','rviz','web']:
    for parent in sorted({p.parent for p in Path(directory).rglob('*') if p.is_file() and '__pycache__' not in str(p)}):
        data.append(('share/'+name+'/'+str(parent),[str(p) for p in parent.iterdir() if p.is_file() and p.suffix!='.pyc']))
entries={'mission_manager':'mission_node','offboard_controller':'offboard_controller','perception':'perception_node','thermal_simulator':'thermal_simulator','fusion_triage':'fusion_node','mapping':'mapping_node','dashboard':'dashboard_node','test_fixture':'test_fixture_node'}
setup(name=name,version='1.0.0',packages=find_packages(exclude=['tests']),data_files=data,install_requires=['setuptools'],zip_safe=False,maintainer='Team AEROINDIA',maintainer_email='aeroindia@example.invalid',description='SAR simulation for Jazzy/Harmonic',license='MIT',entry_points={'console_scripts':[f'{key} = {name}.{module}:main' for key,module in entries.items()]})
