import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Optional

import numpy as np
import pandas as pd

conf_file_path: Optional[str] = globals().get("conf_file_path", None)
conf_file: Optional[dict] = None

# ------------------ Feature Definitions & Presets ------------------

ALL_FEATURES = [
    "srcid", "trans", "flgs", "seq", "dur", "runtime", "idle", "mean", "stddev", "sum",
    "min", "max", "smac", "dmac", "soui", "doui", "stos", "dtos", "sdsb", "ddsb",
    "sco", "dco", "sttl", "dttl", "shops", "dhops", "sipid", "dipid", "smpls", "dmpls",
    "autoid", "sas", "das", "ias", "cause", "nstroke", "snstroke", "dnstroke", "pkts",
    "spkts", "dpkts", "bytes", "sbytes", "dbytes", "appbytes", "sappbytes", "dappbytes",
    "pcr", "load", "sload", "dload", "loss", "sloss", "dloss", "ploss", "psloss", "pdloss",
    "retrans", "sretrans", "dretrans", "pretrans", "psretrans", "pdretrans", "sgap", "dgap",
    "rate", "srate", "drate", "dir", "sintpkt", "sintpktmin", "sintpktmax", "sintdist",
    "sintpktact", "sintdistact", "sintpktidl", "sintdistidl", "dintpkt", "dintpktmin",
    "dintpktmax", "dintdist", "dintpktact", "dintdistact", "dintpktidl", "dintdistidl",
    "sjit", "sjitact", "sjitidle", "djit", "djitact", "djitidle", "state", "label",
    "suser", "duser", "swin", "dwin", "svlan", "dvlan", "svid", "dvid", "svpri", "dvpri",
    "srng", "erng", "stcpb", "dtcpb", "tcprtt", "synack", "ackdat", "tcpopt", "inode",
    "offset", "smeansz", "dmeansz", "spktsz", "smaxsz", "dpktsz", "dmaxsz", "sminsz",
    "dminsz", "Ssaddr", "Sdaddr"
]

FEATURE_PRESETS = {
    "default": [
        "bytes", "sbytes", "dbytes", "pkts", "spkts", "dpkts", "dur",
        "runtime", "idle", "flgs", "tcpopt", "Ssaddr", "Sdaddr"
    ],
    "cic10": [
        "sintpkt", "sintpktmax", "sintpktmin", "dintpkt", "dintpktmax",
        "dintpktmin", "mean", "stddev", "max", "min"
    ],
    "unswnb15": [
        "state", "dur", "sbytes", "dbytes", "sttl", "dttl", "sloss", "dloss",
        "sload", "dload", "spkts", "dpkts", "swin", "dwin", "stcpb", "dtcpb",
        "smeansz", "dmeansz", "sjit", "djit", "sintpkt", "dintpkt", "tcprtt",
        "synack", "ackdat"
    ],
    "botiot": [
        "flgs", "pkts", "bytes", "state", "seq", "dur", "mean", "stddev",
        "smac", "dmac", "sum", "min", "max", "soui", "doui", "sco", "dco",
        "spkts", "dpkts", "sbytes", "dbytes", "rate", "srate", "drate"
    ],
    "genis": [
        "trans", "flgs", "seq", "dur", "runtime", "idle", "mean", "stddev",
        "sum", "min", "max", "smac", "dmac", "soui", "doui", "stos", "dtos",
        "sdsb", "ddsb", "sco", "dco", "sttl", "dttl", "shops", "dhops",
        "sipid", "dipid", "smpls", "dmpls", "autoid", "sas", "das", "ias",
        "cause", "nstroke", "snstroke", "dnstroke", "pkts", "spkts", "dpkts",
        "bytes", "sbytes", "dbytes", "appbytes", "sappbytes", "dappbytes",
        "pcr", "load", "sload", "dload", "loss", "sloss", "dloss", "ploss",
        "retrans", "sretrans", "dretrans", "pretrans", "sgap", "dgap", "rate",
        "srate", "drate", "dir", "sintpkt", "sintpktmin", "sintpktmax",
        "sintdist", "sintpktact", "sintdistact", "sintpktidl", "sintdistidl",
        "dintpkt", "dintpktmin", "dintpktmax", "dintdist", "dintpktact",
        "dintdistact", "dintpktidl", "dintdistidl", "sjit", "sjitact", "djit",
        "djitact", "state", "suser", "duser", "swin", "dwin", "svlan", "dvlan",
        "svid", "dvid", "svpri", "dvpri", "srng", "erng", "stcpb", "dtcpb",
        "tcprtt", "synack", "ackdat", "tcpopt", "inode", "offset", "smeansz",
        "dmeansz", "smaxsz", "dmaxsz", "sminsz", "dminsz", "Ssaddr", "Sdaddr"
    ],
    "all": ALL_FEATURES
}

