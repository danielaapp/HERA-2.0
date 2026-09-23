import argparse
import json
import os
import sys
from typing import Optional

import pandas as pd

conf_file_path: Optional[str] = globals().get("conf_file_path", None)
conf_file: Optional[dict] = None


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


def ensure_truth_file() -> str:
    global conf_file

    truth_val = conf_file["paths"].get("truth", "")
    if truth_val:
        truth_val = truth_val.strip()

    while not (truth_val and os.path.isfile(truth_val) and truth_val.lower().endswith(".csv")):
        if truth_val:
            print(f"[!] Ground truth file not found or invalid: '{truth_val}'")
        truth_val = input("Enter path to ground truth CSV file: ").strip()
        if os.path.isfile(truth_val) and truth_val.lower().endswith(".csv"):
            conf_file["paths"]["truth"] = os.path.abspath(truth_val)
            save_config()
            print(f"[+] Ground truth path set and saved: {conf_file['paths']['truth']}")
            break
        print("[!] Invalid path. File must exist and end with .csv.")

    return os.path.abspath(truth_val)


# ------------------ Labelling Logic ------------------


def harmonize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_dict = {
        "stime": "StartTime",
        "ltime": "LastTime",
        "saddr": "SrcAddr",
        "daddr": "DstAddr",
        "sport": "Sport",
        "dport": "Dport",
        "proto": "Proto",
    }
    lowered_cols = {col.lower(): col for col in df.columns}
    applied_renames = {}

    for lower_key, target in rename_dict.items():
        if lower_key in lowered_cols and lowered_cols[lower_key] != target:
            applied_renames[lowered_cols[lower_key]] = target

    if applied_renames:
        df = df.rename(columns=applied_renames)
    return df


def label_dataset(data: pd.DataFrame, gt: pd.DataFrame) -> pd.DataFrame:
    data = harmonize_columns(data)
    gt = harmonize_columns(gt)

    for col in ["Sport", "Dport", "Proto"]:
        if col in data.columns:
            data[col] = data[col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        if col in gt.columns:
            gt[col] = gt[col].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)

    if "StartTime" in data.columns and "LastTime" in data.columns:
        data["StartTime"] = pd.to_numeric(data["StartTime"], errors="coerce").fillna(0).round().astype(int)
        data["LastTime"] = pd.to_numeric(data["LastTime"], errors="coerce").fillna(0).round().astype(int)

        data_start_max = data["StartTime"].max()
        data_end_min = data["LastTime"].min()

        if "StartTime" in gt.columns and not gt["StartTime"].isna().all():
            gt["StartTime"] = pd.to_numeric(gt["StartTime"], errors="coerce")
        if "LastTime" in gt.columns and not gt["LastTime"].isna().all():
            gt["LastTime"] = pd.to_numeric(gt["LastTime"], errors="coerce")

        has_gt_start = "StartTime" in gt.columns and not gt["StartTime"].isna().all()
        has_gt_last = "LastTime" in gt.columns and not gt["LastTime"].isna().all()

        if not has_gt_start and not has_gt_last:
            gt_filtered = gt
        elif not has_gt_start:
            gt_filtered = gt[(gt["LastTime"] <= data_end_min) & (gt["LastTime"] >= data_start_max)]
        elif not has_gt_last:
            gt_filtered = gt[(gt["StartTime"] >= data_start_max) & (gt["StartTime"] <= data_end_min)]
        else:
            gt_filtered = gt[(gt["StartTime"] <= data_start_max) & (gt["LastTime"] >= data_end_min)]
    else:
        gt_filtered = gt

    print(f"    - Ground Truth entries (Total: {len(gt)}, Time-Window Filtered: {len(gt_filtered)})")

    data["BinaryLabel"] = -1
    data["CategoryLabel"] = "Labelling"
    data["SubCategoryLabel"] = "Labelling"

    for row in gt_filtered.itertuples(index=False):
        gt_dict = row._asdict()

        mask = pd.Series(True, index=data.index)

        if "StartTime" in gt_dict and not pd.isna(gt_dict["StartTime"]) and "StartTime" in data.columns:
            mask &= (data["StartTime"] >= int(round(gt_dict["StartTime"])))
        if "LastTime" in gt_dict and not pd.isna(gt_dict["LastTime"]) and "LastTime" in data.columns:
            mask &= (data["LastTime"] <= int(round(gt_dict["LastTime"])))
        if "SrcAddr" in gt_dict and not pd.isna(gt_dict["SrcAddr"]) and "SrcAddr" in data.columns:
            mask &= (data["SrcAddr"] == str(gt_dict["SrcAddr"]))
        if "DstAddr" in gt_dict and not pd.isna(gt_dict["DstAddr"]) and "DstAddr" in data.columns:
            mask &= (data["DstAddr"] == str(gt_dict["DstAddr"]))
        if "Sport" in gt_dict and not pd.isna(gt_dict["Sport"]) and "Sport" in data.columns:
            mask &= (data["Sport"] == str(gt_dict["Sport"]))
        if "Dport" in gt_dict and not pd.isna(gt_dict["Dport"]) and "Dport" in data.columns:
            mask &= (data["Dport"] == str(gt_dict["Dport"]))
        if "Proto" in gt_dict and not pd.isna(gt_dict["Proto"]) and "Proto" in data.columns:
            mask &= (data["Proto"] == str(gt_dict["Proto"]))

        if "BinaryLabel" in gt_dict and not pd.isna(gt_dict["BinaryLabel"]):
            data.loc[mask, "BinaryLabel"] = gt_dict["BinaryLabel"]
        if "CategoryLabel" in gt_dict and not pd.isna(gt_dict["CategoryLabel"]):
            data.loc[mask, "CategoryLabel"] = gt_dict["CategoryLabel"]
        if "SubCategoryLabel" in gt_dict and not pd.isna(gt_dict["SubCategoryLabel"]):
            data.loc[mask, "SubCategoryLabel"] = gt_dict["SubCategoryLabel"]

    data.loc[data["BinaryLabel"] == -1, "BinaryLabel"] = 0
    data.loc[data["CategoryLabel"] == "Labelling", "CategoryLabel"] = "Benign"
    data.loc[data["SubCategoryLabel"] == "Labelling", "SubCategoryLabel"] = "Benign"

    return data


