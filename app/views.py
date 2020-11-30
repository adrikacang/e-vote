import datetime
import time
import json

import requests
from flask import Flask, flash, render_template, redirect, request, url_for

from app import app

# The node with which our application interacts, there can be multiple
# such nodes as well.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
is_login = False
nik = None


@app.route('/')
def index():
    if is_login:
        return render_template('index.html',
                           title='YourEvote: A Decentralized '
                                 'Verifiable E-Vote System',
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string)
    else:    
        return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Endpoint to create a new transaction via our application.
    """
    global is_login
    global nik
    error = None
    if request.method == "POST":
        post_object = {
            'nik': request.form["nik"]
        }

        # Submit a login
        new_tx_address = "{}/login".format(CONNECTED_NODE_ADDRESS)

        try:
            response = requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
        
            if response.status_code == 200:
                is_login = True
                nik = request.form["nik"]
                return redirect(url_for('index'))
            else: 
                error = "This account has voted before"
        except requests.ConnectionError:
            error = "Unable to connect to the server"
    
    return render_template('login.html',
                           title='YourEvote: A Decentralized '
                                 'Verifiable E-Vote System',
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string, 
                           error= error)

def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')

@app.route('/vote', methods=['POST', 'GET'])
def vote():
    error = None
    if (not is_login):
        return redirect(url_for('login'))
    
    if request.method == "POST":
        name = request.form["name"]
        address = request.form["address"]
        venue_id = request.form["venue_id"]
        voted_candidate = request.form["voted_candidate"]
        # timestamp = time.time()

        post_object = {
            'nik': nik,
            'name': name,
            'address': address,
            'venue_id': venue_id,
            'voted_candidate': voted_candidate
        }
        
        print(post_object['voted_candidate'])
        print(timestamp_to_string)
        # Submit a new transaction
        new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

        try:
            response = requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
        
            if response.status_code == 201:
                flash(response.text)
                return redirect(url_for('index'))
            else: 
                error = response.text
        except requests.ConnectionError:
            error = "Unable to connect to the server"
    
    return render_template('vote.html',
                           title='Vote',
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           nik = nik, 
                           error= error)

@app.route('/verify', methods=['POST', 'GET'])
def verify():
    if (not is_login):
        return redirect(url_for('login'))
    
    if request.method == "POST":
        block_index = request.form["block_index"]
        merkle_root = request.form["merkle_root"]
        leaf_index = request.form["leaf_index"]

        post_object = {
            "block_index": block_index,
            "merkle_root": merkle_root,
            "leaf_index": leaf_index
        }
        
        # Submit a new transaction
        new_tx_address = "{}/new_transaction".format(CONNECTED_NODE_ADDRESS)

        try:
            response = requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
        
            if response.status_code == 200:
                return redirect(url_for('index'))
            else: 
                error = response.text		
        except requests.ConnectionError:
            error = "Unable to connect to the server" 
    return render_template('verify.html',                            
                            title='Verify',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string,
                            error= error)