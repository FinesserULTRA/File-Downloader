import subprocess


def start_workers(num_workers, base_port):
    processes = []
    for i in range(num_workers):
        port = base_port + i
        process = subprocess.Popen(
            [
                "python",
                "./worker_server.py",
                str(port),
            ]
        )
        processes.append(process)
        print(f"Started worker server on port {port}")

    return processes


if __name__ == "__main__":
    num_workers = 3  # Number of worker servers
    base_port = 8001  # Starting port number
    processes = start_workers(num_workers, base_port)

    try:
        print("Press Ctrl+C to stop all servers.")
        while True:
            pass
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
        print("All worker servers stopped.")
