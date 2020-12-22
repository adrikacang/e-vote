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
uid = None
has_voted = False
success = None
error = None

@app.route('/')
def index():
    if is_login:
        return render_template('index.html',
                           title='YourEvote: A Decentralized '
                                 'Verifiable E-Vote System',
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string, 
                           has_voted = has_voted,
                           success= success,
                           error=error)
    else:    
        return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    """
    Endpoint to create a new transaction via our application.
    """
    global is_login
    global uid
    error = None
    if request.method == "POST":
        post_object = {
            'uid': request.form["uid"]
        }

        # Submit a login
        new_tx_address = "{}/login".format(CONNECTED_NODE_ADDRESS)

        try:
            response = requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
        
            if response.status_code == 200:
                is_login = True
                uid = request.form["uid"]
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
    success = None
    global has_voted

    if (not is_login):
        return redirect(url_for('login'))
    
    if request.method == "POST":
        name = request.form["name"]
        voted_candidate = request.form["voted_candidate"]
        # timestamp = time.time()

        post_object = {
            'uid': uid,
            'name': name,
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
                success = response.text
                has_voted = True
            else: 
                error = response.text
        except requests.ConnectionError:
            error = "Unable to connect to the server"
    
    return render_template('vote.html',
                           title='Vote',
                           node_address=CONNECTED_NODE_ADDRESS,
                           readable_time=timestamp_to_string,
                           has_voted= has_voted,
                           uid = uid,
                           success = success,
                           error= error)

@app.route('/mine', methods=['GET'])
def mine():
    if (not is_login):
        return redirect(url_for('login'))  
    
    else:
      error = None
      success = None
      new_tx_address = "{}/mine".format(CONNECTED_NODE_ADDRESS)
      response = requests.get(new_tx_address)
      if response.status_code == 200:
        success = response.text
      else:
        error = response.text
      return render_template('mine.html',                            
                            title='Mine',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string,
                            success=success,
                            error= error)

@app.route('/count', methods=['GET'])
def count():
    if (not is_login):
        return redirect(url_for('login'))  
    
    else:
      error = None
      success = None
      new_tx_address = "{}/count_vote".format(CONNECTED_NODE_ADDRESS)
      response = requests.get(new_tx_address)
      if response.status_code == 200:
        success = response.text
      else:
        error = response.text
      return render_template('count.html',                            
                            title='Count',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string,
                            success=success,
                            error= error)


@app.route('/verify', methods=['POST', 'GET'])
def verify():
    success = None
    error = None
    if (not is_login):
        return redirect(url_for('login'))
    
    if request.method == "POST":
        block_index = request.form["block_index"]
        merkle_root = request.form["merkle_root"]
        leaf_hash = request.form["leaf_hash"]

        post_object = {
            "block_index": int(block_index),
            "merkle_root": merkle_root,
            "leaf_hash": leaf_hash
        }
        
        # Submit a new transaction
        new_tx_address = "{}/verify_vote".format(CONNECTED_NODE_ADDRESS)

        print(json.dumps(post_object))

        try:
            response = requests.post(new_tx_address,
                    json=post_object,
                    headers={'Content-type': 'application/json'})
        
            if response.status_code == 200:
                success = response.text
            else: 
                error = response.text		
        except requests.ConnectionError:
            error = "Unable to connect to the server" 
    return render_template('verify.html',                            
                            title='Verify',
                            node_address=CONNECTED_NODE_ADDRESS,
                            readable_time=timestamp_to_string,
                            success=success,
                            error= error)


@app.route('/logout', methods=['GET'])
def logout():
    global is_login
    global uid
    global success
    global error
    global has_voted

    is_login = False
    uid = None
    success = None
    error = None
    has_voted = False

    return redirect(url_for('login'))