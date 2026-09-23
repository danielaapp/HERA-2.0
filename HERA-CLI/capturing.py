import argparse
from collections import deque
from datetime import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from typing import Optional

import numpy as np
import pandas as pd
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

conf_file_path: Optional[str] = globals().get("conf_file_path", None)
conf_file: Optional[dict] = None

active_subprocesses: list[subprocess.Popen] = []


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


def ensure_interface() -> str:
    interface = conf_file["values"].get("interface", "").strip()
    while not interface:
        interface = input("Where do you wish to capture? (Interface name): ").strip()
        if interface:
            conf_file["values"]["interface"] = interface
            save_config()
            break
        print("[!] Interface name cannot be empty.")
    return interface


def ensure_interval() -> str:
    global conf_file

    interval_val = str(conf_file["values"].get("interval", "")).strip()
    while not interval_val:
        interval_val = input("Enter capture interval in seconds: ").strip()
        if interval_val:
            conf_file["values"]["interval"] = interval_val
            save_config()
            print(f"[+] 'interval' set and saved as: {interval_val}")
            break
        print("[!] Interval cannot be empty.")

    return interval_val


def ensure_client_and_man() -> tuple[str, str]:
    global conf_file

    client_val = conf_file["values"].get("client", "").strip()
    while not client_val:
        client_val = input("Enter client (ra or racluster): ").strip()
        if client_val:
            conf_file["values"]["client"] = client_val
            save_config()
            print(f"[+] 'client' set and saved as: {client_val}")
            break
        print("[!] Client value cannot be empty.")

    man_val = conf_file["values"].get("man", "").strip()
    while not man_val:
        man_val = input("Enter if you want management flows (man or noman): ").strip()
        if man_val:
            conf_file["values"]["man"] = man_val
            save_config()
            print(f"[+] 'man' set and saved as: {man_val}")
            break
        print("[!] Man value cannot be empty.")

    return client_val, man_val


# ------------------ Process Termination ------------------


def kill_all_capture_processes():
    print("\n[*] Terminating capture processes...")
    for proc in active_subprocesses:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    for binary in ["argus", "rasplit", "tshark"]:
        try:
            subprocess.run(["sudo", "pkill", "-9", "-f", binary], stderr=subprocess.DEVNULL)
        except Exception:
            pass


# ------------------ Non-Realtime Capture (tshark) ------------------


def run_tshark_capture() -> None:
    interface = ensure_interface()
    ensure_valid_folder(["pcap"])

    pcap_dir = conf_file["paths"]["pcap"]
    filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.pcapng")
    capture_file = os.path.join(pcap_dir, filename)

    cmd = ["tshark", "-i", interface, "-w", capture_file]
    print(f"\n[+] Starting capture on '{interface}' -> {capture_file}")
    print("[+] Press Ctrl+C to Stop & Save capture...")

    proc = subprocess.Popen(cmd)
    active_subprocesses.append(proc)

    try:
        proc.wait()
    except KeyboardInterrupt:
        kill_all_capture_processes()
        print(f"[+] Capture stopped and saved to: {capture_file}")


# ------------------ Realtime Capture (argus/rasplit) ------------------


