import socket
import os
import struct
from threading import Thread
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
SEGMENT_SIZE = 1024 * 1024  # 1MB


def handle_client(client_socket, base_path):
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                break

            request = data.decode().strip()
            logging.info(f"Received request: {request}")

            if request.startswith("GET_SEGMENT"):
                _, segment_id = request.split()
                segment_id = int(segment_id)
                file_path = os.path.join(base_path, f"segment_{segment_id}.bin")

                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        segment_data = f.read()

                    # Send segment size first
                    client_socket.send(struct.pack("!I", len(segment_data)))
                    # Then send the segment data
                    client_socket.sendall(segment_data)
                    logging.info(f"Sent segment {segment_id}")
                else:
                    client_socket.send(
                        struct.pack("!I", 0)
                    )  # Send size 0 to indicate error
                    logging.warning(f"Segment {segment_id} not found")
        except Exception as e:
            logging.error(f"Error handling client: {e}")
            break

    client_socket.close()


def run_server(port, base_path):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)
    logging.info(f"Minor server listening on port {port}")

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Accepted connection from {addr}")
        client_handler = Thread(target=handle_client, args=(client_socket, base_path))
        client_handler.start()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python minor_server.py <port> <base_path>")
        sys.exit(1)

    port = int(sys.argv[1])
    base_path = sys.argv[2]
    run_server(port, base_path)
