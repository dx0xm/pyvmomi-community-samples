#!/usr/bin/env python

"""
Written by David Martinez
Github: https://github.com/dx0xm

Script to list all portgroup vlan on existing or selected dvswitch
This is for demonstration and reference purposes.
Testing ok in Single datacenter, multiple dvswitch instances
Based on getvnicinfo.py and py-vminfo.py

To improve:
Error handling
"""


from __future__ import print_function
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import atexit
import argparse
import getpass


def get_args():
    parser = argparse.ArgumentParser(
        description='Arguments for talking to vCenter')

    parser.add_argument('-s', '--host',
                        required=True,
                        action='store',
                        help='vSpehre service to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use')

    parser.add_argument('-d', '--datacenter',
                        required=True,
                        help='name of the datacenter')

    parser.add_argument('-dvs', '--dvswitch',
                        required=False,
                        help='name of the dvswitch',
                        default='all')

    parser.add_argument('-c', '--cert_check_skip',
                        required=False,
                        action='store_true',
                        help='skip ssl certificate check')

    args = parser.parse_args()
    return args


def get_obj(content, vimtype, name):
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder,
                                                        vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def get_all_objs(content, vimtype, folder=None, recurse=True):
    if not folder:
        folder = content.rootFolder

    obj = {}
    container = content.viewManager.CreateContainerView(folder, vimtype, recurse)
    for managed_object_ref in container.view:
        obj.update({managed_object_ref: managed_object_ref.name})
    return obj


def main():
    args = get_args()
    if args.password:
        password = args.password
    else:
        password = getpass.getpass(prompt='Enter password for host %s and '
                                   'user %s: ' % (args.host, args.user))
    if args.cert_check_skip:
        context = ssl._create_unverified_context()
        si = SmartConnect(host=args.host,
                          user=args.user,
                          pwd=password,
                          port=int(args.port),
                          sslContext=context)
    else:
        si = SmartConnect(host=args.host,
                          user=args.user,
                          pwd=password,
                          port=int(args.port))

    if not si:
        print("Could not connect to the specified host using specified "
              "username and password")
        return -1

    atexit.register(Disconnect, si)

    content = si.RetrieveContent()

    dc = get_obj(content, [vim.Datacenter], args.datacenter)

    if dc is None:
        print("Failed to find the datacenter %s" % args.datacenter)
        return 0
                    
    if args.dvswitch == 'all':
        dvs_lists = get_all_objs(content, [vim.DistributedVirtualSwitch], 
                                           folder=dc.networkFolder)
    else:
        dvsn = get_obj(content, [vim.DistributedVirtualSwitch], args.dvswitch)
        if dvsn is None:
            print("Failed to find the dvswitch %s" % args.dvswitch)
            return 0
        else:
            dvs_lists = [dvsn]

    print('Datacenter Name'.ljust(40)+' :', args.datacenter)
    for dvs in dvs_lists:
        print(40*'#')
        print('Dvswitch Name'.ljust(40)+' :', dvs.name)
        print(40*'#')
        for dvs_pg in dvs.portgroup:
            vlanInfo=dvs_pg.config.defaultPortConfig.vlan
            if isinstance(vlanInfo,vim.dvs.VmwareDistributedVirtualSwitch.TrunkVlanSpec):
                vlanlist = []
                for item in vlanInfo.vlanId:
                    if item.start == item.end:
                        vlanlist.append(str(item.start)
                    else:
                        vlanlist.append(str(item.start)+'-'+str(item.end))
                print(dvs_pg.name.ljust(40) + " | Trunk | vlan id: " + ','.join(vlanlist))
            else:
                print(dvs_pg.name + " | vlan id: " + str(vlanInfo.vlanId))


if __name__ == "__main__":
    main()
