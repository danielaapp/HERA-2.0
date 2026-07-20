# Features

HERA 2.0 contains a total of 129 features. They can be separated into the following categories:

- Network Identifiers;
- Packet Statistics;
- Time Statistics;
- Flags;
- Header Information;
- Verifiers;
- Flow Statistics;
- Labels;
- Protocol.

Furthermore, HERA 2.0 has pre-defined feature sets, the features present in these sets are identified by the following letters.

- A - All;
- D - Default;
- C - CICFlowMeter;
- N - UNSW-NB15;
- B - Bot-IoT;
- G - GeNIS.

To note, Argus features are described according to the provided description in the man files in <https://manpages.ubuntu.com/manpages/questing/man1/ra.1.html>.

## Network Identifiers

Features that identify or are used to identify a particular flow.

Sets | Name | Description
--- | --- | ---
A\|D\|C\|N\|B\|G | FlowID | Provides an identifier to the flow with destination and souce IP address, destination and source port, and protocol, all separated by a hyphen.
A | SrcId | Argus specific feature, representing an Argus source identifier.
A\|D\|C\|N\|B\|G | Rank | Sequence number representing the ordinal value of the output of the flow record.
A\|B\|G | Seq | Argus sequence number.
A\|G | Trans | Feature indicating the number of records that were aggregated in a flow.This feature only presents a value above 1 when aggregating flows.
A\|B\|G | SrcMac | Source MAC address.
A\|B\|G | DstMac | Destination MAC address.
A\|B\|G | SrcOui | Source OUI portion of the MAC address.
A\|B\|G | DstOui | Destination OUI portion of the MAC address.
A\|D\|C\|N\|B\|G | SrcAddr | Source IP address.
A\|D\|C\|N\|B\|G | DstAddr | Destination IP address.
A\|D\|C\|N\|B\|G | Proto | Transaction protocol of the flow.
A\|D\|C\|N\|B\|G | Sport | Source port number.
A\|D\|C\|N\|B\|G | Dport | Destination port number.
A\|G | AutoId | MySQL identifier, automatically generated.
A\|B\|G | sCo | Source IP's address country code.
A\|B\|G | dCo | Destination IP's address country code.
A\|G | iAS | Intermediate origin autonomous system of ICMP generator.
A\|G | sAS | Source origin autonomous system.
A\|G | dAS | Destination origin autonomous system.
A\|G | Inode | ICMP intermediate node.
A\|G | sIpId | source IP identifier.
A\|G | dIpId | destination IP identifier.
A\|D\|C\|N\|B\|G | StartTime | Record's start time.
A\|D\|C\|N\|B\|G | LastTime | Record's last time.
A\|G | Srange | Start time timestamp for when the timerange is filtered.
A\|G | ERange | End time timestamp for when the timerange is filtered.

## Packet Statistics

Features with information of counters and averages, which give insights into statistics of the packets constituting the particular flow.

