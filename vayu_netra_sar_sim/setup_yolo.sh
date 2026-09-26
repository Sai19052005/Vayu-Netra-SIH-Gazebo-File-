#!/usr/bin/env bash
source "$(dirname -- "$0")/scripts/common.sh"
ubuntu
python3 -m venv --system-site-packages "$ROOT/.yolo-venv"
"$ROOT/.yolo-venv/bin/python" -m pip install 'torch==2.6.0' 'torchvision==0.21.0' --index-url https://download.pytorch.org/whl/cpu
"$ROOT/.yolo-venv/bin/python" -m pip install 'numpy==1.26.4'
"$ROOT/.yolo-venv/bin/python" -m pip install 'ultralytics==8.3.203' 'opencv-python==4.11.0.86'
mkdir -p "$ROOT/weights"
cd "$ROOT/weights"
"$ROOT/.yolo-venv/bin/python" -c 'from ultralytics import YOLO; YOLO("yolov8n.pt")'
"$ROOT/.yolo-venv/bin/python" -m pip freeze > "$ROOT/weights/python-lock.txt"
sha256sum "$ROOT/weights/yolov8n.pt" > "$ROOT/weights/model.sha256"
echo 'Read Ultralytics licensing terms before redistribution. Model downloaded for local testing only.'
echo "Run: cd '$ROOT' && ./run_demo.sh --perception yolo --model '$ROOT/weights/yolov8n.pt'"
