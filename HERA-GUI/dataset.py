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

features = ['srcid', 'trans', 'flgs', 'seq', 'dur', 'runtime', 'idle', 'mean', 'stddev', 'sum', 'min', 'max', 'smac', 'dmac', 'soui', 'doui', 'stos', 'dtos', 'sdsb', 'ddsb', 'sco', 'dco', 'sttl', 'dttl', 'shops', 'dhops', 'sipid', 'dipid', 'smpls', 'dmpls', 'autoid', 'sas', 'das', 'ias', 'cause', 'nstroke', 'snstroke', 'dnstroke', 'pkts', 'spkts', 'dpkts', 'bytes', 'sbytes', 'dbytes', 'appbytes', 'sappbytes', 'dappbytes', 'pcr', 'load', 'sload', 'dload', 'loss', 'sloss', 'dloss', 'ploss', 'psloss', 'pdloss', 'retrans', 'sretrans', 'dretrans', 'pretrans', 'psretrans', 'pdretrans', 'sgap', 'dgap', 'rate', 'srate', 'drate', 'dir', 'sintpkt', 'sintpktmin', 'sintpktmax', 'sintdist', 'sintpktact', 'sintdistact', 'sintpktidl', 'sintdistidl', 'dintpkt', 'dintpktmin', 'dintpktmax', 'dintdist', 'dintpktact', 'dintdistact', 'dintpktidl', 'dintdistidl', 'sjit', 'sjitact', 'sjitidle', 'djit', 'djitact', 'djitidle', 'state', 'label', 'suser', 'duser', 'swin', 'dwin', 'svlan', 'dvlan', 'svid', 'dvid', 'svpri', 'dvpri', 'srng', 'erng', 'stcpb', 'dtcpb', 'tcprtt', 'synack', 'ackdat', 'tcpopt', 'inode', 'offset', 'smeansz', 'dmeansz', 'spktsz', 'smaxsz', 'dpktsz', 'dmaxsz', 'sminsz', 'dminsz', 'Ssaddr', 'Sdaddr']

