import json,os,platform,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
checks=[]


def record(name,ok,detail,fix=''):
    checks.append(dict(check=name,passed=bool(ok),detail=detail,fix=fix))
    print(('OK ' if ok else 'FAIL ')+name+': '+detail+((' | '+fix) if not ok else ''))


def command(args):
    try:
        r=subprocess.run(args,capture_output=True,text=True,timeout=20)
        return r.returncode==0,(r.stdout+r.stderr).strip()
    except (OSError,subprocess.TimeoutExpired) as e:return False,str(e)


record('Host',platform.system()=='Linux' and platform.machine()=='x86_64',platform.platform(),'Use Ubuntu24.04 x86_64; software tests can run elsewhere')
osrelease=Path('/etc/os-release').read_text() if Path('/etc/os-release').exists() else ''
record('Ubuntu24.04','ID=ubuntu' in osrelease and 'VERSION_ID="24.04"' in osrelease,osrelease[:180])
record('Python',sys.version_info[:2]==(3,12),sys.version.split()[0],'Use /usr/bin/python3 on Ubuntu24.04')
record('ROS_DISTRO',os.environ.get('ROS_DISTRO')=='jazzy',os.environ.get('ROS_DISTRO','unset'),'source /opt/ros/jazzy/setup.bash')
for name in ['colcon','ros2','gz','cmake','git']:
    record(name,shutil.which(name) is not None,shutil.which(name) or 'missing','Run ./setup.sh')
ok,out=command(['gz','sim','--versions']);record('Gazebo Harmonic',ok and any(x.strip().startswith('8.') for x in out.splitlines()),out,'Install gz-harmonic and ros-jazzy-ros-gzharmonic')
ok,out=command(['dpkg-query','-W','-f=${Status} ${Version}','ros-jazzy-ros-gzharmonic']);record('Harmonic ROS integration',ok and 'install ok installed' in out,out,'sudo apt install ros-jazzy-ros-gzharmonic')
for name in ['rclpy','px4_msgs','vayu_netra_sim','ros_gz_bridge','cv_bridge']:
    ok,out=command(['ros2','pkg','prefix',name]);record('ROS '+name,ok,out,'Run ./build.sh and source install/setup.bash')
ok,out=command([sys.executable,str(ROOT/'scripts/verify_contract.py')]);record('Pinned message contract',ok,out,'Run ./setup.sh in a clean extracted folder; do not reset user repositories')
for name,path in [('PX4 binary',ROOT/'vendor/PX4-Autopilot/build/px4_sitl_default/bin/px4'),('XRCE Agent2.4.3',ROOT/'vendor/agent-install/bin/MicroXRCEAgent')]:
    record(name,path.is_file(),str(path),'Run ./build.sh')
display=bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
record('Display',display or os.environ.get('VAYU_HEADLESS')=='1',str(display),'Use a logged-in Ubuntu desktop, or VAYU_HEADLESS=1 ./run_demo.sh --headless; rendering still needs EGL/OpenGL')
ok,out=command(['glxinfo','-B']) if shutil.which('glxinfo') else (False,'glxinfo unavailable; install mesa-utils for renderer diagnosis')
checks.append(dict(check='GPU diagnostic',passed=ok,detail=out,required=False))
apt_ok,apt=command(['dpkg-query','-W','-f=${Package} ${Version}\n','ros-jazzy-*','gz-*'])
(ROOT/'validation').mkdir(exist_ok=True)
(ROOT/'validation/environment.json').write_text(json.dumps(dict(checks=checks,apt_versions=apt),indent=2))
raise SystemExit(0 if all(c['passed'] for c in checks if c.get('required',True)) else 2)
