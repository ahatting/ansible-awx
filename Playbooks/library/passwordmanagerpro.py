# (c) 2015, Jonathan Davila <jonathan(at)davila.io>
# (c) 2017 Ansible Project

from __future__ import (absolute_import, division, print_function)

EXAMPLES = """
  - name: Using Password Manager Pro
    debug:
      msg: "{{ lookup('passwordmanagerpro','ResourceName', 'AccountName') }}"
"""

RETURN = """
  _raw:
    description:
      - Password stored in Password Manager Pro
"""

import os
import json
import urllib

from ansible.errors import AnsibleError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase

from ansible.module_utils.urls import open_url

PMP_URL = ''
PMP_AUTHTOKEN =''

if os.getenv('PMP_URL') is not None:
    PMP_URL = os.environ['PMP_URL']
else:
    raise AnsibleError("Password Manager Pro ERROR - Set PMP Url in environent variable");
if os.getenv('PMP_AUTHTOKEN') is not None:
    PMP_AUTHTOKEN = os.environ['PMP_AUTHTOKEN']
else:
    raise AnsibleError("Password Manager Pro ERROR - Set Authtoken in environent variable");



def getPMPResourceAccountDetails(resourceId,accountId):
    url = '{0}/restapi/json/v1/resources/getResourceAccountDetails?APP_AUTHTOKEN={1}&APP_NAME=Ansible&RESOURCEID={2}&ACCOUNTID={3}'.format(PMP_URL, PMP_AUTHTOKEN, resourceId , accountId)  
    print (url)
    headers = {'Content-Type':'application/json'}    
    response = open_url(url, method='GET' ,headers=headers,validate_certs=False)
    resp_json = json.loads(response.read().decode('utf-8'))
    if resp_json.get("operation").get("Details"):
       details = resp_json.get("operation").get("Details")
       resourceDetails = details.get("RESOURCEDETAILS")
       accountDetails = json.loads(details.get("ACCOUNTDETAILS"))
       if accountDetails.get("PASSWORD_REASON"):
          raise AnsibleError("Couldn't able to read password from Password Manager Pro : ",accountDetails.get("PASSWORD_REASON"))
       else:						  }
          password = accountDetails.get("PASSWORD")   
          return [password]    
    else:
       message = resp_json.get("operation").get("result").get("message")
       raise AnsibleError("Password Manager Pro ERROR -",message)
       
   
class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        resourceName = terms[0]
        accountName = terms[1]
        url = '{0}/restapi/json/v1/resources/getResourceIdAccountId?APP_AUTHTOKEN={1}&APP_NAME=Ansible&RESOURCENAME={2}&ACCOUNTNAME={3}'.format(PMP_URL, PMP_AUTHTOKEN, urllib.quote(resourceName) , urllib.quote(accountName))  
        print (url)
        headers = {'Content-Type':'application/json'}    
        response = open_url(url, method='GET' ,headers=headers,validate_certs=False)
        resp_json = json.loads(response.read().decode('utf-8'))
        resp_json = resp_json.get("operation");
        if resp_json.get("Details"):
          details = resp_json.get("Details")
          resourceId = details.get("RESOURCEID")
          accountId = details.get("ACCOUNTID")
          password = getPMPResourceAccountDetails(resourceId , accountId)
          return password        
        else:
          message = resp_json.get("result").get("message")
          raise AnsibleError("Password Manager Pro ERROR - %s " % (message))
