"""Refuse mismatched source commits or changed wire definitions, including version constants."""
import json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NAMES=['VehicleStatus','VehicleLocalPosition','VehicleLandDetected','VehicleAttitude','BatteryStatus','VehicleCommandAck','VehicleCommand','TrajectorySetpoint','OffboardControlMode']


def signature(path):
    return [re.sub(r'\s+','',line.split('#')[0]) for line in path.read_text().splitlines() if line.split('#')[0].strip()]


def verify(px4,msgs):
    report={}
    for name in NAMES:
        choices=[p for p in (px4/'msg').rglob(name+'.msg') if 'px4_msgs_old' not in str(p)]
        if len(choices)!=1:raise ValueError(f'Ambiguous/missing PX4 definition {name}: {choices}')
        target=msgs/'msg'/(name+'.msg')
        if signature(choices[0])!=signature(target):raise ValueError(f'Wire schema differs: {name}; use the locked matching sources')
        version=re.search(r'MESSAGE_VERSION\s*=\s*(\d+)',target.read_text())
        report[name]=dict(version=int(version[1]) if version else 0,match=True)
    return report


if __name__=='__main__':
    lock=json.loads((ROOT/'dependencies.lock.json').read_text())
    for key,path in [('px4',ROOT/'vendor/PX4-Autopilot'),('px4_msgs',ROOT/'src/px4_msgs')]:
        if not (path/'.git').exists():raise SystemExit(f'{key} source missing at {path}. Run ./setup.sh on Ubuntu24.04.')
        found=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if found!=lock[key]['commit']:raise SystemExit(f'{key} SHA mismatch: {found}')
    result=verify(ROOT/'vendor/PX4-Autopilot',ROOT/'src/px4_msgs')
    (ROOT/'validation').mkdir(exist_ok=True)
    (ROOT/'validation/message_contract.json').write_text(json.dumps(result,indent=2))
    print('PX4 and px4_msgs commits and message schemas match')
