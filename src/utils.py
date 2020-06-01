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