Sets | Name | Description
--- | --- | ---
A\|D\|B\|G | TotPkts | Total packet count.
A\|D\|N\|B\|G | SrcPkts | Source to destination packet count.
A\|D\|N\|B\|G | DstPkts | Destination to source packet count.
A\|D\|B\|G | TotBytes | Total transaction bytes.
A\|D\|N\|B\|G | SrcBytes | Source to destination transaction bytes.
A\|D\|N\|B\|G | DstBytes | Destination to source transaction bytes.
A\|G | TotAppByte | Total application bytes.
A\|G | SAppBytes | Source to destination bytes.
A\|G | DAppBytes | Destination to source bytes.
A\|N\|B\|G | State | State of the flow.
A\|G | Loss | Packets that were retransmitted or dropped.
A\|N\|G | SrcLoss | Source packets that were retransmitted or dropped.
A\|N\|G | DstLoss | Destination packets that were retransmitted or dropped.
A\|G | pLoss | Percentage of packets that were retransmitted or dropped.
A\|G | Retrans | Retransmitted packets.
A\|G | SrcRetra | Retransmitted source packets.
A\|G | DstRetra | Retransmitted destination packets.
A\|G | pRetran | Percentage of packets that were retransmitted.
A\|G | SrcGap | Source bytes that are missing in the data stream.
A\|G | DstGap | Destination bytes that are missing in the data stream.
A\|N\|G | sMeanPktSz | Mean of the size of the flow transmitted by the source.
A\|N\|G | dMeanPktSz | Mean of the size of the flow transmitted by the destination.
A | sPktSz | Histogram for the distribution of the source packet size.
A | dPktSz | Histogram for the distribution of the destination packet size.
A\|G | sMaxPktSz | Maximum packet size of traffic transmitted by the source.
A\|G | dMaxPktSz | Maximum packet size of traffic transmitted by the destination.
A\|G | sMinPktSz | Minimum packet size of traffic transmitted by the source.
A\|G | dMinPktSz | Minimum packet size of traffic transmitted by the destination.
A\|G | srcUdata | Source user data buffer.
A\|G | dstUdata | Destination user data buffer.
A\|G | sVlan | Source VLAN identifier.
A\|G | dVlan | Destination VLAN identifier.
A\|G | sVid | Source VLAN identifier.
A\|G | dVid | Destination VLAN identifier.
A\|G | sVpri | Source VLAN priority.
A\|G | dVpri | Destination VLAN priority.
A\|G | Offset | Byte offset in file or stream.
A\|G | NStrok | Number of observed keystrokes.
A\|G | sNStrok | Number of observed keystrokes from source to destination.
A\|G | dNStrok | Number of observed keystrokes from destination to source.
A\|G | sMpls | Source MPLS identifier.
A\|G | dMpls | Destination MPLS identifier.

## Time Statistics

Features with any information that relates to time spent in the flow, both in forward and backward directions.

Sets | Name | Description
--- | --- | ---
A\|D\|N\|B\|G | Dur | Flow's total duration.
A\|N\|G | SrcJitter | Source jitter in mSec.
A\|G | SrcJitAct | Source active jitter in mSec.
A\|N\|G | DstJitter | Destination jitter in mSec.
A\|G | DstJitAct | Destination active jitter in mSec.
A\|G | Load | Bits per second.
A\|N\|G | SrcLoad | Source bits per second.
A\|N\|G | DstLoad | Destination bits per second.
A\|B\|G | Rate | Packets per second.
A\|B\|G | SrcRate | Source packets per second.
A\|B\|G | DstRate | Destination packets per second.
A\|D\|G | RunTime | Flow's active run time, which is the sum of the records' duration.
A\|D\|G | IdleTime | Flow's time since the last packet had activity. It is calculated as the current time minus the last time.
A\|C\|B\|G | Mean | Average duration of the aggregated records.
A\|C\|B\|G | StdDev | Standard deviation of the duration of the aggregated records.
A\|B\|G | Sum | Total duration of the aggregated records.
A\|C\|B\|G | Min | Minimum duration of the aggregated records.
A\|C\|B\|G | Max | Maximum duration of the aggregated records.
A\|C\|N\|G | SIntPkt | Source interpacket arrival time in mSec.
A\|C\|G | SIntPktMin | Mininum source interpacket arrival time in mSec.
A\|C\|G | SIntPktMax | Maximun source interpacket arrival time in mSec.
A\|G | SIntDist | Source interpacket arrival time distribution.
A\|G | SIntPktAct | Source active interpacket arrival time in mSec.
A\|G | SIntActDist | Source active interpacket arrival time distribution.
A\|G | SIntPktIdl | Source idle interpacket arrival time in mSec.
A\|G | SIntIdlDist | Source idle interpacket arrival time distribution.
A\|C\|N\|G | DIntPkt | Destination interpacket arrival time in mSec.
A\|C\|G | DIntPktMin | Mininum destination interpacket arrival time in mSec.
A\|C\|G | DIntPktMax | Maximun destination interpacket arrival time in mSec.
A\|G | DIntDist | Destination interpacket arrival time distribution.
A\|G | DIntPktAct | Destination active interpacket arrival time in mSec.
A\|G | DIntActDist | Destination active interpacket arrival time distribution.
A\|G | DIntPktIdl | Destination idle interpacket arrival time in mSec.
A\|G | DIntIdlDist | Destination idle interpacket arrival time distribution.