CLIENT_OPTIONS = ["ra", "racluster"]
MAN_OPTIONS = ["noman", "man"]


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


def ensure_features() -> list[str]:
    global conf_file

    features = conf_file["values"].get("features", [])
    if features and len(features) > 0:
        return features

    print("\n--- Select Feature Preset for Dataset Creation ---")
    print("  [1] Default Features (13 features)")
    print("  [2] CIC 10 Features (10 features)")
    print("  [3] UNSW-NB15 Features (25 features)")
    print("  [4] Bot-IoT Features (24 features)")
    print("  [5] GeNIS Features (106 features)")
    print("  [6] All Available Features (115 features)")
    print("  [7] Custom input (comma-separated feature names)")

    while True:
        choice = input("\nEnter choice [1-7] (Default: 1): ").strip()
        if choice in ("", "1"):
            selected = FEATURE_PRESETS["default"]
            break
        elif choice == "2":
            selected = FEATURE_PRESETS["cic10"]
            break
        elif choice == "3":
            selected = FEATURE_PRESETS["unswnb15"]
            break
        elif choice == "4":
            selected = FEATURE_PRESETS["botiot"]
            break
        elif choice == "5":
            selected = FEATURE_PRESETS["genis"]
            break
        elif choice == "6":
            selected = FEATURE_PRESETS["all"]
            break
        elif choice == "7":
            custom_input = input("Enter feature names separated by commas: ").strip()
            selected = [f.strip() for f in custom_input.split(",") if f.strip()]
            if selected:
                break
            print("[!] No valid features entered.")
        else:
            print("[!] Invalid option. Please enter a number between 1 and 7.")

    conf_file["values"]["features"] = selected
    save_config()
    print(f"[+] Features set and saved ({len(selected)} features).")
    return selected


def ensure_client() -> str:
    global conf_file

    client_val = conf_file["values"].get("client", "").strip()
    if client_val:
        return client_val

    print("\n--- Select Argus Client Binary ---")
    for idx, opt in enumerate(CLIENT_OPTIONS, 1):
        print(f"  [{idx}] {opt}")

    while True:
        choice = input(f"Enter choice [1-{len(CLIENT_OPTIONS)}] (Default: 1 - 'ra'): ").strip()
        if choice in ("", "1"):
            client_val = CLIENT_OPTIONS[0]
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(CLIENT_OPTIONS):
            client_val = CLIENT_OPTIONS[int(choice) - 1]
            break
        elif choice in CLIENT_OPTIONS:
            client_val = choice
            break
        print("[!] Invalid selection.")

    conf_file["values"]["client"] = client_val
    save_config()
    print(f"[+] 'client' set and saved as: {client_val}")
    return client_val


def ensure_man() -> str:
    global conf_file

    man_val = conf_file["values"].get("man", "").strip()
    if man_val:
        return man_val

    print("\n--- Select Argus Mode / Configuration ('man') ---")
    for idx, opt in enumerate(MAN_OPTIONS, 1):
        print(f"  [{idx}] {opt}")

    while True:
        choice = input(f"Enter choice [1-{len(MAN_OPTIONS)}] (Default: 1 - 'noman'): ").strip()
        if choice in ("", "1"):
            man_val = MAN_OPTIONS[0]
            break
        elif choice.isdigit() and 1 <= int(choice) <= len(MAN_OPTIONS):
            man_val = MAN_OPTIONS[int(choice) - 1]
            break
        elif choice in MAN_OPTIONS:
            man_val = choice
            break
        print("[!] Invalid selection.")

    conf_file["values"]["man"] = man_val
    save_config()
    print(f"[+] 'man' set and saved as: {man_val}")
    return man_val


# ------------------ Feature Extraction ------------------


