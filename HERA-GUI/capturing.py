import os
import json
import pandas as pd
import numpy as np
import threading
import signal
import time
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

import subprocess
from datetime import datetime

import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# ------------------ Variables ------------------

output = widgets.Output()

conf_file = None

# ------------------ Functions ------------------  

def load_config():
    global conf_file
    
    if conf_file_path is None:
        raise ValueError("Please run Workspace Definition first! Configuration file location needed.")
    
    with open(conf_file_path) as f:
        conf_file = json.load(f)

def check_valid_folder(conf_file, conf_file_path, paths_to_check=None):
    if paths_to_check is None:
        paths_to_check = ["pcap", "flow", "csv"]

    with output:
        clear_output()

        invalid_paths = [key for key in paths_to_check
                         if not (os.path.isdir(conf_file["paths"][key]) and 
                                 os.path.exists(conf_file["paths"][key]))]

        if not invalid_paths:
            display(widgets.HTML("Validated path! Go to the next component!"))
            return

        for key in invalid_paths:

            path_t = widgets.Text(placeholder=f'Enter {key} path')
            path_b = widgets.Button(description=f'Submit {key}')
            path_b_out = widgets.Output()

            def path_b_submit(b, key=key, path_t=path_t, path_b_out=path_b_out):
                with path_b_out:
                    clear_output()

                    if not (os.path.isdir(path_t.value) and os.path.exists(path_t.value)):
                        display(widgets.HTML(f"Incorrect Path. Try again."))

                    else:
                        conf_file["paths"][key] = path_t.value

                        with open(conf_file_path, "w") as f:
                            json.dump(conf_file, f, indent=2)

                        path_t.close()
                        display(widgets.HTML(f"All done!"))
                
            path_b.on_click(path_b_submit)
            display(widgets.HTML(f"<b>Please insert the {key.upper()} path:</b>"), path_t, path_b, path_b_out)

def select_capturing_no(b):
    capturing_question_box.layout.display = 'none'

    load_config()

    check_valid_folder(conf_file, conf_file_path, ["pcap"])

def select_capturing_yes(b):
    capturing_question_box.layout.display = 'none'

    load_config()

    with output:
        clear_output()

        if not conf_file["values"]["interface"]:
            interface_textbox = widgets.Text(description = 'Where do you wish to capture? ', placeholder = 'interface', style={'description_width': 'auto'})

            confirm_button = widgets.Button(description="Confirm")

            def interface_submit(b):
                conf_file["values"]["interface"] = interface_textbox.value

                with open(conf_file_path, "w") as f:
                    json.dump(conf_file, f, indent=2)
                
                aid()

            confirm_button.on_click(interface_submit)
            display(interface_textbox, confirm_button)
        else:
            aid()

def aid():
    clear_output()

    b_no_real = widgets.Button(description='No', layout=widgets.Layout(width='auto'))
    b_yes_real = widgets.Button(description='Yes', layout=widgets.Layout(width='auto'))

    b_no_real.on_click(select_capturing_no_real)
    b_yes_real.on_click(select_capturing_yes_real)

    capturing_question_box_real = widgets.VBox([
        widgets.HTML('<h3>Do you want to real-time processing of the traffic?</h3>'),
        widgets.HBox([b_yes_real, b_no_real])
    ])

    display(capturing_question_box_real)    


def select_capturing_no_real(b):
    clear_output()

    capture_file = conf_file["paths"]["pcap"] + "/" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S.pcapng")

    tshark_process = subprocess.Popen(
        ["tshark", "-i", conf_file["values"]["interface"], "-w", capture_file],
    )

    b_stop = widgets.Button(description='Stop & Save', layout=widgets.Layout(width='auto'))

    def stop_wire(b):
        tshark_process.terminate()
        tshark_process.wait()
        print("Capture stopped!")
        capturing.layout.display = 'none'

    b_stop.on_click(stop_wire)

    capturing = widgets.VBox([widgets.HTML("Capture started..."), b_stop])

    display(capturing)

