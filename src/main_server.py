import socket
import os
import threading
import json

WORKER_SERVERS = [
    {"host": "localhost", "port": 8001, "load": 0},
    {"host": "localhost", "port": 8002, "load": 0},
    {"host": "localhost", "port": 8003, "load": 0},
]

FRAGMENTS_DIR = "fragments"
os.makedirs(FRAGMENTS_DIR, exist_ok=True)


def split_file(file_path, num_parts):
    with open(file_path, "rb") as file:
        data = file.read()
    part_size = len(data) // num_parts
    for i in range(num_parts):
        with open(f"{FRAGMENTS_DIR}/part_{i}.bin", "wb") as part_file:
            start = i * part_size
            end = None if i == num_parts - 1 else (i + 1) * part_size
            part_file.write(data[start:end])


def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    request = conn.recv(1024).decode()
    if request.startswith("GET"):
        file_name = request.split()[1]
        if os.path.exists(file_name):
            # Distribute file fragments based on worker load
            num_workers = len(WORKER_SERVERS)
            split_file(file_name, num_workers)
            assignments = []
            for i, server in enumerate(WORKER_SERVERS):
                fragment_path = f"{FRAGMENTS_DIR}/part_{i}.bin"
                assignments.append({"server": server, "fragment": fragment_path})
                server["load"] += 1  # Simulate load increment

            conn.send(json.dumps(assignments).encode())
        else:
            conn.send(b"ERROR: File not found")
    conn.close()


def main_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 9000))
    server_socket.listen(5)
    print("Main server running on port 9000")
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    main_server()
