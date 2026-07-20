import os
import json

import ipywidgets as widgets
from IPython.display import display, HTML, clear_output

# ------------------ Variables ------------------

output = widgets.Output()
conf_file_path = None

# ------------------ Functions ------------------  

def select_workspace_conf_file_yes(b):
    workspace_config_question_box.layout.display = 'none'

    conf_file = widgets.Text(description = 'Configuration file: ', placeholder = '/path', style={'description_width': 'auto'})
    conf_file.layout.width = 'auto'
    
    b_conf_submit = widgets.Button(description='Submit')

    def select_conf_submit(b):
        global conf_file_path
        path = conf_file.value.strip()
        with output:
            clear_output()
            if os.path.exists(path) and path.lower().endswith(".json"):
                display(HTML(f'<p>Configuration file: {path}</p>'))
                conf_file_path = path
            else:
                display(HTML('<p>Invalid path</p>'))
                display(conf_file, b_conf_submit)

    b_conf_submit.on_click(select_conf_submit)

    with output:
        clear_output()
        display(conf_file, b_conf_submit)


def select_workspace_conf_file_no(b):
    workspace_config_question_box.layout.display = 'none'

    conf_file = widgets.Text(description = 'Configuration file: ', placeholder = '/path', style={'description_width': 'auto'})
    conf_file.layout.width = 'auto'

    b_no_conf_submit = widgets.Button(description='Submit')

    config_path_box = widgets.VBox([
        widgets.HTML('<h3>Where do you want the configuration file to be created?</h3>'),
        conf_file,
        b_no_conf_submit
    ])

    def select_no_conf_submit(b):
        global conf_file_path
        path = conf_file.value.strip()
        with output:
            clear_output()
            if os.path.exists(path) and os.path.isdir(path):
                conf_file_path = os.path.join(path, 'configuration.json')
                with open(conf_file_path, 'w') as f:
                    conf = {
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
                    json.dump(conf, f, indent=2)

                display(HTML(f'<p>New configuration file created at: {conf_file_path}</p>'))
            else:
                display(HTML('<p>Invalid path</p>'))
                display(config_path_box)
    
    b_no_conf_submit.on_click(select_no_conf_submit)

    with output:
        clear_output()
        display(config_path_box)        

# ------------------ Display ------------------

b_workspace_conf_file_yes = widgets.Button(description='Yes')
b_workspace_conf_file_no = widgets.Button(description='No')

b_workspace_conf_file_yes.on_click(select_workspace_conf_file_yes)
b_workspace_conf_file_no.on_click(select_workspace_conf_file_no)

workspace_config_question_box = widgets.VBox([
    widgets.HTML('<h3>Do you have a configuration file?</h3>'),
    widgets.HBox([b_workspace_conf_file_yes, b_workspace_conf_file_no])
])

display(workspace_config_question_box)
display(output)