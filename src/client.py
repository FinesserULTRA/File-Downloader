import socket
import json
import os
import struct
from threading import Thread, Lock
import logging
import time
import argparse
import hashlib
from tqdm import tqdm
import zlib

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAIN_SERVER_HOST = "localhost"
MAIN_SERVER_PORT = 8000
MAX_RETRIES = 3
RESUME_FILE = "download_resume.json"


class FileDownloader:
    def __init__(self, filename, output_file, main_server_host, main_server_port):
        self.filename = filename
        self.output_file = output_file
        self.main_server_host = main_server_host
        self.main_server_port = main_server_port
        self.lock = Lock()
        self.file_info = self.get_file_info()
        if self.file_info != {}:
            if "error" in self.file_info:
                raise ValueError(f"Error: {self.file_info['error']}")
            self.total_segments = self.file_info["total_segments"]
            self.segment_size = self.file_info["segment_size"]
            self.file_size = self.file_info["file_size"]
            self.segments = self.file_info["segments"]
            self.is_compressed = self.file_info["is_compressed"]
            self.checksum = self.file_info.get("checksum")
            self.downloaded_segments = set()
            self.pbar = tqdm(
                total=self.file_size, unit="B", unit_scale=True, desc=self.filename
            )
            self.load_resume_data()

    def get_file_info(self):
        if self.filename != "nil":
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.main_server_host, self.main_server_port))
                request = {"type": "get_file_info", "filename": self.filename}
                s.send(json.dumps(request).encode())
                response = json.loads(s.recv(4096).decode())
            return response
        else:
            return {}

    def load_resume_data(self):
        if os.path.exists(RESUME_FILE):
            with open(RESUME_FILE, "r") as f:
                resume_data = json.load(f)
                if resume_data.get("filename") == self.filename:
                    self.downloaded_segments = set(resume_data["downloaded_segments"])
                    logging.info(
                        f"Resumed download. Already downloaded segments: {self.downloaded_segments}"
                    )
                    self.pbar.update(
                        sum(
                            self.segments[i - 1]["end"] - self.segments[i - 1]["start"]
                            for i in self.downloaded_segments
                        )
                    )

    def save_resume_data(self):
        with open(RESUME_FILE, "w") as f:
            json.dump(
                {
                    "filename": self.filename,
                    "downloaded_segments": list(self.downloaded_segments),
                },
                f,
            )

    def calculate_checksum(self, data):
        return hashlib.md5(data).hexdigest()

    def download_segment(self, segment):
        segment_id = segment["id"]
        server = segment["server"]
        for attempt in range(MAX_RETRIES):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((server["host"], server["port"]))
                    s.send(
                        f"GET_SEGMENT {self.filename} {segment_id} {self.is_compressed}".encode()
                    )

                    size_and_checksum = s.recv(36)
                    size, checksum = struct.unpack("!I32s", size_and_checksum)
                    checksum = checksum.decode()

                    if size == 0:
                        logging.warning(
                            f"Error downloading segment {segment_id}: Segment not found"
                        )
                        continue

                    segment_data = b""
                    while len(segment_data) < size:
                        chunk = s.recv(min(4096, size - len(segment_data)))
                        if not chunk:
                            break
                        segment_data += chunk

                    if self.calculate_checksum(segment_data) != checksum:
                        logging.warning(f"Checksum mismatch for segment {segment_id}")
                        continue

                with self.lock:
                    with open(self.output_file, "r+b") as f:
                        f.seek(segment["start"])
                        f.write(segment_data)
                    self.downloaded_segments.add(segment_id)
                    self.save_resume_data()
                    self.pbar.update(len(segment_data))

                # logging.info(f"Downloaded segment {segment_id}")
                return True

            except Exception as e:
                logging.error(
                    f"Error downloading segment {segment_id} (attempt {attempt + 1}): {e}"
                )
                time.sleep(1)  # Wait before retrying

        logging.error(
            f"Failed to download segment {segment_id} after {MAX_RETRIES} retries"
        )
        return False

    def download(self):
        if not os.path.exists(self.output_file):
            with open(self.output_file, "wb") as f:
                f.seek(self.file_size - 1)
                f.write(b"\0")

        threads = []
        for segment in self.segments:
            if segment["id"] not in self.downloaded_segments:
                thread = Thread(target=self.download_segment, args=(segment,))
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

        self.pbar.close()

        if len(self.downloaded_segments) == self.total_segments:
            logging.info("Download completed successfully")
            os.remove(RESUME_FILE)
            # self.verify_file_integrity()
        else:
            missing_segments = (
                set(range(1, self.total_segments + 1)) - self.downloaded_segments
            )
            logging.warning(
                f"Download incomplete. Missing segments: {missing_segments}"
            )

    def verify_file_integrity(self):
        logging.info("Verifying file integrity...")
        with open(self.output_file, "rb") as f:
            file_data = f.read()

        file_checksum = self.calculate_checksum(file_data)
        # if file_checksum == self.checksum:
        if file_checksum == self.file_info.get("checksum"):
            logging.info("File integrity verified successfully")
        else:
            logging.error("File integrity check failed")

    def get_all_files(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.main_server_host, self.main_server_port))
            request = {"type": "list_files"}
            s.send(json.dumps(request).encode())
            response = json.loads(s.recv(4096).decode())
        return response.get("files", [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dynamic File Downloader")
    parser.add_argument("filename", nargs="?", help="Name of the file to download")
    parser.add_argument("output_file", nargs="?", help="Path to the output file")
    parser.add_argument("--host", default="localhost", help="Main server host")
    parser.add_argument("--port", type=int, default=8000, help="Main server port")
    parser.add_argument("--list", action="store_true", help="List available files")

    args = parser.parse_args()

    if args.list:
        downloader = FileDownloader("nil", "nil", args.host, args.port)
        files = downloader.get_all_files()
        print("Available files:")
        for file in files:
            print(f"- {file}")
    elif args.filename and args.output_file:
        try:
            downloader = FileDownloader(
                args.filename, args.output_file, args.host, args.port
            )
            downloader.download()
        except ValueError as e:
            print(f"Error: {e}")
    else:
        print("Error: 'filename' and 'output_file' are required unless using '--list'.")
