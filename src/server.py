import socket
import json
from threading import Thread
import logging
import os
import math
import zlib
import time

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAIN_SERVER_PORT = 8000
BASE_SEGMENT_SIZE = 5 * 1024 * 1024  # 5MB base segment size
MINOR_SERVERS = [
    {"host": "localhost", "port": 8001, "dir": "server1_segments"},
    {"host": "localhost", "port": 8002, "dir": "server2_segments"},
    {"host": "localhost", "port": 8003, "dir": "server3_segments"},
]
FILE_DIR = "test_files"
CACHE_FILE = "segment_cache.json"
CACHE_EXPIRY = 3600  # 1 hour


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


cache = load_cache()


def is_text_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in [".txt", ".xml", ".json", ".csv"]


def compress_data(data):
    return zlib.compress(data)


def create_segments(filename):
    file_path = os.path.join(FILE_DIR, filename)
    file_size = os.path.getsize(file_path)
    num_segments = math.ceil(file_size / BASE_SEGMENT_SIZE)
    segment_size = math.ceil(file_size / num_segments)

    segments = []
    for i in range(num_segments):
        start = i * segment_size
        end = min((i + 1) * segment_size, file_size)
        server = MINOR_SERVERS[i % len(MINOR_SERVERS)]
        segment = {"id": i + 1, "start": start, "end": end, "server": server}
        segments.append(segment)

        # Create segment file
        segment_file = os.path.join(server["dir"], f"{filename}_segment_{i+1}")
        with open(file_path, "rb") as src, open(segment_file, "wb") as dst:
            src.seek(start)
            data = src.read(end - start)
            if is_text_file(filename):
                data = compress_data(data)
            dst.write(data)

    cache[filename] = {
        "segments": segments,
        "total_segments": num_segments,
        "segment_size": segment_size,
        "file_size": file_size,
        "is_compressed": is_text_file(filename),
        "last_accessed": time.time(),
    }
    save_cache(cache)
    return cache[filename]


def cleanup_unused_segments():
    current_time = time.time()
    for filename, info in list(cache.items()):
        if current_time - info["last_accessed"] > CACHE_EXPIRY:
            for segment in info["segments"]:
                segment_file = os.path.join(
                    segment["server"]["dir"], f"{filename}_segment_{segment['id']}"
                )
                if os.path.exists(segment_file):
                    os.remove(segment_file)
            del cache[filename]
    save_cache(cache)


def list_available_files():
    return [
        f for f in os.listdir(FILE_DIR) if os.path.isfile(os.path.join(FILE_DIR, f))
    ]


def handle_client(client_socket):
    try:
        response = {}
        data = client_socket.recv(1024).decode()
        request = json.loads(data)
        logging.info(f"Received request: {request}")

        if request["type"] == "get_file_info":
            filename = request["filename"]
            if filename not in cache:
                if filename not in list_available_files():
                    response = {"error": "File not found"}
                else:
                    file_info = create_segments(filename)
            else:
                file_info = cache[filename]
                file_info["last_accessed"] = time.time()
                save_cache(cache)

            if "error" not in response:
                response = {
                    "filename": filename,
                    "total_segments": file_info["total_segments"],
                    "segment_size": file_info["segment_size"],
                    "file_size": file_info["file_size"],
                    "segments": file_info["segments"],
                    "is_compressed": file_info["is_compressed"],
                }
            client_socket.send(json.dumps(response).encode())
            logging.info(f"Sent file info for {filename}")
        elif request["type"] == "list_files":
            files = list_available_files()
            response = {"files": files}
            client_socket.send(json.dumps(response).encode())
            logging.info("Sent list of available files")
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
        client_socket.close()


def main():
    for server in MINOR_SERVERS:
        os.makedirs(server["dir"], exist_ok=True)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", MAIN_SERVER_PORT))
    server_socket.listen(5)
    logging.info(f"Main server listening on port {MAIN_SERVER_PORT}")

    cleanup_thread = Thread(target=cleanup_unused_segments)
    cleanup_thread.daemon = True
    cleanup_thread.start()

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Accepted connection from {addr}")
        client_handler = Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    main()
