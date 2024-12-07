import socket
import json
import os
import struct
from threading import Thread, Lock
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Configuration
MAIN_SERVER_HOST = "localhost"
MAIN_SERVER_PORT = 8000
SEGMENT_SIZE = 1024 * 1024  # 1MB
MAX_RETRIES = 3


class FileDownloader:
    def __init__(self, output_file, total_segments):
        self.output_file = output_file
        self.total_segments = total_segments
        self.downloaded_segments = set()
        self.lock = Lock()

    def download_segment(self, segment_id):
        for attempt in range(MAX_RETRIES):
            try:
                # Get segment info from main server
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((MAIN_SERVER_HOST, MAIN_SERVER_PORT))
                    request = {"type": "get_segment_info", "segment_id": segment_id}
                    s.send(json.dumps(request).encode())
                    response = json.loads(s.recv(1024).decode())

                if "error" in response:
                    logging.warning(f"Error getting segment info: {response['error']}")
                    continue

                # Download segment from minor server
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((MAIN_SERVER_HOST, response["port"]))
                    s.send(f"GET_SEGMENT {segment_id}".encode())

                    # Receive segment size
                    size_data = s.recv(4)
                    size = struct.unpack("!I", size_data)[0]

                    if size == 0:
                        logging.warning(
                            f"Error downloading segment {segment_id}: Segment not found"
                        )
                        continue

                    # Receive segment data
                    segment_data = b""
                    while len(segment_data) < size:
                        chunk = s.recv(min(4096, size - len(segment_data)))
                        if not chunk:
                            break
                        segment_data += chunk

                # Write segment to file
                with self.lock:
                    with open(self.output_file, "r+b") as f:
                        f.seek((segment_id - 1) * SEGMENT_SIZE)
                        f.write(segment_data)
                    self.downloaded_segments.add(segment_id)

                logging.info(f"Downloaded segment {segment_id}")
                return True

            except Exception as e:
                logging.error(
                    f"Error downloading segment {segment_id} (attempt {attempt + 1}): {e}"
                )

        logging.error(
            f"Failed to download segment {segment_id} after {MAX_RETRIES} retries"
        )
        return False

    def download(self):
        threads = []
        for segment_id in range(1, self.total_segments + 1):
            if segment_id not in self.downloaded_segments:
                thread = Thread(target=self.download_segment, args=(segment_id,))
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

        if len(self.downloaded_segments) == self.total_segments:
            logging.info("Download completed successfully")
        else:
            missing_segments = (
                set(range(1, self.total_segments + 1)) - self.downloaded_segments
            )
            logging.warning(
                f"Download incomplete. Missing segments: {missing_segments}"
            )


if __name__ == "__main__":
    output_file = "downloaded_file.bin"
    total_segments = 9  # Number of segments we define in server.py

    with open(output_file, "wb") as f:
        f.write(b"\0" * SEGMENT_SIZE * total_segments)

    downloader = FileDownloader(output_file, total_segments)
    downloader.download()
