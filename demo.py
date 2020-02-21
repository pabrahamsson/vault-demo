#!/usr/bin/env python

import hvac
from flask import Flask

demo = Flask(__name__)

@demo.route('/')
def secrets():
    client = hvac.Client(url='https://pa-vault.apps.s11.core.rht-labs.com')
    f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
    jwt = f.read()
    client.auth_kubernetes(role="app-role", jwt=jwt, mount_point="kubernetes-demo")

    secret_path = 'producta/servicea'
    kv_secret = client.secrets.kv.read_secret_version(path=secret_path)
    username = kv_secret['data']['data']['username']
    password=kv_secret['data']['data']['password']
    return {
        "username": username,
        "password": password,
    }

if __name__ == '__main__':
    demo.run(host="0.0.0.0")
