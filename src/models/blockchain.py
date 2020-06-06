import contextlib
import hashlib
import json
import logging
import sys
import time
import threading
import requests

from ecdsa import NIST256p
from ecdsa import VerifyingKey

from modules import utils

MINING_DIFFICULTY = 3
MINING_SENDER = 'THE BLOCKCHAIN'
MINING_REWARD = 1.0
MINING_TIMER_SEC = 20

BLOCKCHAIN_PORT_RANGE = (5000, 5003)
NEIGHBOURS_IP_RANGE_NUM = (0, 1)
BLOCKCHAIN_NEIGHBOURS_SYNC_TIME_SEC = 20

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# python3では、本来objectは不要
class BlockChain(object):
    def __init__(self, blockchain_address=None, port=None):
        self.transaction_pool = []
        self.chain = []
        self.neighbours = []
        self.create_block(0, self.hash({}))
        self.blockchain_address = blockchain_address
        self.port = port
        self.mining_semaphore = threading.Semaphore(1) # 定期実行
        self.sync_neighbours_semaphore = threading.Semaphore(1)

    def run(self):
        self.sync_neighbours()
        self.resolve_conflicts()
        self.start_mining()
    
    def set_neighbours(self):
        self.neighbours = utils.find_neighbours(
            utils.get_host(), self.port,
            NEIGHBOURS_IP_RANGE_NUM[0], NEIGHBOURS_IP_RANGE_NUM[1],
            BLOCKCHAIN_PORT_RANGE[0], BLOCKCHAIN_PORT_RANGE[1]
        )
        logger.info({'action': 'set_neighbours', 'neighbours': self.neighbours})

    def sync_neighbours(self):
        is_aquire = self.sync_neighbours_semaphore.acquire(blocking=False)
        if is_aquire:
            with contextlib.ExitStack() as stack:
                stack.callback(self.sync_neighbours_semaphore.release)
                self.set_neighbours()
                loop = threading.Timer(BLOCKCHAIN_NEIGHBOURS_SYNC_TIME_SEC, self.sync_neighbours)
                loop.start()

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

        for node in self.neighbours:
            requests.delete(f'http://{node}/transactions')

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

        if sender_blockchain_address == MINING_SENDER:
            self.transaction_pool.append(transaction)
            return True

        if self.verify_transaction_signature(sender_public_key, signature, transaction):
            # if self.calculate_total_amount(sender_blockchain_address) < float(value):
            #     logger.error({'action': 'add_transaction', 'status': 'no_value'})
            #     return False
            self.transaction_pool.append(transaction)
            return True
        return False

    """ transactionの実装 """
    def create_transaction(self, sender_blockchain_address, 
                        recipient_blockchain_address, value,
                        sender_public_key, signature):
        is_transacted = self.add_transaction(
            sender_blockchain_address, recipient_blockchain_address,
            value, sender_public_key, signature
            )
        
        if is_transacted:
            for node in self.neighbours:
                requests.put(
                    f'http://{node}/transactions',
                    json={
                        'sender_blockchain_address': sender_blockchain_address,
                        'recipient_blockchain_address': recipient_blockchain_address,
                        'value': value,
                        'sender_public_key': sender_public_key,
                        'signature': signature,
                    }
                )

        return is_transacted

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
        # if not self.transaction_pool:
        #     return False

        self.add_transaction(
            sender_blockchain_address=MINING_SENDER,
            recipient_blockchain_address=self.blockchain_address,
            value=MINING_REWARD
        )
        nonce = self.proof_of_work()
        # block_chain.chain[-1] 1番最後のブロックを渡す
        previous_hash = self.hash(self.chain[-1])
        self.create_block(nonce, previous_hash)
        logger.info({'action': 'mining', 'status': 'success'})

        for node in self.neighbours:
            requests.put(f'http://{node}/consensus')

        return True
    
    def start_mining(self):
        # blocking=Falseにすることで異なるスレッドでself.mining()が実行されている場合
        # self.mining()を実行しない
        is_aquire = self.mining_semaphore.acquire(blocking=False)
        if is_aquire:
            with contextlib.ExitStack() as stack:
                # self.mining()でException発生した場合、self.mining_semaphore.release()が実行できなくなることを避けるため
                # with contextlib.ExitStack() as stackを利用してコールバック関数を指定
                stack.callback(self.mining_semaphore.release)
                self.mining()
                loop = threading.Timer(MINING_TIMER_SEC, self.start_mining)
                loop.start()
                
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

    # コンセンサス検証
    def valid_chain(self, chain):
        pre_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            if block['previous_hash'] != self.hash(pre_block):
                return False
            if not self.valid_proof(
                block['transactions'], block['previous_hash'],
                block['nonce'], MINING_DIFFICULTY):
                return False
        
            pre_block = block
            current_index += 1
        return True

    def resolve_conflicts(self):
        longest_chain = None
        max_length = len(self.chain)
        for node in self.neighbours:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                response_json = response.json()
                chain = response_json['chain']
                chain_length = len(chain)
                if chain_length > max_length and self.valid_chain(chain):
                    max_length = chain_length
                    longest_chain = chain
        
        if longest_chain:
            self.chain = longest_chain
            logger.info({'action': 'resolve_conflicts', 'status': 'replaced'})
            return True

        logger.info({'action': 'resolve_conflicts', 'status': 'not_replaced'})
        return False



