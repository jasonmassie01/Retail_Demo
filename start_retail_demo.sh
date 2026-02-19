#!/bin/bash
# Stop any running streamlit on port 8501
fuser -k 8501/tcp || true
sleep 2

# Run the app
nohup /usr/bin/python3 -m streamlit run ./app.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false > ./app.log 2>&1 &
echo "App started on port 8501. PID: $!"
