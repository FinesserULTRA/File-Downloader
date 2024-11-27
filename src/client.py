import socket
import threading
import json
import os

DOWNLOADS_DIR = "downloads"
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def download_fragment(server, fragment, output_path):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server["host"], server["port"]))
    client_socket.send(fragment.encode())  # Request specific fragment
    with open(output_path, 'wb') as file:
        while chunk := client_socket.recv(1024):
            file.write(chunk)
    client_socket.close()
    print(f"Downloaded {fragment} from {server['host']}:{server['port']}")

def combine_files(output_file, input_dir):
    with open(output_file, 'wb') as outfile:
        for part in sorted(os.listdir(input_dir)):
            with open(f"{input_dir}/{part}", 'rb') as part_file:
                outfile.write(part_file.read())
    print(f"Combined fragments into {output_file}")

def client():
    main_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    main_server_socket.connect(('localhost', 9000))
    main_server_socket.send(b"GET large_file.bin")
    response = main_server_socket.recv(4096).decode()
    assignments = json.loads(response)
    main_server_socket.close()

    threads = []
    for i, assignment in enumerate(assignments):
        output_path = f"{DOWNLOADS_DIR}/fragment_{i}.bin"
        thread = threading.Thread(
            target=download_fragment,
            args=(assignment["server"], assignment["fragment"], output_path)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    combine_files(f"{DOWNLOADS_DIR}/final_output.bin", DOWNLOADS_DIR)

if __name__ == "__main__":
    client()
