import os
import json
import subprocess

from contextlib import contextmanager

import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# ------------------ Variables ------------------

output = widgets.Output()

conf_file = None

argus_fields = ['-A | Generate application byte metrics in each audit record.',
                '-O | Turn off Berkeley Packet Filter optimizer. If you think it generates bad code.',
                '-Z | Collect packet size information for all flows (to generate mean, max, min and standard deviation).',
                '-J | Generate packet performance (jitter) data in each audit record.',
                '-m | Provide MAC address information in argus records.',
                '-R | Generate argus records such that response times can be derived from transaction data.']

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
            check_values()

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

                        remaining_invalid = [
                            k for k in ["pcap", "flow", "csv"]
                            if not (os.path.isdir(conf_file["paths"][k]) and 
                                    os.path.exists(conf_file["paths"][k]))
                        ]

                        if not remaining_invalid:
                            check_values()
                
            path_b.on_click(path_b_submit)
            display(widgets.HTML(f"<b>Please insert the {key.upper()} path:</b>"), path_t, path_b, path_b_out)

def check_last_digit(string):
    if string[-1] == '/':
        return string
    else:
        return string + '/'

def check_done():
    argus = conf_file["values"]["argus"]   
    interval = conf_file["values"]["interval"] 

    if argus is not None and len(argus) > 0 and interval > 0:
        with output:
            flow_extract()

def check_values():
    with output:
        clear_output()

        argus = conf_file["values"]["argus"]   
        interval = conf_file["values"]["interval"] 

        if not argus:
            default_argus_values = ['-A | Generate application byte metrics in each audit record.',
                                    '-Z | Collect packet size information for all flows (to generate mean, max, min and standard deviation).',
                                    '-J | Generate packet performance (jitter) data in each audit record.',]

            argus_fields_select = widgets.SelectMultiple(
                options=argus_fields,
                value=default_argus_values,  
                disabled=False
            )

            argus_fields_select.layout.width = '600px'
            argus_fields_select.layout.height = '150px'

            argus_fields_description_label = widgets.HTML('<h4>Fields to generate HERA flow files:</h4>')

            b_submit = widgets.Button(description="Submit")

            def flow_b_submit(b):
                    conf_file["values"]["argus"] = list(argus_fields_select.value)

                    with open(conf_file_path, "w") as f:
                        json.dump(conf_file, f, indent=2)
                    
                    w_argus_values.layout.display = 'none'
                    check_done()
                
            b_submit.on_click(flow_b_submit)

            w_argus_values = widgets.VBox([argus_fields_description_label, argus_fields_select, b_submit])

            display(w_argus_values)
        if not interval:
            S_value_textbox = widgets.IntText(
                value=60,
                min=0,  
                description='Value:',
                disabled=False
            )

            confirm_button = widgets.Button(description="Confirm")

            def interval_b_submit(b):
                with output:
                    if S_value_textbox.value >= 0:
                        conf_file["values"]["interval"] = S_value_textbox.value

                        with open(conf_file_path, "w") as f:
                            json.dump(conf_file, f, indent=2)
                    else:
                        print("Please enter a non-negative value.")

                    w_interval_values.layout.display = 'none'
                    check_done()
                    
            confirm_button.on_click(interval_b_submit)

            argus_flow_interval_description_label = widgets.HTML('<h4>Please select a value in seconds for the flow interval, default value is 60:</h4>')

            w_interval_values = widgets.VBox([argus_flow_interval_description_label, S_value_textbox, confirm_button])
            display(w_interval_values)
        if argus is not None and len(argus) > 0 and interval > 0:
            check_done()

def flow_extract():
    with output:
        argus_args = [item.split(' | ')[0] for item in conf_file["values"]["argus"]]
        S_value = conf_file["values"]["interval"]

        label = widgets.Text('Waiting for button click.')
        argus_file_button = widgets.Button(description='Create HERA Flow File', layout=widgets.Layout(width='auto'))

        @contextmanager
        def show_loading():
            label.value = 'Running Argus...'
            yield
            label.value = 'Ready! Go to the next component!'

        def start_hera_file_creation_process():
            pcap_path = check_last_digit(conf_file["paths"]["pcap"])
            hera_path = check_last_digit(conf_file["paths"]["flow"])

            pcap_file_name = [
                f for f in os.listdir(pcap_path)
                if f.endswith(".pcap") or f.endswith(".pcapng")
            ]

            for i in range(len(pcap_file_name)):
                print(f"Processing: {pcap_file_name[i]}")
                argus_command_file = ["argus"] + ["-S", str(S_value)] + argus_args + ["-r", pcap_path + pcap_file_name[i], "-w", hera_path + os.path.splitext(os.path.basename(pcap_file_name[i]))[0] + ".hera"]
                argus_process = subprocess.Popen(argus_command_file, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                argus_process.communicate() 

        def create_hera_file(self):
            with show_loading():
                start_hera_file_creation_process()
                
        argus_file_button.on_click(create_hera_file)

        display(argus_file_button)    
        display(label)

# ------------------ Display ------------------

display(output)

load_config()

check_valid_folder(conf_file, conf_file_path, ["flow", "csv"])