feature_descriptions = {"srcid": "Argus specific feature, representing an Argus source identifier.", "seq": "Argus sequence number.", "trans": "Feature indicating the number of records that were aggregated in a flow. This feature only presents a value above 1 when aggregating flows.", "smac": "Source MAC address.", "dmac": "Destination MAC address.", "soui": "Source OUI portion of the MAC address.", "doui": "Destination OUI portion of the MAC address.", "autoid": "MySQL identifier, automatically generated.", "sco": "Source IP's address country code.", "dco": "Destination IP's address country code.", "sas": "Source origin autonomous system.", "das": "Destination origin autonomous system.", "ias": "Intermediate origin autonomous system of ICMP generator.", "inode": "ICMP intermediate node.", "sipid": "Source IP identifier.", "dipid": "Destination IP identifier.", "srng": "Start time timestamp for when the timerange is filtered.", "erng": "End time timestamp for when the timerange is filtered.", "pkts": "Total packet count.", "spkts": "Source to destination packet count.", "dpkts": "Destination to source packet count.", "bytes": "Total transaction bytes.", "sbytes": "Source to destination transaction bytes.", "dbytes": "Destination to source transaction bytes.", "appbytes": "Total application bytes.", "sappbytes": "Source to destination bytes.", "dappbytes": "Destination to source bytes.", "state": "State of the flow.", "loss": "Packets that were retransmitted or dropped.", "sloss": "Source packets that were retransmitted or dropped.", "dloss": "Destination packets that were retransmitted or dropped.", "ploss": "Percentage of packets that were retransmitted or dropped.", "retrans": "Retransmitted packets.", "sretrans": "Retransmitted source packets.", "dretrans": "Retransmitted destination packets.", "pretrans": "Percentage of packets that were retransmitted.", "sgap": "Source bytes that are missing in the data stream.", "dgap": "Destination bytes that are missing in the data stream.", "smeansz": "Mean of the size of the flow transmitted by the source.", "dmeansz": "Mean of the size of the flow transmitted by the destination.", "spktsz": "Histogram for the distribution of the source packet size.", "dpktsz": "Histogram for the distribution of the destination packet size.", "smaxsz": "Maximum packet size of traffic transmitted by the source.", "dmaxsz": "Maximum packet size of traffic transmitted by the destination.", "sminsz": "Minimum packet size of traffic transmitted by the source.", "dminsz": "Minimum packet size of traffic transmitted by the destination.", "suser": "Source user data buffer.", "duser": "Destination user data buffer.", "svlan": "Source VLAN identifier.", "dvlan": "Destination VLAN identifier.", "svid": "Source VLAN identifier.", "dvid": "Destination VLAN identifier.", "svpri": "Source VLAN priority.", "dvpri": "Destination VLAN priority.", "offset": "Byte offset in file or stream.", "nstroke": "Number of observed keystrokes.", "snstroke": "Number of observed keystrokes from source to destination.", "dnstroke": "Number of observed keystrokes from destination to source.", "smpls": "Source MPLS identifier.", "dmpls": "Destination MPLS identifier.", "dur": "Flow's total duration.", "sjit": "Source jitter in mSec.", "sjitact": "Source active jitter in mSec.", "djit": "Destination jitter in mSec.", "djitact": "Destination active jitter in mSec", "load": "Bits per second.", "sload": "Source bits per second.", "dload": "Destination bits per second.", "rate": "Packets per second.", "srate": "Source packets per second.", "drate": "Destination packets per second.", "runtime": "Flow's active run time, which is the sum of the records' duration.", "idle": "Flow's time since the last packet had activity. It is calculated as the current time minus the last time.", "mean": "Average duration of the aggregated records.", "stddev": "Standard deviation of the duration of the aggregated records.", "sum": "Total duration of the aggregated records.", "min": "Minimum duration of the aggregated records.", "max": "Maximum duration of the aggregated records.", "sintpkt": "Source interpacket arrival time in mSec.", "sintpktmin": "Mininum source interpacket arrival time in mSec.", "sintpktmax": "Maximun source interpacket arrival time in mSec.", "sintdist": "Source interpacket arrival time distribution.", "sintpktact": "Source active interpacket arrival time in mSec.", "sintdistact": "Source active interpacket arrival time distribution.", "sintpktidl": "Source idle interpacket arrival time in mSec.", "sintdistidl": "Source idle interpacket arrival time distribution.", "dintpkt": "Destination interpacket arrival time in mSec.", "dintpktmin": "Mininum destination interpacket arrival time in mSec.", "dintpktmax": "Maximun destination interpacket arrival time in mSec.", "dintdist": "Destination interpacket arrival time distribution.", "dintpktact": "Destination active interpacket arrival time in mSec.", "dintdistact": "Destination active interpacket arrival time distribution.", "dintpktidl": "Destination idle interpacket arrival time in mSec.", "dintdistidl": "Destination idle interpacket arrival time distribution.", "flgs": "Flow state flags noted in transaction. This feature reports various flow records and protocol identifiers, states and attributes.", "stos": "Source type of service byte value.", "dtos": "Destination type of service byte value.", "shops": "Number of hops from source to this point.", "dhops": "Number of hops from destination to this point.", "sdsb": "Source DiffServ byte value.", "ddsb": "Destination DiffServ byte value.", "sttl": "Source to destination time to live value.", "dttl": "Destination to source time to live value.", "Ssaddr": "Calculated feature for the number of connections with the same service and source address.", "Sdaddr": "Calculated feature for the number of connections with the same service and destination address.", "pcr": "Producer consumer ratio.", "dir": "Direction of the flow represented in arrows.", "cause": "Argus value containing a cause code such as start, status, stop, close or error.", "label": "Metadata in Argus data.", "tcpopt": "This feature presents the TCP options at initiation of the flow.", "synack": "TCP connection setup time with the time between the SYN and SYN_ACK packets.", "ackdat": "TCP connection setup time with the time between SYN_ACK and ACK packets.", "tcprtt": "The sum of SynAck and AckDat packets signifying the TCP connection setup round-trip time.", "swin": "Source TCP window advertisement.", "dwin": "Destination TCP window advertisement.", "stcpb": "Source TCP base sequence number.", "dtcpb": "Destination TCP base sequence number.", "psloss": "Percent source pkts retransmitted or dropped.", "pdloss": "Percent destination pkts retransmitted or dropped.", "psretrans": "Percent source pkts retransmitted.", "pdretrans": "Percent destination pkts retransmitted.", "sjitidle": "Source idle jitter in mSec.", "djitidle": "Destination idle jitter in mSec."}

