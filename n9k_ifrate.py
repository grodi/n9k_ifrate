#!/usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Athor:       grodi, chgrodde@googlemail.com
# Version:     0.5
# Description:
# The script prints interface throughput/packet rate statistics in an
# easy to read list format on NX-OS platforms.
# Further port-channel and member interfaces are displayed in a structured way
# and there will be a IO summary calculated over all ports.
#
# The script knows three options:
#  -d: list ports with description
#  -u: list ports in up state
#  -du: works as well
#
# Without any options all interfaces are shown.
#
# To use:
#   1. Copy script to N9K switch bootflash:scripts/
#   2. Execute using:
# source ifrate.py
#   or
# source ifrate.py -d
#   or
# source ifrate.py -u
#
#   3. Configure an alias, e.g.
# cli alias name ifrate source n9k_ifrate.py
#
# The script was tested on N9K using 7.0(3)I6(1) release.
# It should work at N5k and N7k as well.
#

from __future__ import division

import sys
import xml.etree.cElementTree as ET
from optparse import OptionParser

try:
    from cli import cli
except:
    ignore = None

def args_parser():
    usage = "\n\tsource n9k_ifrate.py [option]\n\t -d, list ports with description \n\t -u, list ports in up state"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--description",
                      action="store_true",
                      dest="d_flag",
                      default=False,
                      help="list ports with description")
    parser.add_option("-u", "--up",
                      action="store_true",
                      dest="u_flag",
                      default=False,
                      help="list ports in up state")

    options, args = parser.parse_args()

    if len(args) >= 1:
        parser.error("No valid option!")

    return options

def if_counter(l_interface, l_i, l_if_manager, l_pc_member_flag, l_rx_bps_sum, l_tx_bps_sum, l_nflag, l_uflag):
    # print l_nflag, l_uflag
    if_descr = "---"

    state = l_i.find(l_if_manager + 'state').text
    desc = l_i.find(l_if_manager + 'desc', '')

    # return in case of up flag and interface down
    if l_uflag:
        if state == 'down':
            return l_rx_bps_sum, l_tx_bps_sum
    # return in case of descr flag and no description configured
    if l_nflag:
        if desc is None:
            return l_rx_bps_sum, l_tx_bps_sum
        else:
            if_descr = desc.text[:20]

    if desc is not None:
        if_descr = desc.text[:20]

    bw = int(l_i.find(l_if_manager + 'eth_bw').text)
    rx_intvl = l_i.find(l_if_manager + 'eth_load_interval1_rx').text
    rx_bps = int(l_i.find(l_if_manager + 'eth_inrate1_bits').text)
    l_rx_bps_sum = l_rx_bps_sum + rx_bps
    rx_mbps = round((rx_bps / 1000000), 1)
    rx_pcnt = round((rx_bps / 1000) * 100 / bw, 1)
    rx_pps = l_i.find(l_if_manager + 'eth_inrate1_pkts').text
    tx_intvl = l_i.find(l_if_manager + 'eth_load_interval1_tx').text
    tx_bps = int(l_i.find(l_if_manager + 'eth_outrate1_bits').text)
    l_tx_bps_sum = l_tx_bps_sum + tx_bps
    tx_mbps = round((tx_bps / 1000000), 1)
    tx_pcnt = round((tx_bps / 1000) * 100 / bw, 1)
    tx_pps = l_i.find(l_if_manager + 'eth_outrate1_pkts').text

    if l_pc_member_flag:
        l_table = " {0:16}{1:26}{2:6}{3:8}{4:9}{5:7}{6:12}{7:9}{8:7}{9:9}"
    else:
        l_table = "{0:17}{1:26}{2:6}{3:8}{4:9}{5:7}{6:12}{7:9}{8:7}{9:9}"

    print l_table.format(l_interface, if_descr, state, rx_intvl + '/' + tx_intvl, str(rx_mbps), str(rx_pcnt) + '%',
                         rx_pps, str(tx_mbps), str(tx_pcnt) + '%', tx_pps)
    sys.stdout.flush()
    return l_rx_bps_sum, l_tx_bps_sum


