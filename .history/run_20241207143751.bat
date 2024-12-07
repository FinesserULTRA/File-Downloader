@echo off
cd src

start cmd /k "python generate_segments.py"
start cmd /k "python server.py"
start cmd /k "python minor_server.py 8001 server1_segments"
start cmd /k "python minor_server.py 8002 server2_segments"
start cmd /k "python minor_server.py 8003 server3_segments"