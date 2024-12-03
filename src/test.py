import socket
import os

DELIMITER = "||"

def test_upload(worker_host, worker_port, fragment_name, fragment_data):
    """
    Test uploading a fragment to the worker server.
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((worker_host, worker_port))

        # Step 1: Send the "UPLOAD" request with fragment name and data
        request = f"UPLOAD{DELIMITER}{fragment_name}{DELIMITER}{fragment_data.decode()}"
        client_socket.sendall(request.encode())

        # Step 2: Receive acknowledgment
        response = client_socket.recv(1024).decode()
        print(f"Upload response: {response}")

    except Exception as e:
        print(f"Error during upload: {e}")
    finally:
        client_socket.close()


def test_download(worker_host, worker_port, fragment_name, save_dir):
    """
    Test downloading a fragment from the worker server.
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((worker_host, worker_port))

        # Step 1: Send the "DOWNLOAD" request with the fragment name
        request = f"DOWNLOAD{DELIMITER}{fragment_name}"
        client_socket.sendall(request.encode())

        # Step 2: Receive the fragment data
        fragment_data = b""
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            fragment_data += data

        if fragment_data:
            # Save the downloaded fragment
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, fragment_name)
            with open(save_path, "wb") as fragment_file:
                fragment_file.write(fragment_data)
            print(f"Fragment {fragment_name} saved to {save_path}")
        else:
            print(f"Failed to download fragment {fragment_name}.")
    except Exception as e:
        print(f"Error during download: {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    # Worker server details
    worker_host = "localhost"
    worker_port = 8001

    # Fragment details for testing
    test_fragment_name = "test_fragment.txt"
    test_fragment_data = b"This is a test fragment for upload testing."

    # Test upload
    print("Testing upload...")
    test_upload(worker_host, worker_port, test_fragment_name, test_fragment_data)

    # Test download
    print("Testing download...")
    test_download(worker_host, worker_port, test_fragment_name, "downloaded_fragments")