def run_realtime_capture() -> None:
    ensure_valid_folder(["flow", "csv"])
    interface = ensure_interface()
    client_bin, man_bin = ensure_client_and_man()
    interval = ensure_interval()

    hera_path = os.path.abspath(conf_file["paths"]["flow"])
    csv_folder = os.path.abspath(conf_file["paths"]["csv"])

    argus_args = [item.split(" | ")[0] for item in conf_file["values"].get("argus", [])]
    features_selector = conf_file["values"].get("features", [])

    calculated_features = ["Ssaddr", "Sdaddr"]
    calculated_features_dict = {"Ssaddr": "saddr, sport", "Sdaddr": "daddr, dport"}

    features_string = "rank stime ltime proto saddr sport daddr dport"
    calculated_features_array = []

    for feature in features_selector:
        if feature not in calculated_features:
            features_string += f" {feature}"
        else:
            calculated_features_array.append(feature)

    def calculate_features(valid_hera_path: str) -> Optional[pd.DataFrame]:
        cmd_n = [
            client_bin, "-n", "-M", man_bin, "-u", "-r", valid_hera_path,
            "-c", ",", "-s", features_string,
        ]
        features_n = subprocess.run(cmd_n, capture_output=True, text=True)
        lines_nf = [line.strip() for line in features_n.stdout.strip().split("\n") if line.strip()]

        if len(lines_nf) <= 1:
            if features_n.stderr.strip():
                print(f"[!] '{client_bin}' error: {features_n.stderr.strip()}")
            return None

        cols = [c.strip() for c in lines_nf[0].split(",")]
        data_nf = [
            [f.strip() if f.strip() else np.nan for f in line.split(",")]
            for line in lines_nf[1:]
        ]
        features_df = pd.DataFrame(data_nf, columns=cols)

        cmd_id = [
            client_bin, "-n", "-M", man_bin, "-u", "-r", valid_hera_path,
            "-c", ",", "-s", "daddr, saddr, dport, sport, proto",
        ]
        features_id = subprocess.run(cmd_id, capture_output=True, text=True)
        lines_id = [line.strip() for line in features_id.stdout.strip().split("\n") if line.strip()]

        if len(lines_id) > 1:
            data_id = [
                "-".join(["nan" if f.strip() == "" else f.strip() for f in line.split(",")])
                for line in lines_id[1:]
            ]
            features_df.insert(0, "FlowID", data_id)

        for calc_feat in calculated_features_array:
            cmd_calc = [
                client_bin, "-n", "-M", man_bin, "-u", "-r", valid_hera_path,
                "-c", ",", "-s", calculated_features_dict[calc_feat],
            ]
            res = subprocess.run(cmd_calc, capture_output=True, text=True)
            lines = [l.strip() for l in res.stdout.strip().split("\n") if l.strip()]

            if len(lines) < 2:
                continue

            column_titles = [c.strip() for c in lines[0].split(",")]
            service_count = [
                parts for line in lines[1:] if len(parts := line.split(",")) >= 2
            ]

            df = pd.DataFrame(service_count, columns=column_titles)
            features_df[calc_feat] = (
                df.groupby([df.columns[0], df.columns[1]])[df.columns[0]]
                .transform("count")
                .astype(pd.Int64Dtype())
            )

        return features_df

    class HeraFileHandler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self.processing_lock = threading.Lock()

        def is_file_ready(self, filepath: str, max_wait: int = 15) -> bool:
            last_size = -1
            checks = 0
            while checks < max_wait:
                if not os.path.exists(filepath):
                    return False
                try:
                    size = os.path.getsize(filepath)
                except OSError:
                    return False

                if size > 0 and size == last_size:
                    return True

                last_size = size
                time.sleep(1)
                checks += 1
            return False

        def remove_file_safely(self, filepath: str, retries: int = 5, delay: float = 2.0):
            for _ in range(retries):
                try:
                    os.remove(filepath)
                    print(f"[-] Cleaned up chunk: {filepath}")
                    return
                except OSError as e:
                    if e.errno == 26:  
                        time.sleep(delay)
                    else:
                        break

            res = subprocess.run(["sudo", "rm", "-f", filepath], stderr=subprocess.DEVNULL)
            if res.returncode == 0 and not os.path.exists(filepath):
                print(f"[-] Cleaned up chunk (forced): {filepath}")
            else:
                print(f"[!] Warning: Could not delete raw file: {filepath}")

        def on_created(self, event):
            if event.is_directory:
                return
            filename = os.path.basename(event.src_path)
            if filename.endswith(".hera") and filename.startswith("split"):
                print(f"[+] Detected incoming chunk: {filename}")
                threading.Thread(target=self.process_file, args=(event.src_path,), daemon=True).start()

        def process_file(self, filepath: str):
            with self.processing_lock:
                self.is_file_ready(filepath)
                try:
                    features_df = calculate_features(filepath)
                    if features_df is not None and not features_df.empty:
                        csv_file_name = os.path.basename(filepath).replace(".hera", ".csv")
                        csv_path = os.path.join(csv_folder, csv_file_name)
                        features_df.to_csv(csv_path, index=False)
                        print(f"[✓] Saved CSV: {csv_path}")

                        self.remove_file_safely(filepath)
                    else:
                        print(f"[!] No valid records found in: {filepath}")
                except Exception as e:
                    print(f"[!] Failed to process chunk {filepath}: {e}")

    argus_cmd = [
        "sudo", "argus", "-i", str(interface), "-P", "561", "-S", str(interval)
    ] + argus_args
    print(f"[+] Starting Argus on port 561 (Interface: {interface}, Interval: {interval}s)...")
    argus_proc = subprocess.Popen(argus_cmd)
    active_subprocesses.append(argus_proc)

    time.sleep(2)

    pattern = os.path.join(hera_path, "split.%Y_%m_%d_%H_%M_%S.hera")
    rasplit_cmd = [
        "sudo", "rasplit", "-M", "time", "1m", "-S", "localhost:561", "-w", pattern
    ]
    print("[+] Starting Rasplit (1-minute chunks)...")
    rasplit_proc = subprocess.Popen(rasplit_cmd)
    active_subprocesses.append(rasplit_proc)

    event_handler = HeraFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path=hera_path, recursive=False)
    observer.start()

    print("\n[+] Real-time monitoring active. (Chunks generate every 1 minute).")
    print("[+] Press Ctrl+C at any time to terminate cleanly.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
        kill_all_capture_processes()


# ------------------ Main Flow & CLI ------------------


def interactive_flow() -> None:
    print("\n--- Network Traffic Capture Step ---")
    while True:
        capture_choice = input("Do you want to capture traffic? (y/n): ").strip().lower()
        if capture_choice in ("y", "yes"):
            break
        elif capture_choice in ("n", "no"):
            print("[+] Skipping traffic capture. Checking PCAP folder availability...")
            ensure_valid_folder(["pcap"])
            print("[+] Step completed.")
            return
        else:
            print("[!] Please enter 'y' or 'n'.")

    while True:
        realtime_choice = input("Do you want real-time processing of traffic? (y/n): ").strip().lower()
        if realtime_choice in ("y", "yes"):
            run_realtime_capture()
            break
        elif realtime_choice in ("n", "no"):
            run_tshark_capture()
            break
        else:
            print("[!] Please enter 'y' or 'n'.")


def main() -> None:
    global conf_file_path

    signal.signal(signal.SIGTERM, lambda s, f: (kill_all_capture_processes(), sys.exit(0)))

    parser = argparse.ArgumentParser(description="Traffic Capturing Component (CLI)")
    parser.add_argument("-c", "--config", type=str, help="Path to configuration.json")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--skip-capture", action="store_true", help="Skip capturing and validate PCAP path")
    mode_group.add_argument("--realtime", action="store_true", help="Start real-time capture and flow feature extraction")
    mode_group.add_argument("--pcap-only", action="store_true", help="Start standard tshark pcap capture")

    args, _ = parser.parse_known_args()

    if args.config:
        conf_file_path = os.path.abspath(args.config)

    load_config()

    if args.skip_capture:
        ensure_valid_folder(["pcap"])
    elif args.realtime:
        run_realtime_capture()
    elif args.pcap_only:
        run_tshark_capture()
    else:
        interactive_flow()


if __name__ == "__main__":
    main()