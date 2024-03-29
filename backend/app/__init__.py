import os
import random
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.blockchain.blockchain import Blockchain
from backend.pubsub import PubSub
from backend.wallet.transaction import Transaction
from backend.wallet.transaction_pool import TransactionPool
from backend.wallet.wallet import Wallet


app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': 'http://localhost:3000'}})
blockchain = Blockchain()
wallet = Wallet(blockchain)
transaction_pool = TransactionPool()
pubsub = PubSub(blockchain, transaction_pool)

@app.route('/')
def route_default():
    return 'Welcome to Block Chain'

@app.route('/blockchain')
def route_blockchain():
    return jsonify(blockchain.to_json())

@app.route('/blockchain/range')
def route_blockchain_range():
    start = int(request.args.get('start'))
    end = int(request.args.get('end'))

    return jsonify(blockchain.to_json()[::-1][start:end])

@app.route('/blockchain/length')
def route_blockchain_length():
    return jsonify(len(blockchain.chain))

@app.route('/blockchain/mine')
def route_blockchain_mine():
    transaction_data = transaction_pool.transactionData()
    transaction_data.append(Transaction.rewardTransaction(wallet).to_json())
    blockchain.addBlock(transaction_data)
    
    block = blockchain.chain[-1]
    pubsub.broadcast_block(block)
    transaction_pool.clearBlockchainTransaction(blockchain)

    return jsonify(block.to_json())

@app.route('/wallet/transact', methods=['POST'])
def route_wallet_transact():
    #{'recipient' : 'data', 'amount': 50}
    transaction_data = request.get_json()
    transaction = transaction_pool.existingTransaction(wallet.address)

    if transaction:
        transaction.update(wallet, transaction_data['recipient'], transaction_data['amount'])
    else:
        transaction=Transaction(wallet, transaction_data['recipient'], transaction_data['amount'])
    
    pubsub.broadcast_transaction(transaction)

    return jsonify(transaction.to_json())

@app.route('/wallet/info')
def route_wallet_info():
    return jsonify({'address': wallet.address, 'balance': wallet.balance})

@app.route('/known-addresses')
def route_known_addresses():
    known_addresses = set()

    for block in blockchain.chain:
        for transaction in block.data:
            known_addresses.update(transaction['output'].keys())
        
    return jsonify(list(known_addresses))

@app.route('/transactions')
def route_transactions():
    return jsonify(transaction_pool.transactionData())

ROOT_PORT = 5000
PORT = ROOT_PORT

if os.environ.get('PEER') == 'True':
    PORT = random.randint(5001, 6000)

    result = requests.get(f'http://localhost:{ROOT_PORT}/blockchain')
    result_blockchain = Blockchain.from_json(result.json()) 

    try:
        blockchain.replace_chain(result_blockchain.chain)
        print(f'\n--Success sync')
    except Exception as e:
        print(f'\n--Not synced: {e}')

if os.environ.get('SEED_DATA') == 'True':
    for i  in range(10):
        blockchain.addBlock([Transaction(Wallet(),Wallet().address,random.randint(2,50)).to_json(),
                             Transaction(Wallet(),Wallet().address,random.randint(2,50)).to_json()
                            ])
    for i in  range(3):
        transaction_pool.setTransaction(Transaction(Wallet(),Wallet().address,random.randint(2,50)))

        
app.run(port = PORT)