## Flags

Features with counters of flags in the packets summarised in the flows.

Sets | Name | Description
--- | --- | ---
A\|D\|B\|G | Flgs | Flow state flags noted in transaction. This feature reports various flow records and protocol identifiers, states and attributes.

## Header Information

Features that contain information exclusive to the headers of packets of the generated flows.

Sets | Name | Description
--- | --- | ---
A\|G | sTos | Source type of service byte value.
A\|G | dTos | Destination type of service byte value.
A\|G | sHops | Number of hops from source to this point.
A\|G | dHops | Number of hops from destination to this point.
A\|G | sDSb | Source DiffServ byte value.
A\|G | dDSb | Destination DiffServ byte value.
A\|N\|G | sTtl | Source to destination time to live value.
A\|N\|G | dTtl | Destination to source time to live value.

## Verifiers

Features which only purpose is to indicate if the flow meets a certain characteristic or not.

Sets | Name | Description
--- | --- | ---
A\|D\|G | Ssaddr | Calculated feature for the number of connections with the same service and source address.
A\|D\|G | Sdaddr | Calculated feature for the number of connections with the same service and destination address.

## Flow Statistics

Features that contain information exclusive to the flow in question.

Sets | Name | Description
--- | --- | ---
A\|G | PCRatio | Producer consumer ratio.
A\|G | Dir | Direction of the flow represented in arrows. If unidirectional it will only represent < or >, if bidirectional, it will contain both < and >. Moreover, it will also contain either -, \|, o or ? if the transaction was normal, reset, timed out or the direction unknown. This means this feature might have, for example, the value <->.  
A\|G | Cause | Argus value containing a cause code such as start, status, stop, close or error.

## Protocol

Features with protocol-specific information.

Sets | Name | Description
--- | --- | ---
A\|D\|G | TcpOpt | TCP related feature. This feature presents the TCP options at initiation of the flow.
A\|N\|G | SynAck | TCP related feature. TCP connection setup time with the time between the SYN and SYN_ACK packets.
A\|N\|G | AckDat | TCP related feature. TCP connection setup time with the time between SYN_ACK and ACK packets.
A\|N\|G | TcpRtt | TCP related feature. The sum of SynAck and AckDat packets signifying the TCP connection setup round-trip time.
A\|N\|G | SrcWin | TCP related feature. Source TCP window advertisement.
A\|N\|G | DstWin | TCP related feature. Destination TCP window advertisement.
A\|N\|G | SrcTCPBase | TCP related feature. Source TCP base sequence number.
A\|N\|G | DstTCPBase | TCP related feature. Destination TCP base sequence number.

## Labels

Features that classify the flow. These features do not belong to a specific set, they only appear if the labelling is executed.

Name | Description
--- | ---
Label | Metadata in Argus data.
BinaryLabel | Label to identify only whether a flow is benign or malicious, with '0' and '1', respectively.
CategoryLabel | Label to identify the general classification of a flow. For example, if '0' appears, it is identified as 'Benign', if '1' appears, it is identified as the type of malicious traffic, such as 'DDoS', 'Worm' or 'Backdoor', among many others.
SubCategoryLabel | Label to provide more information to 'CategoryLabel', for example, in the case of 'DoS', the label can provide information such as 'Slowloris', 'GoldenEye', or 'HTTP'.
