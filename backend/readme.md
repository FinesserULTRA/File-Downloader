# Distributed File Downloader

This project implements a distributed file downloading system that splits large files into segments, distributes them across multiple minor servers, and allows clients to download and reassemble the file. The system ensures data integrity, supports resuming downloads, and compresses text files for efficient transfers.

## Features

- **File Segmentation**: Large files are split into segments and distributed across minor servers.
- **Distributed Servers**: Segments are hosted on multiple minor servers for scalability.
- **Resume Downloads**: Interrupted downloads can be resumed using a progress file.
- **Data Integrity**: File segments and assembled files are verified using checksums.
- **Compression**: Text files are compressed to save bandwidth.
- **Parallel Downloads**: Segments are downloaded concurrently for efficiency.

## Directory Structure
```
.
├── src
│   ├── data
│   │   ├── server1_segments/   # Directory for segments hosted by minor server 1
│   │   ├── server2_segments/   # Directory for segments hosted by minor server 2
│   │   └── server3_segments/   # Directory for segments hosted by minor server 3
│   ├── client.py               # Client for downloading files
│   ├── gen_test_files.py       # Script to generate test files
│   ├── generate_test_files.js  # Alternate script for generating test files
│   ├── minor_server.py         # Minor server for hosting file segments
│   ├── server.py               # Main server for managing
│   └── segment_cache.json      # Cache file for segment metadata file segmentation and requests
├── first_run.sh            # Helper script to set up the environment
├── run.sh                  # Script to run all components
└── README.md               # Project documentation
```

## Requirements
- Python 3.8+
- Required Python packages:
  - `tqdm`
  - `zlib`
  - `pickle`
- Node.js (optional for `generate_test_files.js`)

Install dependencies using pip:
```bash
pip install tqdm
```

## How to Run

### Via Script

#### 1. first_run.sh
- The first_run.sh should be run first time only, as it installs the requirements, if any, creates files, and starts all the servers
  
#### 2. run.sh
- This should be run every other time, it directly starts all the servers in dedicated terminals

### Via Command Line
#### 1. Start the Servers
#### Main Server
Start the main server to manage file segmentation and client requests:
```bash
python server.py
```

#### Minor Servers
Start the minor servers to host file segments. Each server requires a unique port and a directory for storing segments:
```bash
python minor_server.py 8001 data/server1_segments
python minor_server.py 8002 data/server2_segments
python minor_server.py 8003 data/server3_segments
```

### 2. Generate Test Files
To test the system, generate large files in the `data` directory using the provided script:
```bash
python gen_test_files.py
```

### 3. List Available Files
To list files available for download, use the client with the `--list` option:
```bash
python client.py --list
```

### 4. Download a File
To download a file, specify the file name and the output file path:
```bash
python client.py <filename> <output_file>
```
Example:
```bash
python client.py example.txt downloaded_example.txt
```

#### Alternate arguments for client
Client file has alternate arguments:
```bash
--host <hostname>
```
Specify the hostname of the main server. Default is `localhost`.

```bash
--port <port>
```
Specify the port number of the main server. Default is `8000`.

```bash
--list
```
List all available files for download from the main server.

### 5. Resume Downloads
If a download is interrupted, rerun the same command to resume downloading from the last checkpoint.
This is done via storing the segments, ids and stuff on the client side, so that it can be paused and resumed at will.

## File Compression
Text files are compressed automatically during segmentation to save bandwidth. The client decompresses the segments after downloading.
We are also doing hashing and verify checks. There is checksum, segment checks etc.

## Cache and Cleanup
The system maintains a cache (`segment_cache.json`) to store metadata about segmented files. Unused segments are automatically deleted after an hour (`CACHE_EXPIRY`).