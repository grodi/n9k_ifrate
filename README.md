# n9k_ifload

# Description:
The script prints interface throughput/packet rate statistics in an
easy to read list format on NX-OS platforms.
Further port-channel and member interfaces are displayed in a structured way
and IO summary is calculated over all ports.

The script knows two options:
 -d: list ports with description
 -u: list ports in up state
 -du: works as well
 Without options all interfaces are shown.

To use:
     1. Copy script to N9K switch bootflash:scripts/
     2. Execute using:
 source ifload.py
   or
 source ifload.py -d
   or
 source ifload.py -u

 The script was tested on N9K using 7.0(3)I6(1) release.
 It should work at N5k and N7k as well.
