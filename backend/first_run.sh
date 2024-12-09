#!/bin/bash

# Change to the src directory
cd src

# Launch each script in a new Command Prompt window using start
start cmd.exe /k "python gen_test_files.py"

# Wait for the to complete
wait

start cmd.exe /k "python server.py"
# Launch the remaining scripts simultaneously
start cmd.exe /k "python minor_server.py 8001 server1_segments"
start cmd.exe /k "python minor_server.py 8002 server2_segments"
start cmd.exe /k "python minor_server.py 8003 server3_segments"
