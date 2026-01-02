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
# Version:     1.1
# Description:
# This script shows the interface throughput and packet rate statistics in an
# easy to read table format on NX-OS platforms.
# Port-channel and member interfaces are displayed in a hirachical order.
# A throughput summary is calculated for Rx and Tx over all ports. In nativ unicast environments ingress and egress should be equal.
# To reduce the table width a filter can be configured which shortens the interface descriptions as well as cdp/lldp hostnames. 
#  event manager environment RMLIST "connected-to-, .mydom.dom, yyy-, zzz"   
#
# To shorten the the table width inter
#
# The script knows five options:
#  -d: list ports with description
#  -u: list ports in up state
#  -r: adding a column with input/output discards
#  -n: looks for cdp neighbor or, if no cdp neighbor, try lldp
#  -l: shows load interval used for rate calculation. Default is 30 sec.
#  -du: any combination of options works as well
#
# Without an option all interfaces are shown. Discards or neighbors columns are not displayed in this case.
#
# To use:
#   1. Copy the script to the Nexus switch directory bootflash:scripts/
#   2. Execute using:
# source nx_ifrate.py
#   or
# source nx_ifrate.py -d
#   or
# source nx_ifrate.py -u
#
#   3. Configure an alias, e.g.
# cli alias name ifrate source nx_ifrate.py
#
#   4. Configure a list removing unnessacary characters form interfaces description or the cdp/lldp neighbor hostname
# event manager environment RMLIST "connected-to-, xxx-, yyy-, zzz"
#
# The script was tested on N9K using 10.6.1 release.
# 
#

from __future__ import division

import sys
import xml.etree.cElementTree as ET
import re
from optparse import OptionParser

try:
    from cli import cli
except:
    ignore = None

# max column width
max_descr_width = 23      # interface description
max_neigh_width = 30      # cdp/lldp neighbor column, must be >= 13



def args_parser():
    usage = (
        "\n  source nx_ifrate.py [option(s)]\n"
        "      valid options are -d, -u, -r or -n \n"
        "      or any combination of options in the form of -d -u or -du"
        )
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
    parser.add_option("-r", "--discards",
                      action="store_true",
                      dest="discard_flag",
                      default=False,
                      help="show input/output discards per interface")
    parser.add_option("-n", "--neighbor",
                      action="store_true",
                      dest="neigh_flag",
                      default=False,
                      help="show the CDP or LLDP neighbor attached to an interface")
    parser.add_option("-l", "--load",
                      action="store_true",
                      dest="l_flag",
                      default=False,
                      help="shows load interval used for rate calculation. Default is 30 sec.")
    
    options, args = parser.parse_args()

    if len(args) > 0:
        parser.error("No valid option!")
    return options


def rmlist_parser():
    ## Get character remove-list from event manager environment command
    # Run CLI command to fetch the line(s)
    try:
        env_cmd = cli('show running-config | include "event manager environment"')
    except Exception as e:
        print(f"Error running command: {e}")
        env_cmd = None

    # init remove list with none
    rm_list = None

    if env_cmd:
        # Regex pattern for: event manager environment <VAR> "<VALUE>"
        pattern = r"event manager environment\s+(\S+)\s+\"([^\"]+)\""
        matches = re.findall(pattern, env_cmd)
        print ("Raw matches: ", matches)

        params = {key: value for key, value in matches}

        # convert to dict RMLIST to a list
        if "RMLIST" in params:
            raw_value = params["RMLIST"]
            # split into list
            rm_list = [item.strip() for item in raw_value.split(",") if item.strip()]
            print(f"List form: {rm_list}")
        else:
            #print("RMLIST not found.")
            print ()
            
    return rm_list


def getcdpnbor(l_interface, l_cdp_root, l_rm_list):
    cdpd = '{http://www.cisco.com/nxos:1.0:cdpd}'
    cdpresult = ('---')
    for c in l_cdp_root.iter(cdpd + 'ROW_cdp_neighbor_brief_info'):
        try:
            intfid = c.find(cdpd + 'intf_id').text
            if intfid == l_interface:
                # optimize remote hostname
                devid = c.find(cdpd + 'device_id').text
                devid = ((devid.split("("))[0])
                devid = ((devid.split("."))[0])
                # optimize description width
                for r in (l_rm_list or []):
                        devid = devid.replace(r, "")
                # optimize remote interface name
                portid = c.find(cdpd + 'port_id').text
                if1 = re.findall('([E,G,T]).+', portid)
                if2 = re.findall('([0-9]*/?[0-9]*/?[0-9])+$', portid)
                if3 = "".join(if1 + if2)
                cdpresult = devid + "-" + if3
                c.clear()
                break
        except:
            pass
    return cdpresult


