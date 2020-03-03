#!/usr/bin/env python

import hvac
import mysql.connector
import os
import requests
from flask import Flask, render_template
from mysql.connector import errorcode

demo = Flask(__name__)
url = 'http://pa-vault.pa-vault.svc:8200'
client = hvac.Client(url=url)


def get_client():
    client.token = os.environ.get('VAULT_TOKEN')
    if client.is_authenticated():
        client.renew_token()
    else:
        f = open('/var/run/secrets/kubernetes.io/serviceaccount/token')
        jwt = f.read()
        client.auth_kubernetes(role="app-role", jwt=jwt, mount_point="kubernetes-demo")
    os.environ['VAULT_TOKEN'] = client.token
    return client


@demo.route('/')
def secrets():
    client = get_client()
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
    html="""<html>
    <body>"""
    client = get_client()
    db_creds = requests.get("{url}/v1/database/creds/myreadonly".format(url=url),headers={'X-Vault-Token':client.token})
    try:
        cnx = mysql.connector.connect(
                user=db_creds.json()['data']['username'],
                password=db_creds.json()['data']['password'],
                host='mysql',
                database='sampledb'
        )
        html + "<h4>Connected to sampledb</h4>"
        html + "<h4>" + db_creds.text + "</h4>"
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
            html + "<h4>Check them creds</h4>"
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
            html + "<h4>Um, no record of that db</h4>"
        else:
            print(err)
            html + "<h4>" + err + "</h4>"
    else:
        cnx.close()
    html + '</body>\n</html>'
    return render_template(html)

if __name__ == '__main__':
    demo.run(host="0.0.0.0",port=8080)
