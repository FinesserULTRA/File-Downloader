@echo off

start cmd /k "pip install -r requirements.txt"
cd src
start cmd /k "python gen_test_files.py"
start cmd /k "python server.py"
start cmd /k "python minor_server.py 8001 server1_segments"
start cmd /k "python minor_server.py 8002 server2_segments"
start cmd /k "python minor_server.py 8003 server3_segments"