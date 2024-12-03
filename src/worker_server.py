import socket
import os
import threading

WORKER_DIR = "worker_fragments"
os.makedirs(WORKER_DIR, exist_ok=True)


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


if __name__ == "__main__":
    ports = [8001, 8002, 8003]
    threads = []
    for port in ports:
        thread = threading.Thread(target=worker_server, args=(port,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()