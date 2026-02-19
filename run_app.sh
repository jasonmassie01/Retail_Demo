#!/bin/bash
cd ~/retail_demo
export PYTHONUNBUFFERED=1
pkill -f streamlit
sleep 2
nohup python3 -m streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true > app.log 2>&1 &
echo "App started with PID $!"
