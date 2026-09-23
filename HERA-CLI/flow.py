import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Optional

conf_file_path: Optional[str] = globals().get("conf_file_path", None)
conf_file: Optional[dict] = None

ARGUS_FIELDS = [
    "-A | Generate application byte metrics in each audit record.",
    "-O | Turn off Berkeley Packet Filter optimizer. If you think it generates bad code.",
    "-Z | Collect packet size information for all flows (to generate mean, max, min and standard deviation).",
    "-J | Generate packet performance (jitter) data in each audit record.",
    "-m | Provide MAC address information in argus records.",
    "-R | Generate argus records such that response times can be derived from transaction data.",
]

DEFAULT_ARGUS_CHOICES = [0, 2, 3]  # Indexes for -A, -Z, -J


# ------------------ Config & Path Helpers ------------------


def load_config() -> dict:
    global conf_file, conf_file_path

    if not conf_file_path:
        while True:
            candidate = input("Enter path to configuration JSON file: ").strip()
            if os.path.isfile(candidate) and candidate.lower().endswith(".json"):
                conf_file_path = os.path.abspath(candidate)
                break
            print("[!] File not found or invalid format. Must be a .json file.")

    with open(conf_file_path, "r", encoding="utf-8") as f:
        conf_file = json.load(f)

    return conf_file


def save_config() -> None:
    if conf_file and conf_file_path:
        with open(conf_file_path, "w", encoding="utf-8") as f:
            json.dump(conf_file, f, indent=2)


def ensure_valid_folder(paths_to_check: list[str]) -> None:
    global conf_file

    for key in paths_to_check:
        current_path = conf_file["paths"].get(key, "").strip()

        while not (current_path and os.path.isdir(current_path)):
            print(f"[!] Path for '{key}' is invalid or empty: '{current_path}'")
            current_path = input(f"Please enter a valid directory for {key.upper()}: ").strip()
            if os.path.isdir(current_path):
                conf_file["paths"][key] = os.path.abspath(current_path)
                save_config()
                print(f"[+] Updated configuration: {key} -> {conf_file['paths'][key]}")
                break
            print(f"[!] Directory '{current_path}' does not exist.")


def ensure_interval() -> int:
    global conf_file

    val = conf_file["values"].get("interval")
    while True:
        if val is not None and str(val).strip() != "":
            try:
                int_val = int(val)
                if int_val >= 0:
                    return int_val
            except ValueError:
                pass
        
        user_input = input("Enter flow interval in seconds [Default: 60]: ").strip()
        if not user_input:
            val = 60
        else:
            try:
                val = int(user_input)
                if val < 0:
                    print("[!] Value must be a non-negative integer.")
                    val = None
            except ValueError:
                print("[!] Please enter a valid integer.")
                val = None

        if val is not None:
            conf_file["values"]["interval"] = val
            save_config()
            print(f"[+] 'interval' set and saved as: {val}")
            return val


def ensure_argus_flags() -> list[str]:
    global conf_file

    argus = conf_file["values"].get("argus", [])
    if argus and len(argus) > 0:
        return argus

    print("\n--- Select Argus Fields to generate HERA flow files ---")
    for idx, field in enumerate(ARGUS_FIELDS):
        default_tag = " (default)" if idx in DEFAULT_ARGUS_CHOICES else ""
        print(f"  [{idx + 1}] {field}{default_tag}")

    prompt = input("\nEnter choice numbers separated by commas [Press Enter for defaults 1,3,4]: ").strip()

    selected = []
    if not prompt:
        selected = [ARGUS_FIELDS[i] for i in DEFAULT_ARGUS_CHOICES]
    else:
        for part in prompt.split(","):
            part = part.strip()
            if part.isdigit():
                num = int(part) - 1
                if 0 <= num < len(ARGUS_FIELDS):
                    selected.append(ARGUS_FIELDS[num])

    if not selected:
        print("[!] No valid selection made. Falling back to defaults (-A, -Z, -J).")
        selected = [ARGUS_FIELDS[i] for i in DEFAULT_ARGUS_CHOICES]

    conf_file["values"]["argus"] = selected
    save_config()
    print("[+] Argus fields set and saved.")
    return selected


# ------------------ Flow Extraction ------------------


def extract_flows() -> None:
    pcap_dir = os.path.abspath(conf_file["paths"]["pcap"])
    hera_dir = os.path.abspath(conf_file["paths"]["flow"])

    s_value = conf_file["values"]["interval"]
    argus_args = [item.split(" | ")[0] for item in conf_file["values"]["argus"]]

    if not shutil.which("argus"):
        print("[!] ERROR: 'argus' binary was not found in PATH.")
        print("    Install Argus (e.g., sudo apt install argus-server) before running.")
        sys.exit(1)

    pcap_files = [
        f for f in os.listdir(pcap_dir)
        if f.endswith(".pcap") or f.endswith(".pcapng")
    ]

    if not pcap_files:
        print(f"[!] No .pcap or .pcapng files found in: {pcap_dir}")
        return

    print(f"\n[+] Found {len(pcap_files)} PCAP file(s) to process.")
    for pcap_file in pcap_files:
        in_path = os.path.join(pcap_dir, pcap_file)
        base_name = os.path.splitext(pcap_file)[0]
        out_path = os.path.join(hera_dir, f"{base_name}.hera")

        print(f"[+] Processing: {pcap_file} -> {os.path.basename(out_path)}")

        cmd = ["argus", "-S", str(s_value)] + argus_args + ["-r", in_path, "-w", out_path]

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[!] Error running Argus on {pcap_file}: {res.stderr.strip()}")
        else:
            print(f"[✓] Generated: {out_path}")

    print("\n[✓] Flow generation complete! Proceed to the next step.")


# ------------------ Main Flow & CLI ------------------


def main() -> None:
    global conf_file_path

    parser = argparse.ArgumentParser(description="Flow File Generation Component (CLI)")
    parser.add_argument("-c", "--config", type=str, help="Path to configuration.json")
    parser.add_argument("-i", "--interval", type=int, help="Override Argus flow interval (seconds)")

    args, _ = parser.parse_known_args()

    if args.config:
        conf_file_path = os.path.abspath(args.config)

    load_config()

    if args.interval is not None:
        if args.interval >= 0:
            conf_file["values"]["interval"] = args.interval
            save_config()
        else:
            print("[!] Provided interval cannot be negative. Prompting...")

    # Validate needed directories
    ensure_valid_folder(["pcap", "flow", "csv"])

    # Validate needed values
    ensure_interval()
    ensure_argus_flags()

    # Run batch conversion
    extract_flows()


if __name__ == "__main__":
    main()