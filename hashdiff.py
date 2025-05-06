from pathlib import Path
import hashlib
import argparse


def parse_args():
    """Add CLI args for modifying how the script runs"""
    parser = argparse.ArgumentParser(
        description="Compare two directories or files for drift"
    )
    parser.add_argument(
        "source", type=Path, help="Path to the source directory or file"
    )
    parser.add_argument(
        "target", type=Path, help="Path to the target directory or file"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Print detailed file-by-file drift"
    )

    return parser.parse_args()


def compute_file_hash(file_path, algorithm="sha256"):
    """Compute the hash of a file using sha256"""
    hash = hashlib.new(algorithm)

    with open(file_path, "rb") as file:
        # Read the file in chunks of 8192 bytes
        while chunk := file.read(8192):
            hash.update(chunk)

    return hash.hexdigest()


def compute_dir_hash(directory):
    """Given file path, compute the hash of every file recursively"""

    hasher = hashlib.sha256()
    ignore_dirs = {".git"}
    ignore_files = {".gitignore", "lazy-lock.json"}

    for file in sorted(directory.rglob("*")):
        if any(part in ignore_dirs for part in file.parts):
            continue
        if file.is_file() and file.name not in ignore_files:
            # Get relative file path
            relative_path = file.relative_to(directory)
            # encode that path into the hasher
            hasher.update(str(relative_path).encode("utf-8"))

            # Now proceed with normal reading of files
            with open(file, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)

    return hasher.hexdigest()


def file_by_file_hash(archive, active):
    """Compute file by file hash for granular comparison"""

    ignore_dirs = {".git"}
    ignore_files = {".gitignore", "lazy-lock.json"}

    archive_files = {}
    for file in sorted(archive.rglob("*")):
        if any(part in ignore_dirs for part in file.parts):
            continue
        if file.is_file() and file.name not in ignore_files:
            relative_path = file.relative_to(archive)
            archive_files[relative_path] = file

    active_files = {}
    for file in sorted(active.rglob("*")):
        if any(part in ignore_dirs for part in file.parts):
            continue
        if file.is_file() and file.name not in ignore_files:
            relative_path = file.relative_to(active)
            active_files[relative_path] = file

    all_paths = set(archive_files) | set(active_files)

    for path in all_paths:
        if path not in archive_files:
            print(f"New file: {path}")
        elif path not in active_files:
            print(f"Deleted file: {path}")
        else:
            a_hash = compute_file_hash(archive_files[path])
            b_hash = compute_file_hash(active_files[path])
            if a_hash != b_hash:
                print(f"Modified file: {path}")


def main():
    args = parse_args()

    source = args.source
    target = args.target
    verbose = args.verbose

    # archive_dot = Path.home() / "archive" / ".dotfiles"
    # active_dot = Path.home() / ".dotfiles"

    if source.is_file() and target.is_file():
        hash_source = compute_file_hash(source)
        hash_target = compute_file_hash(target)

        print(f"Source: {hash_source}\nTarget: {hash_target}")
        if hash_source == hash_target:
            print("Files are identical")
        else:
            print("Files have drifted")

    elif source.is_dir() and target.is_dir():
        hash_source = compute_dir_hash(source)
        hash_target = compute_dir_hash(target)

        print(f"Source: {hash_source}\nTarget: {hash_target}")
        if hash_source == hash_target:
            print("Directories are identical")
        else:
            print("Directories have drifted")
            if verbose:
                file_by_file_hash(source, target)

    else:
        print("Error: Source and Target must both be files or both be directories")


if __name__ == "__main__":
    main()