default_features = ['bytes', 'sbytes', 'dbytes', 'pkts', 'spkts', 'dpkts', 'dur', 'runtime', 'idle', 'flgs', 'tcpopt', 'Ssaddr', 'Sdaddr']

cic_10_features = ['sintpkt', 'sintpktmax', 'sintpktmin', 'dintpkt', 'dintpktmax', 'dintpktmin', 'mean', 'stddev', 'max', 'min']

unswnb15_features = ['state', 'dur', 'sbytes', 'dbytes', 'sttl', 'dttl', 'sloss', 'dloss', 'sload', 'dload', 'spkts', 'dpkts', 'swin', 'dwin', 'stcpb', 'dtcpb', 'smeansz', 'dmeansz','sjit', 'djit', 'sintpkt', 'dintpkt', 'tcprtt', 'synack', 'ackdat']

botiot_features = ['flgs', 'pkts', 'bytes', 'state', 'seq', 'dur', 'mean', 'stddev', 'smac', 'dmac', 'sum', 'min', 'max', 'soui', 'doui', 'sco', 'dco', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'srate', 'drate']

genis_features = ['trans', 'flgs', 'seq', 'dur', 'runtime', 'idle', 'mean', 'stddev', 'sum', 'min', 'max', 'smac', 'dmac', 'soui', 'doui', 'stos', 'dtos', 'sdsb', 'ddsb', 'sco', 'dco', 'sttl', 'dttl', 'shops', 'dhops', 'sipid', 'dipid', 'smpls', 'dmpls', 'autoid', 'sas', 'das', 'ias', 'cause', 'nstroke', 'snstroke', 'dnstroke', 'pkts', 'spkts', 'dpkts', 'bytes', 'sbytes', 'dbytes', 'appbytes', 'sappbytes', 'dappbytes', 'pcr', 'load', 'sload', 'dload', 'loss', 'sloss', 'dloss', 'ploss', 'retrans', 'sretrans', 'dretrans', 'pretrans', 'sgap', 'dgap', 'rate', 'srate', 'drate', 'dir', 'sintpkt', 'sintpktmin', 'sintpktmax', 'sintdist', 'sintpktact', 'sintdistact', 'sintpktidl', 'sintdistidl', 'dintpkt', 'dintpktmin', 'dintpktmax', 'dintdist', 'dintpktact', 'dintdistact', 'dintpktidl', 'dintdistidl', 'sjit', 'sjitact', 'djit', 'djitact', 'state', 'suser', 'duser', 'swin', 'dwin', 'svlan', 'dvlan', 'svid', 'dvid', 'svpri', 'dvpri', 'srng', 'erng', 'stcpb', 'dtcpb', 'tcprtt', 'synack', 'ackdat', 'tcpopt', 'inode', 'offset', 'smeansz', 'dmeansz', 'smaxsz', 'dmaxsz', 'sminsz', 'dminsz', 'Ssaddr', 'Sdaddr']

client = ['ra', 'racluster']