def getlldpnbor(l_interface, l_lldp_root, l_rm_list):
    lldp = '{http://www.cisco.com/nxos:1.0:lldp}'
    lldpresult = ('---')
    for l in l_lldp_root.iter(lldp + 'ROW_nbor'):
        try:
            lportid = l.find(lldp + 'l_port_id').text
            if1 = re.findall('(Eth).+', l_interface)
            if2 = re.findall('([0-9]*/?[0-9]*/?[0-9])+$', l_interface)
            ifshort = "".join(if1 + if2)
            if lportid == ifshort:
                # optimize remote hostname
                chassisid = l.find(lldp + 'chassis_id').text
                # optimize description width
                for r in (l_rm_list or []):
                        chassisid = chassisid.replace(r, "")
                # optimize remote interface name                
                portid = l.find(lldp + 'port_id').text
                if1 = re.findall('([E,G,T]).+', portid)
                if2 = re.findall('([0-9/:]*)$', portid)
                if3 = "".join(if1 + if2)
                lldpresult = chassisid + "-" + if3
                l.clear()
                break
        except:
            pass
    return lldpresult


def if_counter(l_interface, l_i, l_if_manager, l_pc_member_flag, l_rx_bps_sum, l_tx_bps_sum, l_dflag, l_uflag, l_lflag, l_discard_flag, l_neigh_flag, l_cdp_root, l_lldp_root, l_rm_list):
    #print l_rm_list

    state = l_i.find(l_if_manager + 'state').text
    desc = l_i.find(l_if_manager + 'desc', '')

    # return if up flag set but interface down
    if l_uflag:
        if state == 'down':
            return l_rx_bps_sum, l_tx_bps_sum
        
    # return if descr flag set but no description configured
    if l_dflag and desc is None:
        return l_rx_bps_sum, l_tx_bps_sum

    if_descr = "---" # initial interface description 
    # optimize interface description
    if desc is not None:
        if_descr = desc.text
        # optimize description width
        for r in (l_rm_list or []):
                if_descr = if_descr.replace(r, "")
        if_descr = if_descr.replace("Ethernet", "e")      # always replace Ethernet with e
        if_descr = if_descr[:max_descr_width-1]
        

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

    # get input/output discards in case of -r option
    if l_discard_flag:
        indiscards = l_i.find(l_if_manager + 'eth_indiscard').text
        outdiscards = l_i.find(l_if_manager + 'eth_outdiscard').text
 
    if l_pc_member_flag:
        prefix = " "  # leading space
        first_col_width = 16
    else:
        prefix = ""   # no leading space
        first_col_width = 17


    # look for CDP/LLDP neighbor information in case of -n option
    if l_neigh_flag:
        # look for CDP neighbors
        if l_cdp_root is not None:
            neigh_result = getcdpnbor(l_interface, l_cdp_root, l_rm_list)
        else:
            neigh_result = "---"

        # Search for LLDP neighbors if no CDP neighbor available
        if l_lldp_root is not None and neigh_result == "---":
            neigh_result = getlldpnbor(l_interface, l_lldp_root, l_rm_list)
    
    # print a nice row to screen
    print(
        f'{prefix}{l_interface:{first_col_width}}'
        f'{if_descr:{max_descr_width}}'
        + (f'{neigh_result[:max_neigh_width-1]:{max_neigh_width}}' if l_neigh_flag else '')
        + f'{state:6}'
        + (f'{rx_intvl + "/" + tx_intvl:8}' if l_lflag else '')
        + f'{rx_mbps:<9.1f}'
        f'{(str(rx_pcnt) + "%"):7}'
        f'{rx_pps:<9}'
        + (f'{indiscards:8}' if l_discard_flag else '')
        + f'{tx_mbps:<9.1f}'
        f'{(str(tx_pcnt) + "%"):7}'
        f'{tx_pps:<9}'
        + (f'{outdiscards:8}' if l_discard_flag else '')
    )

    sys.stdout.flush()
    return l_rx_bps_sum, l_tx_bps_sum


### Main Program ###

## Script options
# d_flag: show interfaces with a description on it
# u_flag: show interfaces with up status
# discard_flag: show interface input/output discards
# neigh_flag: show cdp neighbor or if not cdp try lldp neigh
# loadint_flag shows load interval used for rate calculation. Default is 30 sec.

option = args_parser()

print ()
print ("Collecting and processing interface statistics ...")
print ()

# init rx/tx-sum with 0 bps
rx_bps_sum = 0
tx_bps_sum = 0

sys.stdout.flush()

# get remove list from NX-configuration
rm_list = rmlist_parser()

# get interface information in xml format
try:
    if_tree = ET.ElementTree(ET.fromstring(cli('show interface | xml | exclude "]]>]]>"')))
    if_root = if_tree.getroot()
except Exception as e:
    print(f"Error running command: {e}")
    sys.exit()
