import socket
import os
import threading
import json
import time

WORKER_SERVERS = [
    {"host": "localhost", "port": 8001, "load": 0},
    {"host": "localhost", "port": 8002, "load": 0},
    {"host": "localhost", "port": 8003, "load": 0},
]

WORKER_DIR = "worker_fragments"
FRAGMENTS_DIR = "fragments"
if not os.path.exists(WORKER_DIR):
    os.makedirs(WORKER_DIR)

if not os.path.exists(FRAGMENTS_DIR):
    os.makedirs(FRAGMENTS_DIR)

# Delimiter to separate different parts of the request
DELIMITER = "||"


def handle_connection(conn, addr):
    print(f"Connected to: {addr}")
    try:
        # Step 1: Read the request data
        request_data = conn.recv(4096).decode().strip()
        print(f"Request data received: {request_data}")

        # Split the request data based on the delimiter
        parts = request_data.split(DELIMITER)
        request_type = parts[0]

        if request_type == "UPLOAD":
            # Extract fragment name and data
            fragment_name = parts[1]
            fragment_data = parts[2].encode()
            print(f"Uploading fragment: {fragment_name}")

            # Save the fragment
            fragment_path = os.path.join(WORKER_DIR, fragment_name)
            with open(fragment_path, "wb") as fragment_file:
                fragment_file.write(fragment_data)
            print(f"Fragment {fragment_name} saved to {fragment_path}")
            conn.send(b"ACK")  # Acknowledge successful upload

        elif request_type == "DOWNLOAD":
            # Extract fragment name
            fragment_name = parts[1]
            print(f"Downloading fragment: {fragment_name}")

            fragment_path = os.path.join(WORKER_DIR, fragment_name)
            if os.path.exists(fragment_path):
                # Send the fragment back to the client
                with open(fragment_path, "rb") as fragment_file:
                    conn.sendall(fragment_file.read())
                print(f"Fragment {fragment_name} sent to {addr}")
            else:
                print(f"Fragment {fragment_name} not found.")
                conn.send(b"ERROR: Fragment not found")
        else:
            print(f"Unknown request type: {request_type}")
            conn.send(b"ERROR: Unknown request type")
    except Exception as e:
        print(f"Error handling connection {addr}: {e}")
    finally:
        conn.close()


def worker_server(port):
    """
    Starts the worker server on the given port using threads.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", port))
    server_socket.listen(5)
    print(f"Worker server running on port {port}")
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_connection, args=(conn, addr)).start()


def split_file(file_path, num_parts):
    with open(file_path, "rb") as file:
        data = file.read()
    part_size = len(data) // num_parts
    for i in range(num_parts):
        with open(f"{FRAGMENTS_DIR}/part_{i}.bin", "wb") as part_file:
            start = i * part_size
            end = None if i == num_parts - 1 else (i + 1) * part_size
            part_file.write(data[start:end])


def distribute_fragments(num_workers):
    assignments = []
    for i in range(num_workers):
        least_loaded_worker = min(WORKER_SERVERS, key=lambda x: x["load"])
        fragment_path = f"{FRAGMENTS_DIR}/part_{i}.bin"
        with open(fragment_path, "rb") as fragment_file:
            fragment_data = fragment_file.read()
        try:
            worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            worker_socket.connect(
                (least_loaded_worker["host"], least_loaded_worker["port"])
            )
            # Send request type
            request = f"UPLOAD{DELIMITER}{os.path.basename(fragment_path)}{DELIMITER}{fragment_data.decode()}"
            worker_socket.sendall(request.encode())

            # Receive acknowledgment
            ack = worker_socket.recv(1024).decode()
            if ack == "ACK":
                print(
                    f"Fragment {os.path.basename(fragment_path)} successfully sent to {least_loaded_worker['host']}:{least_loaded_worker['port']}"
                )
                assignments.append(
                    {
                        "server": least_loaded_worker,
                        "fragment": os.path.basename(fragment_path),
                    }
                )
                least_loaded_worker["load"] += 1
            else:
                print(
                    f"Worker did not acknowledge receipt of fragment {os.path.basename(fragment_path)}"
                )
        except Exception as e:
            print(
                f"Error sending fragment {os.path.basename(fragment_path)} to worker {least_loaded_worker}: {e}"
            )
        finally:
            worker_socket.close()
    return assignments


def cleanup_fragments():
    for file in os.listdir(FRAGMENTS_DIR):
        os.remove(os.path.join(FRAGMENTS_DIR, file))
    print("Temporary fragments cleaned up.")


def reset_loads():
    while True:
        time.sleep(60)  # Reset every minute
        for worker in WORKER_SERVERS:
            worker["load"] = 0
        print("Worker loads reset.")


def main_server():
    threading.Thread(target=reset_loads, daemon=True).start()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 9000))
    server_socket.listen(5)
    print("Main server running on port 9000")
    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()


def handle_client(conn, addr):
    print(f"Client connected: {addr}")
    try:
        request = conn.recv(1024).decode()
        if request.startswith("GET"):
            file_name = request.split()[1]
            if os.path.exists(file_name):
                num_workers = len(WORKER_SERVERS)
                split_file(file_name, num_workers)
                assignments = distribute_fragments(num_workers)
                conn.send(json.dumps(assignments).encode())
                cleanup_fragments()
            else:
                conn.send(b"ERROR: File not found")
        else:
            conn.send(b"ERROR: Invalid request")
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main_server()