### Main Program ###

### Get script options
# d_flag: show interfaces with a description on it
# u_flag: show interfaces with up status

option = args_parser()

print
print 'Collecting and processing interface statistics ...'
print

# keeps the sum of bps over all phy interfaces
rx_bps_sum = 0
tx_bps_sum = 0

sys.stdout.flush()
# get interface information in xml format
if_tree = ET.ElementTree(ET.fromstring(cli('show interface | xml | exclude "]]>]]>"')))
if_data = if_tree.getroot()
if_manager = '{http://www.cisco.com/nxos:1.0:if_manager}'

# get port-channel sum in xml format
pcm_tree = ET.ElementTree(ET.fromstring(cli('show port-channel sum | xml | exclude "]]>]]>"')))
pcm_data = pcm_tree.getroot()
pcm = '{http://www.cisco.com/nxos:1.0:eth_pcm_dc3}'

table = "{0:17}{1:26}{2:6}{3:8}{4:9}{5:7}{6:12}{7:9}{8:7}{9:9}"
print '-----------------------------------------------------------------------------------------------------------------'
print table.format("Port", "Descr", "State", "Intvl", "Rx Mbps", "Rx %", "Rx pps", "Tx Mbps", "Tx %", "Tx pps")
print '-----------------------------------------------------------------------------------------------------------------'

# Find port-channel interfaces
for p in pcm_data.iter(pcm + 'ROW_channel'):
    try:
        pc = p.find(pcm + 'port-channel').text
        for i in if_data.iter(if_manager + 'ROW_interface'):
            try:
                interface = i.find(if_manager + 'interface').text
                if interface == pc:
                    pc_member_flag = False
                    # fetching and printing interface counter
                    # port-channel bps are not added to the sum
                    rx_unused, tx_unused = if_counter(interface, i, if_manager, pc_member_flag, rx_bps_sum, tx_bps_sum,
                                                      option.d_flag, option.u_flag)
                    i.clear()
            except AttributeError:
                pass
        # Find port-channel member interfaces
        for m in p.iter(pcm + 'ROW_member'):
            try:
                member = m.find(pcm + 'port').text
                for i in if_data.iter(if_manager + 'ROW_interface'):
                    try:
                        interface = i.find(if_manager + 'interface').text
                        if interface == member:
                            pc_member_flag = True
                            # fetching and printing interface counter
                            rx_bps_sum, tx_bps_sum = if_counter(interface, i, if_manager, pc_member_flag, rx_bps_sum,
                                                                tx_bps_sum, option.d_flag, option.u_flag)
                            i.clear()
                    except AttributeError:
                        pass
            except AttributeError:
                pass
    except AttributeError:
        pass

print

# Find and display non port-channel interfaces
for i in if_data.iter(if_manager + 'ROW_interface'):
    try:
        pc_member_flag = False
        interface = i.find(if_manager + 'interface').text
        # fetching and printing interface counter
        rx_bps_sum, tx_bps_sum = if_counter(interface, i, if_manager, pc_member_flag, rx_bps_sum, tx_bps_sum,
                                            option.d_flag, option.u_flag)
    except AttributeError:
        pass

rx_mbps_sum = round((rx_bps_sum / 1000000), 1)
tx_mbps_sum = round((tx_bps_sum / 1000000), 1)
table = "{0:17}{1:26}{2:6}{3:8}{4:9}{5:7}{6:12}{7:9}{8:7}{9:9}"
print '-----------------------------------------------------------------------------------------------------------------'
print table.format("IO Summary:", " ", " ", " ", str(rx_mbps_sum), " ", " ", str(tx_mbps_sum), " ", " ")
sys.exit()
