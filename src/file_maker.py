
def generate_large_file(file_path, size_in_mb):
    """Generate a dummy file with the specified size in MB."""
    with open(file_path, 'wb') as file:
        file.write(b'A' * (size_in_mb * 1024 * 1024))
    print(f"Generated {file_path} of size {size_in_mb} MB.")

if __name__ == "__main__":
    generate_large_file("large_file.bin", 50)