if_manager = '{http://www.cisco.com/nxos:1.0:if_manager}'

# get port-channel sum in xml format
try:
    pcm_tree = ET.ElementTree(ET.fromstring(cli('show port-channel sum | xml | exclude "]]>]]>"')))
    pcm_root = pcm_tree.getroot()
except Exception as e:
    print(f"Error running command: {e}")
    sys.exit()
pcm = '{http://www.cisco.com/nxos:1.0:eth_pcm_dc3}'

cdp_root = False
lldp_root = False
if option.neigh_flag:
    # get CDP neighbors
    try:
        cdp_tree = ET.ElementTree(ET.fromstring(cli('show cdp neighbor | xml | exclude "]]>]]>"')))
        cdp_root = cdp_tree.getroot()
        print('Found some CDP neighbors!')
    except:
        print('No CDP neighbors found! Trying LLDP...')
        cdp_root = None

    # get LLDP neighbors
    try:
        lldp_tree = ET.ElementTree(ET.fromstring(cli('show lldp neighbor | xml | exclude "]]>]]>"')))
        lldp_root = lldp_tree.getroot()
        print('Found some LLDP neighbors!')
        print()
    except:
        print('No LLDP neighbors found!')
        lldp_root = None


# Build table header
header = (
     f"{'Port':17}{'Descr':{max_descr_width}}"
     + (f"{'C/L-Neighbor':{max_neigh_width}}" if option.neigh_flag else '')
     + f"{'State':6}"
     + (f"{'Intvl':8}" if option.l_flag else '')
     + f"{'Rx Mbps':9}{'Rx %':7}{'Rx pps':9}"
     + (f"{'InDisc':8}" if option.discard_flag else '')
     + f"{'Tx Mbps':9}{'Tx %':7}{'Tx pps':9}"
     + (f"{'OutDisc':8}" if option.discard_flag else '')
)
print ("-" * len(header))
print (header)
print ("-" * len(header))

# Find port-channel interfaces
for p in pcm_root.iter(pcm + 'ROW_channel'):
    try:
        pc = p.find(pcm + 'port-channel').text
        for i in if_root.iter(if_manager + 'ROW_interface'):
            try:
                interface = i.find(if_manager + 'interface').text
                if interface == pc:
                    pc_member_flag = False
                    # fetch the interface counter and display them
                    # port-channel bps are not added to the sum
                    rx_unused, tx_unused = if_counter(interface, i, if_manager, pc_member_flag, rx_bps_sum, tx_bps_sum,
                                                      option.d_flag, option.u_flag, option.l_flag, option.discard_flag, option.neigh_flag, cdp_root, lldp_root, rm_list)
                    i.clear()
            except AttributeError:
                pass
        # Find port-channel member interfaces
        for m in p.iter(pcm + 'ROW_member'):
            try:
                member = m.find(pcm + 'port').text
                for i in if_root.iter(if_manager + 'ROW_interface'):
                    try:
                        interface = i.find(if_manager + 'interface').text
                        if interface == member:
                            pc_member_flag = True
                            # fetch the interface counter and display them
                            rx_bps_sum, tx_bps_sum = if_counter(interface, i, if_manager, pc_member_flag, rx_bps_sum, tx_bps_sum, 
                                                                option.d_flag, option.u_flag, option.l_flag, option.discard_flag, option.neigh_flag, cdp_root, lldp_root, rm_list)
                            i.clear()
                    except AttributeError:
                        pass
            except AttributeError:
                pass
    except AttributeError:
        pass


# Find and display all other non port-channel interfaces
for i in if_root.iter(if_manager + 'ROW_interface'):
    try:
        pc_member_flag = False
        interface = i.find(if_manager + 'interface').text
        # fetch the interface counter and display them
        rx_bps_sum, tx_bps_sum = if_counter(interface, i, if_manager, pc_member_flag, rx_bps_sum, tx_bps_sum,
                                            option.d_flag, option.u_flag, option.l_flag, option.discard_flag, option.neigh_flag, cdp_root, lldp_root, rm_list)
    except AttributeError:
        pass

rx_mbps_sum = round((rx_bps_sum / 1000000), 1)
tx_mbps_sum = round((tx_bps_sum / 1000000), 1)

# print the IO summary data rate as buttom line
print("-" * len(header))
print(
    f"{'IO Summary:':17}{'':{max_descr_width}}"
    + (f"{'':{max_neigh_width}}" if option.neigh_flag else '')
    + f"{'':6}"
    + (f"{'':8}" if option.l_flag else '')
    + f"{str(rx_mbps_sum):9}{'':7}{'':9}"
    + (f"{'':8}" if option.discard_flag else '')
    + f"{str(tx_mbps_sum):9}{'':7}{'':9}"
    + (f"{'':8}" if option.discard_flag else '')
)
sys.exit()
