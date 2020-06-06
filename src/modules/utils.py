import collections
import hashlib
import re
import socket
import logging

logger = logging.getLogger(__name__)

# 192.168.0.24 (1, 3) prefix_host=192.168.0, last_ip=24
RE_IP = re.compile('(?P<prefix_host>^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.)(?P<last_ip>\\d{1,3}$)')

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

def is_found_host(target, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((target, port))
            return True
        except Exception as ex:
            logger.error({
                'action': 'is_found_host',
                'target': target,
                'port': port,
                'ex': ex
            })
            return False

"""
address range, port range
を指定してノードを検索
"""
def find_neighbours(my_host, my_port, start_ip_range, end_ip_range, start_port, end_port):
    # 192.168.0.24 (1, 3)
    address = f'{my_host}:{my_port}'
    m = RE_IP.search(my_host)
    if not m:
        return None
    
    prefix_host = m.group('prefix_host')
    last_ip = m.group('last_ip')

    neighbours = []
    for guess_port in range(start_port, end_port):
        for ip_range in range(start_ip_range, end_ip_range):
            guess_host = f'{prefix_host}{int(last_ip)+int(ip_range)}'
            guess_address = f'{guess_host}:{guess_port}'
            if is_found_host(guess_host, guess_port) and not guess_address == address:
                neighbours.append(guess_address)
    return neighbours

def get_host():
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as ex:
        logger.debug({'action': 'get_host', 'ex': ex})
    return '127.0.0.1'

if __name__ == '__main__':
    # print(is_found_host('127.0.0.1', 5000))
    # print(find_neighbours('127.0.0.1', 5000, 0, 3, 5000, 5003))
    print(get_host())

