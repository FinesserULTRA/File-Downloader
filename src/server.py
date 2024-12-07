import socket
import json
from threading import Thread
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
MAIN_SERVER_PORT = 8000
SEGMENT_SIZE = 1024 * 1024  # 1MB
MINOR_SERVERS = [
    {"port": 8001, "segments": [1, 2, 3]},
    {"port": 8002, "segments": [4, 5, 6]},
    {"port": 8003, "segments": [7, 8, 9]},
]


def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break

            request = json.loads(data)
            logging.info(f"Received request: {request}")

            if request["type"] == "get_segment_info":
                segment_id = request["segment_id"]
                for server in MINOR_SERVERS:
                    if segment_id in server["segments"]:
                        response = {"segment_id": segment_id, "port": server["port"]}
                        client_socket.send(json.dumps(response).encode())
                        logging.info(f"Sent response: {response}")
                        break
                else:
                    error_msg = {"error": f"Segment {segment_id} not found"}
                    client_socket.send(json.dumps(error_msg).encode())
                    logging.warning(f"Sent error response: {error_msg}")
        except Exception as e:
            logging.error(f"Error handling client: {e}")
            break

    client_socket.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", MAIN_SERVER_PORT))
    server_socket.listen(5)
    logging.info(f"Main server listening on port {MAIN_SERVER_PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Accepted connection from {addr}")
        client_handler = Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    main()
