#!/usr/bin/env python3

import os
import re
import ldap3
import json
import configparser
import argparse
import ssl

parser = argparse.ArgumentParser(
    description='Script to obtain host inventory from AD')
parser.add_argument('--list', action='store_true',
                    help='prints a json of hosts with groups and variables')
parser.add_argument('--host', help='returns variables of given host')
args = parser.parse_args()


class ADAnsibleInventory():

    def __init__(self):
        #directory = os.path.dirname(os.path.abspath(__file__))
        #configfile = directory + '/tmp/ldap-ad.ini'
        #config = configparser.ConfigParser()
        #config.read(configfile)
        username = os.environ.get("LDAP_USERNAME")
        password = os.environ.get("LDAP_PASSWORD")
        basedn = os.environ.get("LDAP_BASEDN")
        ldapuri = os.environ.get("LDAP_URI")
        port = os.environ.get("LDAP_PORT")
        ca_file = ""
        #adfilter = "(&(sAMAccountType=805306369))"
        adfilter = "(objectClass=computer)"

        self.inventory = {"_meta": {"hostvars": {}}}
        self.ad_connect(ldapuri, username, password, port, ca_file)
        self.get_hosts(basedn, adfilter)
        self.org_hosts(basedn)
        if args.list:
            print(json.dumps(self.inventory, indent=2))
        if args.host is not None:
            try:
                print(self.inventory['_meta']['hostvars'][args.host])
            except Exception:
                print('{}')

    def ad_connect(self, ldapuri, username, password, port, ca_file):
        server = ldap3.Server(ldapuri, use_ssl=False)
        conn = ldap3.Connection(server,
                                auto_bind=True,
                                user=username,
                                password=password,
                                authentication=ldap3.SIMPLE)
        self.conn = conn

    def get_hosts(self, basedn, adfilter):
        self.conn.search(search_base=basedn,
                         search_filter=adfilter,
                         attributes=['cn', 'dnshostname'])
        self.conn.response_to_json
        self.results = self.conn.response

    def org_hosts(self, basedn):
        # Removes CN,OU, and DC and places into a list
        basedn_list = (re.sub(r"..=", "", basedn)).split(",")
        for computer in self.results:
            org_list=[]
            if 'dn' in computer:
                org_list = (re.sub(r"..=", "", computer['dn'])).split(",")
                # Remove hostname
            if org_list:
                del org_list[0]
                

            # Removes all excess OUs and DC
            
            for count in range(0, (len(basedn_list)-1)):
                if org_list:
                    del org_list[-1]

            # Reverse list so top group is first
            org_list.reverse()

            org_range = range(0, (len(org_list)))
            for orgs in org_range:
                if computer['attributes']['dNSHostName']:
                    if orgs == org_range[-1]:
                        self.add_host(org_list[orgs],
                                      computer['attributes']['dNSHostName'])
                    else:
                        self.add_group(group=org_list[orgs],
                                       children=org_list[orgs+1])

    def add_host(self, group, host):
        host = (''.join(host)).lower()
        group = (''.join(group)).lower()
        if group not in self.inventory.keys():
            self.inventory[group] = {'hosts': [], 'children': []}
        self.inventory[group]['hosts'].append(host)

    def add_group(self, group, children):
        group = (''.join(group)).lower()
        children = (''.join(children)).lower()
        if group not in self.inventory.keys():
            self.inventory[group] = {'hosts': [], 'children': []}
        if children not in self.inventory[group]['children']:
            self.inventory[group]['children'].append(children)


if __name__ == '__main__':
    ADAnsibleInventory()