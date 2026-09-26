"""Own child process groups, wait for actual world readiness, preserve per-run logs."""
import argparse,json,os,signal,socket,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['quick','full'],default='quick');parser.add_argument('--headless',action='store_true');parser.add_argument('--perception',choices=['simulated','yolo'],default='simulated');parser.add_argument('--model',default='');args=parser.parse_args()
    if args.perception=='yolo' and not Path(args.model).is_file():raise SystemExit('YOLO requires --model /absolute/path/yolov8n.pt; run setup_yolo.sh beforehand')
    lockdir=ROOT/'.runtime';lockdir.mkdir(exist_ok=True)
    import fcntl
    lockfile=(lockdir/'supervisor.lock').open('w')
    try:fcntl.flock(lockfile,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:raise SystemExit('Another VAYU supervisor is running')
    for port,kind in [(8080,socket.SOCK_STREAM),(8888,socket.SOCK_DGRAM)]:
        with socket.socket(socket.AF_INET,kind) as sock:
            try:sock.bind(('127.0.0.1',port))
            except OSError:raise SystemExit(f'Port {port} occupied; stop its owner before starting. No broad process killing.')
    output=ROOT/'runs'/time.strftime('%Y%m%d-%H%M%S');output.mkdir(parents=True)
    share=Path(subprocess.check_output(['ros2','pkg','prefix','--share','vayu_netra_sim'],text=True).strip())
    px4=ROOT/'vendor/PX4-Autopilot';gz=px4/'Tools/simulation/gz'
    env=dict(os.environ, GZ_PARTITION='vayu_'+str(os.getpid()),
             GZ_SIM_RESOURCE_PATH=os.pathsep.join([str(share/'models'),str(gz/'models'),str(gz/'worlds')]),
             GZ_SIM_SYSTEM_PLUGIN_PATH=str(px4/'build/px4_sitl_default/src/modules/simulation/gz_plugins'),
             PX4_GZ_STANDALONE='1',PX4_GZ_WORLD='disaster_zone',PX4_GZ_MODEL_NAME='vayu_netra_0',
             PX4_SIM_MODEL='gz_x500',PX4_SYS_AUTOSTART='4001',PX4_SIMULATOR='gz',PX4_UXRCE_DDS_PORT='8888',
             PX4_PARAM_COM_RC_IN_MODE='4',PX4_PARAM_COM_RCL_EXCEPT='4',PX4_PARAM_COM_OF_LOSS_T='1',
             PX4_PARAM_COM_OBL_RC_ACT='4',PX4_PARAM_COM_DISARM_LAND='2',PX4_PARAM_NAV_DLL_ACT='0',
             PX4_PARAM_UXRCE_DDS_SYNCT='0',PX4_PARAM_MPC_XY_CRUISE='3',
             PX4_PARAM_UXRCE_DDS_PTCFG='1',
             ROS_DOMAIN_ID='42',ROS_LOCALHOST_ONLY='1')
    env['LD_LIBRARY_PATH']=str(ROOT/'vendor/agent-install/lib')+os.pathsep+env.get('LD_LIBRARY_PATH','')
    if args.perception=='yolo':
        interpreter=ROOT/'.yolo-venv/bin/python'
        if not interpreter.is_file():raise SystemExit('Run ./setup_yolo.sh first')
        env['VAYU_YOLO_SITE']=subprocess.check_output([str(interpreter),'-c','import site;print(site.getsitepackages()[0])'],text=True).strip()
    children=[];files=[]
    def start(name,cmd,cwd=ROOT):
        log=(output/(name+'.log')).open('w');files.append(log)
        p=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        children.append((name,p));print(f'{name}: PID{p.pid}, log {output/name}.log',flush=True)
        return p
    def stop(*_):raise KeyboardInterrupt
    signal.signal(signal.SIGINT,stop);signal.signal(signal.SIGTERM,stop)
    (lockdir/'supervisor.json').write_text(json.dumps(dict(pid=os.getpid(),start_ticks=Path(f'/proc/{os.getpid()}/stat').read_text().split()[21],output=str(output))))
    try:
        start('agent',[str(ROOT/'vendor/agent-install/bin/MicroXRCEAgent'),'udp4','-p','8888'])
        command=['gz','sim','-r','-s',str(share/'worlds/disaster_zone.sdf')]
        if args.headless:command.insert(2,'--headless-rendering')
        start('gazebo',command)
        deadline=time.monotonic()+60
        while True:
            if any(p.poll() is not None for _,p in children):raise RuntimeError('Gazebo/Agent exited during startup; inspect logs')
            result=subprocess.run(['gz','service','-l'],env=env,capture_output=True,text=True,timeout=5)
            if '/world/disaster_zone/scene/info' in result.stdout:break
            if time.monotonic()>deadline:raise RuntimeError('World readiness timeout. Check Gazebo log/resources/OpenGL.')
            time.sleep(.5)
        if not args.headless:start('gazebo_gui',['gz','sim','-g'])
        work=output/'px4';work.mkdir()
        # PX4 binary's -s startup script resolves ROMFS through explicit symlink in a fresh run directory.
        (work/'etc').symlink_to(px4/'build/px4_sitl_default/etc',target_is_directory=True)
        start('px4',[str(px4/'build/px4_sitl_default/bin/px4'),'-i','0','-d','-s','etc/init.d-posix/rcS'],work)
        start('ros',['ros2','launch','vayu_netra_sim','sar.launch.py',f'mode:={args.mode}',f'perception:={args.perception}',f'model_path:={args.model}',f'output_dir:={output}'])
        print('Dashboard http://127.0.0.1:8080 | Ctrl+C ends this SIMULATION. Logs: '+str(output),flush=True)
        while True:
            for name,p in children:
                if p.poll() is not None:raise RuntimeError(f'{name} exited ({p.returncode}); inspect {output}/{name}.log')
            time.sleep(.5)
    except KeyboardInterrupt:print('Stopping this simulation process group set…',flush=True)
    finally:
        # ROS first, so mapping can save an interrupted report. PX4/Gazebo follow.
        for _,p in reversed(children):
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGINT)
                except ProcessLookupError:pass
        deadline=time.monotonic()+5
        while any(p.poll() is None for _,p in children) and time.monotonic()<deadline:time.sleep(.1)
        for _,p in reversed(children):
            if p.poll() is None:
                try:os.killpg(p.pid,signal.SIGKILL)
                except ProcessLookupError:pass
            p.wait()
        for file in files:file.close()
        (lockdir/'supervisor.json').unlink(missing_ok=True)
        lockfile.close()


if __name__=='__main__':main()
