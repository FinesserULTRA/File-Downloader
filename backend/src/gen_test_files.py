import os
import random
import string


def generate_random_content(size):
    """Generate random binary content of a specified size."""
    return bytes(random.randint(0, 255) for _ in range(size))


def generate_text_content(size):
    """Generate random text content of a specified size."""
    return "".join(random.choice(string.ascii_uppercase) for _ in range(size)).encode(
        "utf-8"
    )


def generate_xml_content(size):
    """Generate random XML content of a specified size."""
    header = '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n'
    footer = "</root>"
    content_size = size - len(header) - len(footer)
    content = "\n".join(
        f"  <item{i}>{random.randint(100000, 999999)}</item{i}>"
        for i in range(content_size // 20)
    )
    return (header + content + footer).encode("utf-8")


def generate_file(filename, size, file_type):
    """Generate a file with the specified size and type."""
    if file_type == "bin":
        content = generate_random_content(size)
    elif file_type == "txt":
        content = generate_text_content(size)
    elif file_type == "xml":
        content = generate_xml_content(size)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    with open(filename, "wb") as file:
        file.write(content)
    print(f"Generated {filename} ({size} bytes)")


test_files = [
    {"name": "small_file.bin", "size": 1024 * 1024, "type": "bin"},  # 1 MB
    {"name": "medium_file.txt", "size": 25 * 1024 * 1024, "type": "txt"},  # 10 MB
    {"name": "large_file.xml", "size": 200 * 1024 * 1024, "type": "xml"},  # 200 MB
]

test_dir = "test_files"
if not os.path.exists(test_dir):
    os.makedirs(test_dir)

for file in test_files:
    generate_file(os.path.join(test_dir, file["name"]), file["size"], file["type"])

print("Test files generated successfully.")
