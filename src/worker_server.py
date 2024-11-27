import socket
import os
import sys

def worker_server(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", port))
    server_socket.listen(1)
    print(f"Worker server running on port {port}")

    while True:
        conn, addr = server_socket.accept()
        print(f"Connection from {addr}")
        fragment_path = conn.recv(1024).decode()
        if os.path.exists(fragment_path):
            with open(fragment_path, "rb") as file:
                while chunk := file.read(1024):
                    conn.send(chunk)
        else:
            conn.send(b"ERROR: Fragment not found")
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    worker_server(port)
