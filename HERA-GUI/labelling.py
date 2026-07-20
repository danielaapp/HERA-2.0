import os
import json
import subprocess

import numpy as np
import pandas as pd

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

def gt():
    if conf_file["paths"]["truth"] is None:
        truth_file = widgets.Text(description = 'Ground truth file in a csv: ', placeholder = '/path', style={'description_width': 'auto'})
        truth_file.layout.width = 'auto'
        
        b_truth_submit = widgets.Button(description='Submit')

        def select_truth_submit(b):
            if os.path.exists(truth_file.value.strip()) and truth_file.value.strip().lower().endswith(".csv"):
                display(HTML(f'<p>Ground truth file: {truth_file.value.strip()}</p>'))

                conf_file["paths"]["truth"] = truth_file.value

                with open(conf_file_path, "w") as f:
                    json.dump(conf_file, f, indent=2)

                labelling()
            else:
                clear_output()
                display(HTML('<p>Invalid path</p>'))
                display(truth_file, b_truth_submit)

        b_truth_submit.on_click(select_truth_submit)
        
        with output:
            clear_output()
            display(truth_file, b_truth_submit)

    else:
        labelling()

def check_last_digit(string):
    if string[-1] == '/':
        return string
    else:
        return string + '/'

def labelling():
    gt = pd.read_csv(conf_file["paths"]["truth"], dtype={'Sport': 'object', 'Dport': 'object'}, low_memory=False)

    csv_path = check_last_digit(conf_file["paths"]["csv"])

    csv_file_name = [
        f for f in os.listdir(csv_path)
        if f.endswith(".csv")
    ]

    csv_files = [
        f.replace(".csv", "")
        for f in csv_file_name
    ]

    def label(data, gt):
        data['StartTime'] = data['StartTime'].round().astype(int)
        data['LastTime'] = data['LastTime'].round().astype(int)
        
        start_time = data['StartTime'].max()
        end_time = data['LastTime'].min()

        if not gt['StartTime'].isna().any():
            gt['StartTime'] = gt['StartTime'].round().astype(int)

        if not gt['LastTime'].isna().any():
            gt['LastTime'] = gt['LastTime'].round().astype(int)
        
        if gt['StartTime'].isna().any() and gt['LastTime'].isna().any():
            gt_filtered = gt  
        elif gt['StartTime'].isna().any():
            gt_filtered = gt[(gt['LastTime'] <= end_time) & (gt['LastTime'] >= start_time)]
        elif gt['LastTime'].isna().any():
            gt_filtered = gt[(gt['StartTime'] >= start_time) & (gt['StartTime'] <= end_time)] 
        else:
            gt_filtered = gt[(gt['StartTime'] <= start_time) & (gt['LastTime'] >= end_time)]

        print("Full: ", len(gt))
        print("Used: ", len(gt_filtered))
        
        data['BinaryLabel'] = -1
        data['CategoryLabel'] = "Labelling"
        data['SubCategoryLabel'] = "Labelling"
        
        for row in gt_filtered.itertuples(index=False, name='GT'):
            label_gt = (((data['StartTime'] >= row.StartTime) if not pd.isna(row.StartTime) else True) &
                        ((data['LastTime'] <= row.LastTime) if not pd.isna(row.LastTime) else True) &
                        ((data['SrcAddr'] == row.SrcAddr) if not pd.isna(row.SrcAddr) else True) &
                        ((data['DstAddr'] == row.DstAddr) if not pd.isna(row.DstAddr) else True) &
                        ((data['Sport'] == row.Sport) if not pd.isna(row.Sport) else True) &
                        ((data['Dport'] == row.Dport) if not pd.isna(row.Dport) else True) &
                        ((data['Proto'] == row.Proto) if not pd.isna(row.Proto) else True)
                    )
            
            data.loc[label_gt,'BinaryLabel'] = row.BinaryLabel
            data.loc[label_gt,'CategoryLabel'] = row.CategoryLabel
            data.loc[label_gt,'SubCategoryLabel'] = row.SubCategoryLabel
        
        data.loc[data['BinaryLabel'] == -1, 'BinaryLabel'] = 0
        data.loc[data['CategoryLabel'] == "Labelling", 'CategoryLabel'] = "Benign"
        data.loc[data['SubCategoryLabel'] == "Labelling", 'SubCategoryLabel'] = "Benign"
            
        return data

    i = 0

    for file in csv_file_name:
        data = pd.read_csv(csv_path + file, dtype={'Sport': 'object', 'Dport': 'object'}, low_memory=False)
        labelled_data = label(data, gt)
        
        labelled_data.to_csv(csv_path + os.path.splitext(os.path.basename(csv_files[i]))[0] + '_labelled.csv', index=False)
        
        stats = labelled_data[['BinaryLabel', 'CategoryLabel', 'SubCategoryLabel']].value_counts()
        with open(csv_path + os.path.splitext(os.path.basename(csv_files[i]))[0] + '_labelled' + ".txt", "w") as output_file:
            output_file.write(stats.to_string())
        
        i += 1
        
        print(file)

# ------------------ Display ------------------

display(output)

load_config()

gt()