man = ['noman', 'man']

# ------------------ Functions ------------------  

def load_config():
    global conf_file
    
    if conf_file_path is None:
        raise ValueError("Please run Workspace Definition first! Configuration file location needed.")
    
    with open(conf_file_path) as f:
        conf_file = json.load(f)

def feature_select():
    if not conf_file["values"]["features"]:
        feature_selector = widgets.SelectMultiple(
            #options=features,
            options=[(f"{f} - {feature_descriptions.get(f, f)}", f) for f in features],
            disabled=False,
            layout=widgets.Layout(width='auto', height='auto')
        )

        features_description_label = widgets.HTML('<h4>Select the features you want present in your dataset:</h4>')

        w_features = widgets.VBox([features_description_label, feature_selector])

        display(w_features)

        def select_features(features_list):
            valid_values = [value for label, value in feature_selector.options]
            feature_selector.value = tuple(f for f in features_list if f in valid_values)

        all_feature_button = widgets.Button(description='Select All')
        default_feature_button = widgets.Button(description='Default Features')
        cic_10_feature_button = widgets.Button(description='CIC 10 Features')
        unswnb15_feature_button = widgets.Button(description='UNSW-NB15')
        botiot_feature_button = widgets.Button(description='Bot-IoT')
        genis_feature_button = widgets.Button(description='GeNIS')

        all_feature_button.on_click(lambda b: select_features(features))
        default_feature_button.on_click(lambda b: select_features(default_features))
        cic_10_feature_button.on_click(lambda b: select_features(cic_10_features))
        unswnb15_feature_button.on_click(lambda b: select_features(unswnb15_features))
        botiot_feature_button.on_click(lambda b: select_features(botiot_features))
        genis_feature_button.on_click(lambda b: select_features(genis_features))

        w_dataset = widgets.HBox([all_feature_button, default_feature_button, unswnb15_feature_button, botiot_feature_button, cic_10_feature_button, genis_feature_button])

        display(w_dataset)

        b_submit = widgets.Button(description="Submit")

        def f_b_submit(b):
            conf_file["values"]["features"] = list(feature_selector.value)

            with open(conf_file_path, "w") as f:
                json.dump(conf_file, f, indent=2)

                clear_output()

                client_select()
                    
        b_submit.on_click(f_b_submit)

        display(b_submit)
    else:
        client_select()

def client_select():
    if not conf_file["values"]["client"]:
        client_selector = widgets.Select(
            options=client,
            disabled=False,
            layout=widgets.Layout(width='auto', height='auto')
        )

        client_description_label = widgets.HTML('<h4>Select client to use:</h4>')

        display(widgets.VBox([client_description_label, client_selector]))

        b_submit = widgets.Button(description="Submit")

        def c_b_submit(b):
            conf_file["values"]["client"] = client_selector.value

            with open(conf_file_path, "w") as f:
                json.dump(conf_file, f, indent=2)

                clear_output()

                man_select()
                    
        b_submit.on_click(c_b_submit)

        display(b_submit)
    else:
        man_select()

def man_select():
    if not conf_file["values"]["man"]:
        man_selector = widgets.Select(
            options=man,
            disabled=False,
            layout=widgets.Layout(width='auto', height='auto')
        )

        man_description_label = widgets.HTML('<h4>Select which to use:</h4>')

        display(widgets.VBox([man_description_label, man_selector]))

        b_submit = widgets.Button(description="Submit")

        def m_b_submit(b):
            conf_file["values"]["man"] = man_selector.value

            with open(conf_file_path, "w") as f:
                json.dump(conf_file, f, indent=2)

                clear_output()

                feature_extract()
                    
        b_submit.on_click(m_b_submit)

        display(b_submit)
    else:
        feature_extract()

def check_last_digit(string):
    if string[-1] == '/':
        return string
    else:
        return string + '/'