def check_last_digit(string):
    if string[-1] == '/':
        return string
    else:
        return string + '/'
    
def select_capturing_yes_real(b):
    clear_output()

    if not os.path.isdir(conf_file["paths"]["flow"]) or not os.path.isdir(conf_file["paths"]["csv"]):
        check_valid_folder(conf_file, conf_file_path, ["flow", "csv"])

    # ------------------------------
    # Setup configuration and paths
    # ------------------------------
    argus_args = [item.split(' | ')[0] for item in conf_file["values"]["argus"]]

    folder_path_hera = conf_file["paths"]["flow"]
    hera_path = check_last_digit(folder_path_hera)
    csv_folder = check_last_digit(conf_file["paths"]["csv"])

    interface = conf_file["values"]["interface"]
    features_selector = conf_file["values"]["features"]

    calculated_features = ['Ssaddr', 'Sdaddr']
    calculated_features_dict = {'Ssaddr': 'saddr, sport', 'Sdaddr': 'daddr, dport'}

    features_string = 'rank stime ltime proto saddr sport daddr dport'
    calculated_features_array = []

    for feature in features_selector:
        if feature not in calculated_features:
            features_string += ' ' + feature
        else:
            calculated_features_array.append(feature)

    # ------------------------------
    # Feature calculation function
    # ------------------------------
    def calculate_features(valid_hera_path): 
        features_df = pd.DataFrame()
        # Normal features
        features_n = subprocess.run(
            [conf_file["values"]["client"], "-n", "-M", conf_file["values"]["man"],
             "-u", "-r", valid_hera_path, "-c", ",", "-s", features_string],
            capture_output=True, text=True
        )

        lines_nf = features_n.stdout.strip().split('\n')
        if len(lines_nf) > 1:
            column_names_nf = lines_nf[0].split(',')
            data_nf = [[field.strip() if field.strip() else np.nan for field in line.split(',')] 
                       for line in lines_nf[1:]]
            features_df = pd.DataFrame(data_nf, columns=column_names_nf)

        # FlowID
        features_id = subprocess.run(
            [conf_file["values"]["client"], "-n", "-M", conf_file["values"]["man"],
             "-u", "-r", valid_hera_path, "-c", ",", "-s", "daddr, saddr, dport, sport, proto"],
            capture_output=True, text=True
        )
        lines_id = features_id.stdout.strip().split('\n')
        if len(lines_id) > 1:
            data_id = ['-'.join(["nan" if field.strip() == '' else field.strip() for field in line.split(',')]) 
                       for line in lines_id[1:]]
            features_df.insert(0, 'FlowID', data_id)

        # Calculated features
        for calculated_feature in calculated_features_array:
            features = subprocess.run(
                [conf_file["values"]["client"], "-n", "-M", conf_file["values"]["man"],
                 "-u", "-r", valid_hera_path, "-c", ",", "-s", calculated_features_dict[calculated_feature]],
                capture_output=True, text=True
            )
            lines = features.stdout.strip().split('\n')
            if len(lines) < 2:
                continue
            column_titles = lines[0].split(',')
            
            service_count = []
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) < 2:
                    continue
                f1, f2 = parts
                service_count.append([f1, f2])  
            df = pd.DataFrame(service_count, columns=column_titles)
            
            features_df[calculated_feature] = df.groupby([df.columns[0], df.columns[1]])[df.columns[0]] \
                                                .transform('count').astype(pd.Int64Dtype())
        
        return features_df

    # ------------------------------
    # Directory watcher for .hera files
    # ------------------------------
    class HeraFileHandler(FileSystemEventHandler):
        def __init__(self):
            self.queue = deque()
            super().__init__()

        def finish_writing(self, filepath, check_interval=5, stable_time=60):
            """Wait until file size is stable for stable_time seconds"""
            last_size = -1
            stable_counter = 0
            while stable_counter < stable_time:
                try:
                    size = os.path.getsize(filepath)
                except FileNotFoundError:
                    return False
                if size == last_size:
                    stable_counter += check_interval
                else:
                    stable_counter = 0
                last_size = size
                time.sleep(check_interval)
            return True

        def on_created(self, event):
            if event.is_directory:
                return
            filename = os.path.basename(event.src_path)
            if filename.endswith(".hera") and filename.startswith("split"):
                print(f"Detected new file: {filename}")
                self.queue.append(event.src_path)
                self.process_queue()

        def process_queue(self):
            """Process files in order with retries if busy"""
            while self.queue:
                filepath = self.queue[0]
                retries = 0
                max_retries = 5
                while retries < max_retries:
                    if not self.finish_writing(filepath):
                        print(f"[WARNING] File may be incomplete: {filepath}")
                    try:
                        features_df = calculate_features(filepath)
                        csv_file_name = os.path.basename(filepath).replace(".hera", ".csv")
                        csv_path = os.path.join(csv_folder, csv_file_name)
                        features_df.to_csv(csv_path, index=False)
                        print(f"Saved CSV: {csv_path}")

                        os.remove(filepath)
                        print(f"Deleted: {filepath}")
                        break  # success, exit retry loop
                    except OSError as e:
                        if e.errno == 26:  # Text file busy
                            retries += 1
                            wait_time = 5 * retries
                            print(f"File busy, retrying in {wait_time}s ({retries}/{max_retries}): {filepath}")
                            time.sleep(wait_time)
                        else:
                            print(f"Error processing {filepath}: {e}")
                            break
                else:
                    print(f"[ERROR] Could not process file after retries: {filepath}")
                self.queue.popleft()

    # --- Start Argus ---
    def start_argus():
        argus_command = [
            "sudo", "argus", "-d", "-i", str(interface), "-P", str(561), "-S", str(conf_file["values"]["interval"])
        ] + argus_args + [
            "-w", os.path.join(hera_path, datetime.now().strftime("%Y_%m_%d_%H_%M_%S") + ".hera")
        ]
        print("\nStarting argus...")
        subprocess.run(argus_command, capture_output=False)

    # --- Start Rasplit ---
    def start_rasplit():
        pattern = os.path.join(hera_path, "split.%Y_%m_%d_%H_%M_%S.hera")
        rasplit_command = ["sudo", "rasplit", "-M", "time", "1m", "-S", "localhost:561", "-w", pattern]
        print("\nStarting rasplit...")
        subprocess.run(rasplit_command, capture_output=False)

    # --- Monitor directory ---
    def monitor_directory():
        event_handler = HeraFileHandler()
        observer = Observer()
        observer.schedule(event_handler, path=hera_path, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\nStopping HERA...")

            # Kill Argus safely
            try:
                result = subprocess.run(['pgrep', '-f', 'argus -d'], capture_output=True, text=True)
                if result.stdout:
                    for pid in result.stdout.strip().split('\n'):
                        subprocess.run(["sudo", "kill", pid])
                else:
                    print("No matching Argus processes found.")
            except Exception as e:
                print(f"Failed to kill Argus: {e}")

        observer.join()

    # --- Start threads ---
    try:
        argus_thread = threading.Thread(target=start_argus, daemon=True)
        argus_thread.start()
        time.sleep(5)

        rasplit_thread = threading.Thread(target=start_rasplit, daemon=True)
        rasplit_thread.start()

        monitor_directory()
    except Exception as e:
        print(f"\nSomething went wrong: {e}")

# ------------------ Display ------------------

b_no = widgets.Button(description='No', layout=widgets.Layout(width='auto'))
b_yes = widgets.Button(description='Yes', layout=widgets.Layout(width='auto'))

b_no.on_click(select_capturing_no)
b_yes.on_click(select_capturing_yes)

capturing_question_box = widgets.VBox([
    widgets.HTML('<h3>Do you want to capture traffic?</h3>'),
    widgets.HBox([b_yes, b_no])
])

display(capturing_question_box)
display(output)