def extract_dataset() -> None:
    client_bin = ensure_client()
    man_val = ensure_man()
    features_list = ensure_features()

    if not shutil.which(client_bin):
        print(f"[!] ERROR: '{client_bin}' binary was not found in PATH.")
        sys.exit(1)

    hera_dir = os.path.abspath(conf_file["paths"]["flow"])
    csv_dir = os.path.abspath(conf_file["paths"]["csv"])

    calculated_features = ["Ssaddr", "Sdaddr"]
    calculated_features_dict = {"Ssaddr": "saddr, sport", "Sdaddr": "daddr, dport"}

    features_string = "rank stime ltime proto saddr sport daddr dport"
    calculated_features_array = []

    for feature in features_list:
        if feature not in calculated_features:
            features_string += f" {feature}"
        else:
            calculated_features_array.append(feature)

    def calculate_features(hera_file_path: str) -> Optional[pd.DataFrame]:
        cmd_n = [
            client_bin, "-n", "-M", man_val, "-u", "-r", hera_file_path,
            "-c", ",", "-s", features_string
        ]
        features_n = subprocess.run(cmd_n, capture_output=True, text=True)
        lines_nf = [line.strip() for line in features_n.stdout.strip().split("\n") if line.strip()]

        if len(lines_nf) <= 1:
            if features_n.stderr.strip():
                print(f"[!] Error in {client_bin}: {features_n.stderr.strip()}")
            return None

        cols = [c.strip() for c in lines_nf[0].split(",")]
        data_nf = [
            [f.strip() if f.strip() else np.nan for f in line.split(",")]
            for line in lines_nf[1:]
        ]
        features_df = pd.DataFrame(data_nf, columns=cols)

        cmd_id = [
            client_bin, "-n", "-M", man_val, "-u", "-r", hera_file_path,
            "-c", ",", "-s", "daddr, saddr, dport, sport, proto"
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
                client_bin, "-n", "-M", man_val, "-u", "-r", hera_file_path,
                "-c", ",", "-s", calculated_features_dict[calc_feat]
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

    hera_files = [f for f in os.listdir(hera_dir) if f.endswith(".hera")]
    if not hera_files:
        print(f"[!] No .hera files found in: {hera_dir}")
        return

    print(f"\n[+] Found {len(hera_files)} .hera file(s) to process.")

    for hera_file in hera_files:
        base_name = os.path.splitext(hera_file)[0]
        csv_filename = f"{client_bin}_{base_name}.csv"
        csv_full_path = os.path.join(csv_dir, csv_filename)
        hera_full_path = os.path.join(hera_dir, hera_file)

        if not os.path.exists(csv_full_path):
            print(f"[+] Extracting features from: {hera_file}")
            df = calculate_features(hera_full_path)
            if df is not None and not df.empty:
                df.to_csv(csv_full_path, index=False)
                print(f"[✓] Features extracted to CSV: {csv_full_path}")

                # Optional racount audit summary
                racount_path = os.path.join(csv_dir, f"racount_{base_name}.txt")
                if shutil.which("racount"):
                    with open(racount_path, "w") as out_f:
                        subprocess.run(
                            ["racount", "-r", hera_full_path, "-M", "addr", "proto"],
                            stdout=out_f,
                            stderr=subprocess.DEVNULL
                        )
            else:
                print(f"[!] No records extracted from {hera_file}")
        else:
            print(f"[*] File already exists, skipping: {csv_filename}")

    print("\n[✓] Dataset creation complete! Proceed to the labelling component.")


# ------------------ Main Flow & CLI ------------------


def main() -> None:
    global conf_file_path

    parser = argparse.ArgumentParser(description="Dataset Creation Component (CLI)")
    parser.add_argument("-c", "--config", type=str, help="Path to configuration.json")
    parser.add_argument(
        "--preset",
        choices=["default", "cic10", "unswnb15", "botiot", "genis", "all"],
        help="Feature preset to use for dataset generation"
    )

    args, _ = parser.parse_known_args()

    if args.config:
        conf_file_path = os.path.abspath(args.config)

    load_config()

    if args.preset:
        conf_file["values"]["features"] = FEATURE_PRESETS[args.preset]
        save_config()

    ensure_valid_folder(["flow", "csv"])
    ensure_features()
    ensure_client()
    ensure_man()

    extract_dataset()


if __name__ == "__main__":
    main()