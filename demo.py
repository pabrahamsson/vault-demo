#!/usr/bin/env python

import hvac
import requests
from flask import Flask

demo = Flask(__name__)
url = 'http://pa-vault.pa-vault.svc:8200'

@demo.route('/')
def secrets():
    client = hvac.Client(url=url)
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

@demo.route('/db')
def db():
    client = hvac.Client(url=url)
    f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
    jwt = f.read()
    k8s_token = client.auth_kubernetes(role="app-role", jwt=jwt, mount_point="kubernetes-demo")['auth']['client_token']
    db_token = client.create_token(policies=['demo-db-read'], lease='1h')['auth']['client_token']
    db_creds = requests.get("{url}/v1/database/creds/myreadonly".format(url=url),headers={'X-Vault-Token':db_token})['data']
    return db_creds

if __name__ == '__main__':
    demo.run(host="0.0.0.0",port=8080)
