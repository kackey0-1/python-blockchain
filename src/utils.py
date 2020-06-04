import collections
import hashlib

"""
dict型の問題点
# 同じdict型
block = {'b': 2, 'a': 1}
block2 = {'a': 1, 'b': 2}

# 異なるハッシュ結果になる
print(hashlib.sha256(str(block).encode()).hexdigest())
print(hashlib.sha256(str(block2).encode()).hexdigest())

故に、dict型は順番を保証する処理が必要
"""
def sorted_dict_by_key(unsorted_dict):
    # dict型は順番を保証する処理    
    return collections.OrderedDict(sorted(unsorted_dict.items(), key=lambda d:d[0]))


"""
Blockchainの詳細表示
"""
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
    print(f'{"*"*25}')
