# Configurations

HERA has a configurations file to make it easier to use. It is divided into two parts. The first part is the paths section, which contains the paths you should input for your pcap, flow, csv, and truth files to be created in the HERA workspace.

```json
{
  "paths": {
    "pcap": "",
    "flow": "",
    "csv": "",
    "truth": ""
  },
}
```

The second part is the values section, which contains the interface field for you network interface if capturing traffic or using the online mode. The argus field contains the arguments you want to use with argus, those can be:
    - -A to generate application byte metrics in each audit record.
    - -O to turn off Berkeley Packet Filter optimizer. If you think it generates bad code.
    - -Z to collect packet size information for all flows (to generate mean, max, min and standard deviation).
    - -J to generate packet performance (jitter) data in each audit record.
    - -m to provide MAC address information in argus records.
    - -R to generate argus records such that response times can be derived from transaction data.

 The interval field contains the number, in seconds, that you want you flows to be divided if it extends past that number. Lets say a connection lasts for 100 seconds, if the interval is defined as 60 seconds, then it would be divided into two flows. The features field contains the features you want to extract from the flows, these can be viewed in detail in the features file in the docs folder. Then the client to use, that is ra or racluster, the ra will process the flows by default, while racluster groups the flows further. Finally, the man field refers to if you want management information of argus to be included in the output, man for including, noman for not including.


```json
{
    "values": {
    "interface": "enp0s3",
    "argus": [],
    "interval": 60,
    "features": [],
    "client": "ra",
    "man": "noman"
  }
}
```
