import argparse,json,os,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'.runtime/supervisor.json'
if not p.exists():print('No registered simulation supervisor. No files deleted.');raise SystemExit(0)
d=json.loads(p.read_text());proc=Path('/proc')/str(d['pid'])
if not proc.exists():print('Supervisor already stopped. No processes killed.');raise SystemExit(0)
if (proc/'stat').read_text().split()[21]!=d['start_ticks']:raise SystemExit('PID was reused; refusing to signal it')
command=(proc/'cmdline').read_bytes().replace(b'\0',b' ').decode()
if str(ROOT/'scripts/supervisor.py') not in command:raise SystemExit('Unexpected process owner; refusing to signal it')
os.kill(d['pid'],signal.SIGINT)
print('Requested shutdown of this package supervisor; preserving reports and sources.')
