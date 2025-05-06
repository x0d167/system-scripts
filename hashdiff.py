from pathlib import Path
import hashlib
import argparse
import difflib
from colorama import init, Fore, Style

init(autoreset=True)


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
    parser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        help="Show line by line diffs of files with changes",
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


def file_by_file_hash(archive, active, diff=False):
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
            print(f"{Fore.GREEN}New file: {path}")
        elif path not in active_files:
            print(f"{Fore.RED}Deleted file: {path}")
        else:
            a_hash = compute_file_hash(archive_files[path])
            b_hash = compute_file_hash(active_files[path])
            if a_hash != b_hash:
                print(f"{Fore.YELLOW}Modified file: {path}")
                if diff:
                    print_diff(archive_files[path], active_files[path])


def print_diff(file1, file2):
    try:
        with open(file1) as f1, open(file2) as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
    except UnicodeDecodeError:
        print(" (binary or non-text file, skipping diff)\n")
        return

    diff = difflib.unified_diff(
        lines1, lines2, fromfile=str(file1.name), tofile=str(file2.name), lineterm=""
    )
    for line in diff:
        if line.startswith("---") or line.startswith("+++"):
            color = Fore.CYAN
        elif line.startswith("@@"):
            color = Fore.MAGENTA
        elif line.startswith("-"):
            color = Fore.RED
        elif line.startswith("+"):
            color = Fore.GREEN
        else:
            color = Style.RESET_ALL
        print("  " + color + line.rstrip())


def main():
    args = parse_args()

    source = args.source
    target = args.target
    verbose = args.verbose
    diff = args.diff

    # archive_dot = Path.home() / "archive" / ".dotfiles"
    # active_dot = Path.home() / ".dotfiles"

    if source.is_file() and target.is_file():
        hash_source = compute_file_hash(source)
        hash_target = compute_file_hash(target)

        print(f"Source: {hash_source}\nTarget: {hash_target}")
        if hash_source == hash_target:
            print(Style.BRIGHT + Fore.GREEN + "Files are identical")
        else:
            print(Style.BRIGHT + Fore.RED + "Files have drifted")
            if diff:
                print_diff(source, target)

    elif source.is_dir() and target.is_dir():
        hash_source = compute_dir_hash(source)
        hash_target = compute_dir_hash(target)

        print(f"Source: {hash_source}\nTarget: {hash_target}")
        if hash_source == hash_target:
            print(Style.BRIGHT + Fore.GREEN + "Directories are identical")
        else:
            print(Style.BRIGHT + Fore.RED + "Directories have drifted")
            if verbose:
                file_by_file_hash(source, target, diff)

    else:
        print("Error: Source and Target must both be files or both be directories")


if __name__ == "__main__":
    main()
