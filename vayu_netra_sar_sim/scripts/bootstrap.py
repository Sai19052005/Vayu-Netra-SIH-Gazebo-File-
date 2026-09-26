import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lock=json.loads((ROOT/'dependencies.lock.json').read_text())


def checkout(key,path):
    item=lock[key]
    if (path/'.git').exists():
        head=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
        if head!=item['commit']:raise SystemExit(f'{path}: wrong commit. Keep it intact and select a fresh extracted workspace; no automatic reset.')
    else:
        path.mkdir(parents=True,exist_ok=True)
        if list(path.iterdir()):raise SystemExit(f'Refusing to overwrite nonempty {path}')
        subprocess.run(['git','init',str(path)],check=True)
        subprocess.run(['git','-C',str(path),'remote','add','origin',item['url']],check=True)
        subprocess.run(['git','-C',str(path),'fetch','--depth','1','origin',item['commit']],check=True)
        subprocess.run(['git','-C',str(path),'checkout','--detach','FETCH_HEAD'],check=True)
    if key in ('px4','agent'):subprocess.run(['git','-C',str(path),'submodule','update','--init','--recursive','--depth','1'],check=True)


for key,path in [('px4',ROOT/'vendor/PX4-Autopilot'),('px4_msgs',ROOT/'src/px4_msgs'),('agent',ROOT/'vendor/Micro-XRCE-DDS-Agent')]:checkout(key,path)
# Keep vendor projects out of colcon's recursive discovery.
(ROOT/'vendor/COLCON_IGNORE').touch()