def run_labelling() -> None:
    ensure_valid_folder(["csv"])
    truth_file_path = ensure_truth_file()
    csv_dir = os.path.abspath(conf_file["paths"]["csv"])

    print(f"\n[+] Loading Ground Truth: {truth_file_path}")
    gt = pd.read_csv(
        truth_file_path,
        dtype={"Sport": "object", "Dport": "object", "sport": "object", "dport": "object"},
        low_memory=False,
    )

    csv_candidates = [
        f for f in os.listdir(csv_dir)
        if f.endswith(".csv") and not f.endswith("_labelled.csv")
    ]

    if not csv_candidates:
        print(f"[!] No unlabelled CSV files found in: {csv_dir}")
        return

    print(f"[+] Found {len(csv_candidates)} CSV file(s) to label.")

    for file_name in csv_candidates:
        file_path = os.path.join(csv_dir, file_name)
        base_name = os.path.splitext(file_name)[0]
        out_csv_path = os.path.join(csv_dir, f"{base_name}_labelled.csv")
        out_txt_path = os.path.join(csv_dir, f"{base_name}_labelled.txt")

        print(f"\n[+] Labelling: {file_name}")
        data = pd.read_csv(
            file_path,
            dtype={"Sport": "object", "Dport": "object", "sport": "object", "dport": "object"},
            low_memory=False,
        )

        labelled_df = label_dataset(data, gt)
        labelled_df.to_csv(out_csv_path, index=False)
        print(f"[✓] Saved labelled dataset: {out_csv_path}")

        stats = labelled_df[["BinaryLabel", "CategoryLabel", "SubCategoryLabel"]].value_counts()
        with open(out_txt_path, "w", encoding="utf-8") as out_txt:
            out_txt.write(stats.to_string())
        print(f"[✓] Saved labelling statistics: {out_txt_path}")

    print("\n[✓] All files successfully labelled!")


# ------------------ Main Flow & CLI ------------------


def main() -> None:
    global conf_file_path

    parser = argparse.ArgumentParser(description="Dataset Labelling Component (CLI)")
    parser.add_argument("-c", "--config", type=str, help="Path to configuration.json")
    parser.add_argument("-t", "--truth", type=str, help="Path to ground truth CSV file")

    args, _ = parser.parse_known_args()

    if args.config:
        conf_file_path = os.path.abspath(args.config)

    load_config()

    if args.truth:
        if os.path.isfile(args.truth) and args.truth.lower().endswith(".csv"):
            conf_file["paths"]["truth"] = os.path.abspath(args.truth)
            save_config()
        else:
            print(f"[!] Provided --truth path '{args.truth}' is invalid. Prompting...")

    run_labelling()


if __name__ == "__main__":
    main()