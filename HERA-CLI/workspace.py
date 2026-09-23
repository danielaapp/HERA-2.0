import os
import sys
import json
import argparse
from typing import Optional

DEFAULT_TEMPLATE = {
    "paths": {
        "pcap": "",
        "flow": "",
        "csv": "",
        "truth": ""
    },
    "values": {
        "interface": "",
        "argus": [],
        "interval": "",
        "features": [],
        "client": "",
        "man": ""
    }
}

conf_file_path: Optional[str] = None


def create_default_config(directory: str) -> str:
    target_dir = os.path.abspath(directory.strip())
    if not os.path.isdir(target_dir):
        raise ValueError(f"Invalid directory path: '{target_dir}' does not exist or is not a directory.")

    file_path = os.path.join(target_dir, "configuration.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_TEMPLATE, f, indent=2)

    print(f"[+] New configuration file created at: {file_path}")
    return file_path


def validate_existing_config(path: str) -> str:
    clean_path = os.path.abspath(path.strip())
    if not os.path.isfile(clean_path):
        raise ValueError(f"File not found: '{clean_path}'")
    if not clean_path.lower().endswith(".json"):
        raise ValueError(f"File must be a JSON file (.json): '{clean_path}'")
    
    print(f"[+] Configuration file loaded: {clean_path}")
    return clean_path


def interactive_mode() -> str:
    print("--- Workspace Setup ---")
    while True:
        choice = input("Do you have a configuration file? (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            while True:
                path = input("Enter path to configuration file: ").strip()
                try:
                    return validate_existing_config(path)
                except ValueError as err:
                    print(f"Error: {err}. Please try again.")

        elif choice in ("n", "no"):
            while True:
                dir_path = input("Enter folder path where 'configuration.json' should be created: ").strip()
                try:
                    return create_default_config(dir_path)
                except ValueError as err:
                    print(f"Error: {err}. Please try again.")
        else:
            print("Invalid input. Please enter 'y' or 'n'.")


def main() -> None:
    global conf_file_path

    parser = argparse.ArgumentParser(description="Workspace and Configuration Manager")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--config", type=str, help="Path to existing configuration JSON file")
    group.add_argument("-n", "--new", type=str, metavar="DIR", help="Directory where a new configuration.json will be generated")

    args, _ = parser.parse_known_args()

    if args.config:
        conf_file_path = validate_existing_config(args.config)
    elif args.new:
        conf_file_path = create_default_config(args.new)
    else:
        conf_file_path = interactive_mode()


if __name__ == "__main__":
    main()