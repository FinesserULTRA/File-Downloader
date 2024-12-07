import os
import random

SEGMENT_SIZE = int((1024 * 1024 * 250) / 9)  # 1MB
TOTAL_SEGMENTS = 9


def generate_segment(segment_id, base_path):
    file_path = os.path.join(base_path, f"segment_{segment_id}.bin")
    with open(file_path, "wb") as f:
        f.write(os.urandom(SEGMENT_SIZE))
    print(f"Generated segment {segment_id} in {base_path}")


def main():
    base_paths = ["server1_segments", "server2_segments", "server3_segments"]

    for base_path in base_paths:
        os.makedirs(base_path, exist_ok=True)

    segments_per_server = TOTAL_SEGMENTS // len(base_paths)
    for i, base_path in enumerate(base_paths):
        start = i * segments_per_server + 1
        end = start + segments_per_server
        for segment_id in range(start, end):
            generate_segment(segment_id, base_path)


if __name__ == "__main__":
    main()