def feature_extract():
    calculated_features = ['Ssaddr', 'Sdaddr']

    calculated_features_dict = {'Ssaddr': 'saddr, sport', 'Sdaddr': 'daddr, dport'}

    features_string = 'rank stime ltime proto saddr sport daddr dport'
    calculated_features_array = []

    for feature in conf_file["values"]["features"]:
        if feature not in calculated_features:
            features_string += ' ' + feature
        else:
            calculated_features_array.append(feature)
            
    #-nn", "-u",- ip",
    def calculate_features(valid_hera_path): 
        # Generating normal features
        
        features_n = subprocess.run([conf_file["values"]["client"], "-n", "-M", conf_file["values"]["man"], "-u", "-r", valid_hera_path, "-c", "," , "-s", features_string], capture_output=True, text=True)
        
        lines_nf = features_n.stdout.strip().split('\n')
        column_names_nf = lines_nf[0].split(',')
        data_nf = [[field.strip() if field.strip() else np.nan for field in line.split(',')] for line in lines_nf[1:]]
        features_df = pd.DataFrame(data_nf, columns=column_names_nf)
        
        # Generating ID
        
        features_id = subprocess.run([conf_file["values"]["client"], "-n", "-M", conf_file["values"]["man"], "-u", "-r", valid_hera_path, "-c", "," , "-s", "daddr, saddr, dport, sport, proto"], capture_output=True, text=True)
        lines_id = features_id.stdout.strip().split('\n')
        data_id = ['-'.join(["nan" if field.strip() == '' else field.strip() for field in line.split(',')]) for line in lines_id[1:]]
        features_df.insert(0, 'FlowID', data_id)

        # Generating calculated features
        
        def calculate_features(valid_hera_path, calculated_feature):
            features = subprocess.run([conf_file["values"]["client"], "-n", "-M", conf_file["values"]["man"], "-u", "-r", valid_hera_path, "-c", ",", "-s", calculated_features_dict[calculated_feature]], capture_output=True, text=True)
            lines = features.stdout.strip().split('\n')
        
            column_titles = lines[0].split(',')
            
            service_count = []
            for line in lines[1:]:
                f1, f2 = line.split(',')
                service_count.append([f1, f2])  
            df = pd.DataFrame(service_count, columns=column_titles)
        
            features_df[calculated_feature] = df.groupby([df.columns[0], df.columns[1]])[df.columns[0]].transform('count').astype(pd.Int64Dtype())
        
        for feat in calculated_features_array:
            calculate_features(valid_hera_path, feat)
        
        return features_df

    i = 0

    hera_path = check_last_digit(conf_file["paths"]["flow"])
    csv_path = check_last_digit(conf_file["paths"]["csv"])

    hera_file_name = [
        f for f in os.listdir(hera_path)
        if f.endswith(".hera")
    ]

    csv_file_name = [
        f.replace(".hera", "")
        for f in hera_file_name
    ]

    for file in hera_file_name:
        if not os.path.exists(csv_path + conf_file["values"]["client"] + '_' + csv_file_name[i] + ".csv"):
            f = calculate_features(hera_path + file)
            f.to_csv(csv_path + conf_file["values"]["client"] + '_' + csv_file_name[i] + ".csv", index=False)
            print(f"Features extracted to CSV file: {csv_path + conf_file['values']['client'] + '_' + csv_file_name[i] + '.csv'}")
            
            with open(csv_path + "racount_" + csv_file_name[i] + ".txt", "w") as output_file:
                subprocess.run(["racount", "-r", os.path.join(hera_path, file), "-M", "addr", "proto"], stdout=output_file)
        else:
            print(f"The file '{csv_path + conf_file['values']['client'] + '_' + csv_file_name[i] + '.csv'}' already exists.")
        i += 1 

    display(widgets.HTML("All done, go to the labelling component if you wish for labelled datasets and have ground truth information!"))


# ------------------ Display ------------------

display(output)

load_config()

feature_select()
