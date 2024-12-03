import socket
import sys
import os
import json
import threading

DELIMITER = "||"
RECOMBINED_DIR = "recombined"
os.makedirs(RECOMBINED_DIR, exist_ok=True)


def request_file(server_host, server_port, file_name):
    try:
        # Connect to the main server
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, server_port))
        request = f"GET {file_name}"
        client_socket.send(request.encode())
        response = client_socket.recv(4096).decode()
        client_socket.close()

        return json.loads(response)
    except Exception as e:
        print(f"Error: {e}")
        return None


def request_fragment(server_info, fragment_name):
    try:
        worker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        worker_socket.connect((server_info["host"], server_info["port"]))

        # Send the "DOWNLOAD" request
        request = f"DOWNLOAD{DELIMITER}{fragment_name}"
        worker_socket.sendall(request.encode())

        # Receive fragment data
        fragment_data = b""
        while True:
            data = worker_socket.recv(4096)
            if not data:
                break
            fragment_data += data

        worker_socket.close()
        if fragment_data.startswith(b"ERROR"):
            print(
                f"Error retrieving fragment '{fragment_name}' from {server_info['host']}:{server_info['port']}"
            )
            return None
        return fragment_data
    except Exception as e:
        print(
            f"Error retrieving fragment '{fragment_name}' from {server_info['host']}:{server_info['port']} - {e}"
        )
        return None


def recombine_fragments(assignments, output_file):
    with open(output_file, "wb") as outfile:
        for assignment in assignments:
            server_info = assignment["server"]
            fragment_name = assignment["fragment"]
            fragment_data = request_fragment(server_info, fragment_name)
            if fragment_data is not None:
                outfile.write(fragment_data)
            else:
                print(f"Failed to retrieve fragment: {fragment_name}")
                return False
    print(f"Recombined file saved as {output_file}")
    return True


def threaded_request_fragment(server_info, fragment_name, results, index):
    fragment_data = request_fragment(server_info, fragment_name)
    results[index] = fragment_data


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python client.py <server_host> <server_port> <file_name>")
        sys.exit(1)

    server_host = sys.argv[1]
    server_port = int(sys.argv[2])
    file_name = sys.argv[3]

    # Step 1: Request file fragments from the main server
    assignments = request_file(server_host, server_port, file_name)
    if not assignments:
        print("Failed to retrieve fragment information from the main server.")
        sys.exit(1)

    # Step 2: Recombine fragments into the original file using multiple threads
    output_file = os.path.join(RECOMBINED_DIR, os.path.basename(file_name))
    results = [None] * len(assignments)
    threads = []

    for i, assignment in enumerate(assignments):
        server_info = assignment["server"]
        fragment_name = assignment["fragment"]
        thread = threading.Thread(
            target=threaded_request_fragment,
            args=(server_info, fragment_name, results, i),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    with open(output_file, "wb") as outfile:
        for fragment_data in results:
            if fragment_data is not None:
                outfile.write(fragment_data)
            else:
                print("File recombination failed.")
                sys.exit(1)

    print(f"Recombined file saved as {output_file}")
    print("File recombination successful!")
