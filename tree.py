from merkletools import MerkleTools
from hashlib import sha256
import json

# transactions =  [{"name": "R Muh Adrian Septiandry", "nik": "31750205099500031111", "address": "Camar 3 BC 19", "venue_id": "2", "voted_candidate": "Jokowi", "timestamp": 1606492536.3499079}, {"name": "Endang Sanitowati", "nik": "31750205099500012382", "address": "Camar 3 BC 19", "venue_id": "2", "voted_candidate": "Prabowo", "timestamp": 1606492561.7882664}]
transactions = [{
    "name":"R Muh Adrian Septiandry",
    "nik":"31750205099500031111",
    "address":"Camar 3 BC 19",
    "venue_id":"2",
    "voted_candidate":"Jokowi"
}]
mt = MerkleTools(hash_type="sha256")

for trx in transactions:
    trx_string = json.dumps(trx)
    mt.add_leaf(trx_string, True)

print("print leaf count", mt.get_leaf_count())

mt.make_tree()

print("root:", mt.get_merkle_root()) # root: '765f15d171871b00034ee55e48ffdf76afbc44ed0bcff5c82f31351d333c2ed1'

print("get proof 0", mt.get_proof(0)) 
print("get proof 1", mt.get_proof(1)) 

print("get leaf 0", mt.get_leaf(0))
print("sha256 hexdigest", sha256(json.dumps(transactions[0]).encode()).hexdigest())


print("validate", mt.validate_proof(mt.get_proof(0), '1e24510073e374315875928d345eb689387fca89c3d2872050898b5628672229', mt.get_merkle_root()))  # True