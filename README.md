## Description
The script prints interface throughput/packet rate statistics in an easy to read list format on NX-OS platforms.
Further port-channel and member interfaces are displayed in a structured way and IO summary is calculated over all ports.

The script knows two options:

 -d: list ports with description
 
 -u: list ports in up state
 
 -du: works as well
 
 Without options all interfaces are shown.

## To use

 1. Copy script to N9K switch bootflash:scripts/
     
 2. Execute using:
     
 source ifload.py
 
   or
   
 source ifload.py -d
 
   or
   
 source ifload.py -u

 

 The script was tested on N9K using 7.0(3)I6(1) release.
 
 It should work at N5k and N7k as well.
 
 ## Sample output
 ```
Leaf# ifload -d

Collecting and processing interface statistics ...

--------------------------------------------------------------------------------------------------
Port            Descr         State Intvl   Rx Mbps  Rx %   Rx pps    Tx Mbps  Tx %   Tx pps
--------------------------------------------------------------------------------------------------
port-channel1   XXX11 Po1     up    30/30   6.5      0.0%   2002      0.1      0.0%   130
  Ethernet1/1    XXX11 E1/1    up    30/30   4.3      0.0%   920       0.0      0.0%   37
  Ethernet2/1    XXX11 E2/1    up    30/30   2.2      0.0%   1082      0.1      0.0%   93
port-channel12  XXX11 Po12    up    30/30   793.4    1.0%   96501     242.6    0.3%   48320
  Ethernet1/3    XXX11 E1/3    up    30/30   75.8     0.2%   15469     92.4     0.2%   16539
  Ethernet2/3    XXX11 E2/3    up    30/30   717.5    1.8%   81032     150.2    0.4%   31781
port-channel14  XXX12 Po14    up    30/30   510.2    0.6%   79104     680.4    0.9%   83912
  Ethernet1/2    XXX12 E1/2    up    30/30   91.5     0.2%   18344     58.2     0.1%   12981
  Ethernet2/2    XXX12 E2/2    up    30/30   418.8    1.0%   60760     622.2    1.6%   70931
 
Ethernet1/3     A-link        up    30/30   0.0      0.0%   0         0.0      0.0%   0
Ethernet1/4     B-link        up    30/30   0.0      0.0%   0         0.0      0.0%   0
Ethernet1/5     C-link        up    30/30   0.0      0.0%   0         0.0      0.0%   0
<snip>
--------------------------------------------------------------------------------------------------
IO Summary:                              1310.0                       924.8
 ```
