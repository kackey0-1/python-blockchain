import hashlib
import json
import logging
import sys
import time

import utils

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# python3では、本来objectは不要
class BlockChain(object):
    def __init__(self):
        self.transaction_pool = []
        self.chain = []
        self.create_block(0, self.hash({}))
    
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
    def add_transaction(self, sender_blockchain_address, recipient_blockchain_address, value):
        transaction = utils.sorted_dict_by_key({
            'sender_blockchain_address': sender_blockchain_address,
            'recipient_blockchain_address': recipient_blockchain_address,
            'value': float(value)
        })
        self.transaction_pool.append(transaction)
        return True
    
    """ Proof of Work(コンセンサスアルゴリズム): nonceの正当性を検証 """
    def test(self):
        return None

def pprint(chains):
    for i, chain in enumerate(chains):
        print(f'{"="*25} Chain {i} {"="*25}')
        for k, v in chain.items():
            if k == 'transactions':
                print(k)
                for d in v:
                    print(f'{"-"*40}')
                    for kk, vv in d.items():
                        print(f'{kk:30}{vv}')
            else:
                print(f'{k:15}{v}')
    print(f'{"*"}*25')

# Pythonでは、インポートされたファイルの中身は実行される
# ですので単にインポートしただけなのに main() => print("Hello") と処理が実行されてしまいます。
# 単にPythonファイルをインポートして、main関数を再利用しようとしただけなのに実行されてしまう。 
# import re や from datetime import datetime とするだけで自動でプログラムが動くと迷惑
# インポートされた際にプログラムが動かないようにするために、以下のように if __name__ == "__main__": というif文を書く
if __name__ == '__main__':
    block_chain = BlockChain()
    pprint(block_chain.chain)

    block_chain.add_transaction('A', 'B', 1.0)
    # block_chain.chain[-1] 1番最後のブロックを渡す
    previous_hash = block_chain.hash(block_chain.chain[-1])
    block_chain.create_block(5, previous_hash)
    pprint(block_chain.chain)

    block_chain.add_transaction('C', 'D', 2.0)
    block_chain.add_transaction('X', 'Y', 3.0)
    previous_hash = block_chain.hash(block_chain.chain[-1])
    block_chain.create_block(2, previous_hash)
    pprint(block_chain.chain)
