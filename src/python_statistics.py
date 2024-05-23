import os
import glob
import sys

def count_python_files_lines(directory):
    total_files = 0
    total_lines = 0

    for python_file in glob.glob(os.path.join(directory, '**', '*.py'), recursive=True):
        # Skip the script file itself if encountered
        if os.path.abspath(python_file) == os.path.abspath(__file__):
            continue
        total_files += 1
        with open(python_file, 'rb') as file:  # Open as binary to avoid decoding issues
            for line in file:
                try:
                    line.decode('utf-8')
                    total_lines += 1
                except UnicodeDecodeError:
                    # Optionally, handle or log the error here
                    pass  # Skip lines that can't be decoded in UTF-8

    return total_files, total_lines

if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory_path = sys.argv[1]
    else:
        directory_path = os.getcwd()

    total_files, total_lines = count_python_files_lines(directory_path)
    print(f"Total Python files: {total_files}")
    print(f"Total lines in Python files: {total_lines}")
