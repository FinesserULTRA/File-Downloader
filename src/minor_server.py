import socket
import os
import struct
from threading import Thread
import logging
import hashlib
import zlib

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def calculate_checksum(data):
    return hashlib.md5(data).hexdigest()


def decompress_data(data):
    return zlib.decompress(data)


def handle_client(client_socket, base_path):
    try:
        data = client_socket.recv(1024).decode()
        request = data.strip().split()
        logging.info(f"Received request: {request}")

        if request[0] == "GET_SEGMENT":
            filename, segment_id, is_compressed = (
                request[1],
                int(request[2]),
                request[3] == "True",
            )
            file_path = os.path.join(base_path, f"{filename}_segment_{segment_id}")

            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    segment_data = f.read()

                if is_compressed:
                    segment_data = decompress_data(segment_data)

                checksum = calculate_checksum(segment_data)
                client_socket.send(
                    struct.pack("!I32s", len(segment_data), checksum.encode())
                )
                client_socket.sendall(segment_data)
                logging.info(f"Sent segment {segment_id} of {filename}")
            else:
                client_socket.send(struct.pack("!I32s", 0, b"\0" * 32))
                logging.warning(f"Segment {segment_id} of {filename} not found")
    except Exception as e:
        logging.error(f"Error handling client: {e}")
    finally:
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
