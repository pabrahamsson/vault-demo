#!/usr/bin/env python

import base64
import hvac
import mysql.connector
import os
import requests
from flask import Flask, render_template_string
from mysql.connector import errorcode

app = Flask(__name__)
url = os.getenv('VAULT_ADDR')
client = hvac.Client(url=url)


def db_connect(client):
    config = get_db_config()
    if not config:
        db_creds = requests.get("{url}/v1/database/creds/myreadonly".format(url=url),headers={'X-Vault-Token':client.token})
        os.environ['DB_USER'] = db_creds.json()['data']['username']
        os.environ['DB_PASS'] = db_creds.json()['data']['password']
        config = get_db_config()
    try:
        cnx = mysql.connector.connect(**config)
        return {'cnx': cnx, 'err': None}
    except mysql.connector.Error as err:
        return {'cnx': None, 'err': err.errno}


def get_db_config():
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    if not db_user or not db_pass:
        return None
    return {
        'user': db_user,
        'password': db_pass,
        'host': 'mysql',
        'database': 'sampledb'
    }


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


@app.route('/')
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


@app.route('/db')
def db():
    html="""<html>
    <body>"""
    client = get_client()
    cnx = db_connect(client)
    if cnx['err'] == errorcode.ER_ACCESS_DENIED_ERROR:
        del os.environ['DB_USER']
        del os.environ['DB_PASS']
        cnx = db_connect(client)
    cnx['cnx'].close()
    html += "<h4>Successfully connected to db</h4>"
    html += "<h5>Token: {token}</h5>".format(token=os.environ.get('VAULT_TOKEN'))
    html += "<h5>Username: {user}</h5>".format(user=os.environ.get('DB_USER'))
    html += "<h5>Password: {password}</h5>".format(password=os.environ.get('DB_PASS'))
    return render_template_string(html)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=8080)
