from hashlib import sha256
import json
import time
import sqlite3

from flask import Flask, request
from merkletools import MerkleTools

import requests


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = '0'

    def compute_hash(self):
        """
        A function that return the hash of the block contents.
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()

    def merkle_tree(self):
        mt = MerkleTools(hash_type="sha256")
        for trx in self.transactions:
            trx_string = json.dumps(trx)
            mt.add_leaf(trx_string, True)
        mt.make_tree()
        return mt.get_merkle_root()

    def verify_vote(self, leaf_index, merkle_root):
        mt = MerkleTools(hash_type="sha256")
        for trx in self.transactions:
            trx_string = json.dumps(trx)
            mt.add_leaf(trx_string, True)
        mt.make_tree()
        return mt.validate_proof(mt.get_proof(leaf_index), mt.get_leaf(leaf_index), merkle_root) # True

class Blockchain:
    # difficulty of our PoW algorithm
    difficulty = 2

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 0, and
        a valid hash.
        """
        genesis_block = Block(0, [], 0, "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification includes:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not Blockchain.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    @staticmethod
    def proof_of_work(block):
        """
        Function that tries different values of nonce to get a hash
        that satisfies our difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    @classmethod
    def is_valid_proof(cls, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    @classmethod
    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "0"

        for block in chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            if not cls.is_valid_proof(block, block_hash) or \
                    previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by adding them to the block
        and figuring out Proof Of Work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block
        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        self.unconfirmed_transactions = []

        return True


app = Flask(__name__)

# the node's copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# the address to other participating members of the network
peers = set()

# endpoint to login. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/login', methods=['POST'])
def login():
    tx_data = request.get_json()
    required_fields = ["uid"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    if is_user_exist(tx_data["uid"]):
        return "Voter has been voted", 400

    return "Voter has not been voted", 200


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    tx_data = request.get_json()
    required_fields = ["name", "uid", "voted_candidate"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404
    
    if is_user_exist(tx_data["uid"]):
        return "This voter has been voted", 400

    tx_data_str = json.dumps(tx_data)
    tx_data_hash = sha256(tx_data_str.encode()).hexdigest()

    blockchain.add_new_transaction(tx_data)
    tx_leaf_index = len(blockchain.unconfirmed_transactions) - 1 #get leaf index
    register_user(tx_data['uid'])
    return "<p> Vote has been requested, please note the following data for verifaction purpose. </p> <p> vote hash: " + tx_data_hash + "</p> <p>leaf index: " +  str(tx_leaf_index) + "</p>", 201


# endpoint to return the node's copy of the chain.
# Our application will be using this endpoint to query
# all the posts to display.
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})


# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    result = blockchain.mine()
    if not result:
        return "No transactions to mine"
    else:
        # Making sure we have the longest chain before announcing to the network
        chain_length = len(blockchain.chain)
        consensus()
        if chain_length == len(blockchain.chain):
            # announce the recently mined block to the network
            announce_new_block(blockchain.last_block)
        return "<p> A new block has been mined. Please record this for verification purpose. </p> <p> block-index: {} </p> <p> merkle-root: {} </p>".format(blockchain.last_block.index, blockchain.last_block.merkle_tree()), 200


# endpoint to add new peers to the network.
@app.route('/register_node', methods=['POST'])
def register_new_peers():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    # Add the node to the peer list
    peers.add(node_address)

    # Return the consensus blockchain to the newly registered node
    # so that he can sync
    return get_chain()


@app.route('/register_with', methods=['POST'])
def register_with_existing_node():
    """
    Internally calls the `register_node` endpoint to
    register current node with the node specified in the
    request, and sync the blockchain as well as peer data.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    data = {"node_address": request.host_url}
    headers = {'Content-Type': "application/json"}

    # Make a request to register with remote node and obtain information
    response = requests.post(node_address + "/register_node",
                             data=json.dumps(data), headers=headers)

    if response.status_code == 200:
        global blockchain
        global peers
        # update chain and the peers
        chain_dump = response.json()['chain']
        blockchain = create_chain_from_dump(chain_dump)
        peers.update(response.json()['peers'])
        return "Registration successful", 200
    else:
        # if something goes wrong, pass it on to the API response
        return response.content, response.status_code


def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain


# endpoint to add a block mined by someone else to
# the node's chain. The block is first verified by the node
# and then added to the chain.
@app.route('/add_block', methods=['POST'])
def verify_and_add_block():
    block_data = request.get_json()
    block = Block(block_data["index"],
                  block_data["transactions"],
                  block_data["timestamp"],
                  block_data["previous_hash"],
                  block_data["nonce"])

    proof = block_data['hash']
    added = blockchain.add_block(block, proof)

    if not added:
        return "The block was discarded by the node", 400

    return "Block added to the chain", 201


# endpoint to query unconfirmed transactions
@app.route('/pending_tx')
def get_pending_tx():
    return json.dumps(blockchain.unconfirmed_transactions)    

# endpoint to query unconfirmed transactions
@app.route('/count_vote', methods=['GET'])
def count_vote():
    candidates = {
        "Apple": 0,
        "Banana": 0
    }
    for block in blockchain.chain:
        for transaction in block.transactions:
            voted_candidate = transaction.get('voted_candidate')
            candidates[voted_candidate] += 1
    return json.dumps(candidates)

@app.route('/verify_vote', methods=['POST'])
def verify_vote():
    block_index = request.get_json()["block_index"]
    merkle_root = request.get_json()["merkle_root"]
    leaf_index = request.get_json()["leaf_index"]

    if block_index is None or merkle_root is None or leaf_index is None:
        return "Invalid or Missing Parameters", 400

    block = blockchain.chain[block_index]
    if block.verify_vote(leaf_index, merkle_root):
        return "Your vote has been verified", 200
    else:
        return "Data is not found or has been tampered, verifiaction failed", 400

def consensus():
    """
    Our naive consensus algorithm. If a longer valid chain is
    found, our chain is replaced with it.
    """
    global blockchain

    longest_chain = None
    current_len = len(blockchain.chain)

    for node in peers:
        response = requests.get('{}chain'.format(node))
        length = response.json()['length']
        chain = response.json()['chain']
        if length > current_len and blockchain.check_chain_validity(chain):
            current_len = length
            longest_chain = chain

    if longest_chain:
        blockchain = longest_chain
        return True

    return False


def announce_new_block(block):
    """
    A function to announce to the network once a block has been mined.
    Other blocks can simply verify the proof of work and add it to their
    respective chains.
    """
    for peer in peers:
        url = "{}add_block".format(peer)
        headers = {'Content-Type': "application/json"}
        requests.post(url,
                      data=json.dumps(block.__dict__, sort_keys=True),
                      headers=headers)

# Uncomment this line if you want to specify the port number in the code
#app.run(debug=True, port=8000)


#database to register users
def register_user(uid):
  try:
    sqliteConnection = sqlite3.connect('test.db')
    cursor = sqliteConnection.cursor()

    sqlite_insert_with_param = """INSERT INTO USERS(uid) VALUES (?);"""

    cursor.execute(sqlite_insert_with_param, (uid,))
    sqliteConnection.commit()
    cursor.close()
  except sqlite3.Error as error:
    print("Failed to insert Python variable into sqlite table", error)
  finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("The SQLite connection is closed")

def is_user_exist(uid):
  try:
    result = False
    sqliteConnection = sqlite3.connect('test.db')
    cursor = sqliteConnection.cursor()

    sql_select_query = """select * from USERS where uid = ?"""
    cursor.execute(sql_select_query, (uid,))
    records = cursor.fetchall()
    for row in records:
      if row[1] == uid:
          result = True
    cursor.close()
    sqliteConnection.close()
  except sqlite3.Error as error:
    print("Failed to read data from sqlite table", error)
  finally:
    if (sqliteConnection):
      sqliteConnection.close()
      print("The SQLite connection is closed")
    return result