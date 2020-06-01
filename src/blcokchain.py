import logging
import sys
import time

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# python3では、本来objectは不要
class BlockChain(object):
    def __init__(self):
        self.transaction_pool = []
        self.chain = []
        self.create_block(0, 'init hash')
    
    def create_block(self, nonce, previous_hash):
        block = {
            'timestamp': time.time(),
            'transactions': self.transaction_pool,
            'nonce': nonce,
            'previous_hash': previous_hash
        }
        self.chain.append(block)
        self.transaction_pool = []
        return block

def pprint(chains):
    for i, chain in enumerate(chains):
        print(f'{"="*25} Chain {i} {"="*25}')
        for k, v in chain.items():
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
    block_chain.create_block(5, 'hash 1')
    pprint(block_chain.chain)
    block_chain.create_block(2, 'hash 2')
    pprint(block_chain.chain)

