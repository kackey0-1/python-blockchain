import hashlib
import json
import logging
import sys
import time

from ecdsa import NIST256p
from ecdsa import VerifyingKey

import utils

MINING_DIFFICULTY = 3
MINING_SENDER = 'THE BLOCKCHAIN'
MINING_REWARD = 1.0

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# python3では、本来objectは不要
class BlockChain(object):
    def __init__(self, blockchain_address=None):
        self.transaction_pool = []
        self.chain = []
        self.create_block(0, self.hash({}))
        self.blockchain_address = blockchain_address
    
    def create_block(self, nonce, previous_hash):
        # ソート処理を入れることによりblockの順番を保証
        block = utils.sorted_dict_by_key({
            'timestamp': time.time(),
            'transactions': self.transaction_pool,
            'nonce': nonce,
            'previous_hash': previous_hash
        })
        self.chain.append(block)
        self.transaction_pool = []
        return block
    
    """ blockのhash化実装 """
    def hash(self, block):
        # json.dumps()により文字列に変換：ソートをダブルで保証
        sorted_block = json.dumps(block, sort_keys=True)
        return hashlib.sha256(sorted_block.encode()).hexdigest()
    
    """ transactionの実装 """
    def add_transaction(self, sender_blockchain_address, 
                        recipient_blockchain_address, value,
                        sender_public_key=None, signature=None):
        transaction = utils.sorted_dict_by_key({
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'value': float(value)
        })
        if self.verify_transaction_signature(sender_public_key, signature, transaction):
            self.transaction_pool.append(transaction)
            return True
        return False

    def verify_transaction_signature(self, sender_public_key, signature, transaction):
        sha256 = hashlib.sha256()
        sha256.update(str(transaction).encode('utf-8'))
        message = sha256.digest()
        signature_bytes = bytes().fromhex(signature)
        verifying_key = VerifyingKey.from_string(
            bytes().fromhex(sender_public_key), curve=NIST256p
        )
        verified_key = verifying_key.verify(signature_bytes, message)
        return verified_key
    
    """ Proof of Work(コンセンサスアルゴリズム): nonceの正当性を検証 """
    def valid_proof(self, transactions, previous_hash, nonce, difficulty=MINING_DIFFICULTY):
        guess_block = utils.sorted_dict_by_key({
            'transactions': transactions,
            'nonce': nonce,
            'previous_hash': previous_hash
        })
        guess_hash = self.hash(guess_block)
        return guess_hash[:difficulty] == '0'*difficulty

    """ Proof of Work: 解が求められた場合 nonce を返す """
    def proof_of_work(self):
        transactions = self.transaction_pool.copy()
        previous_hash = self.hash(self.chain[-1])
        nonce = 0
        while self.valid_proof(transactions, previous_hash, nonce) is False:
            nonce += 1
        return nonce

    def mining(self):
        self.add_transaction(
            sender_blockchain_address=MINING_SENDER,
            recipient_blockchain_address=self.blockchain_address,
            value=MINING_REWARD
        )
        nonce = self.proof_of_work()
        # block_chain.chain[-1] 1番最後のブロックを渡す
        previous_hash = self.hash(self.chain[-1])
        self.create_block(nonce, previous_hash)
        logger.info({
            'action': 'mining', 'status': 'success'
        })
        return True

    def calculate_total_amount(self, blockchain_address):
        total_amount = 0.0
        for block in self.chain:
            for transaction in block['transactions']:
                value = float(transaction['value'])
                if blockchain_address == transaction['recipient_blockchain_address']:
                    total_amount += value
                if blockchain_address == transaction['sender_blockchain_address']:
                    total_amount -= value
        return total_amount
