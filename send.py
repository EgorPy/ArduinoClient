import requests
from config import REAL_TOKEN, XOR_KEY

result = ''.join(f'{ord(c) ^ ord(XOR_KEY[i % len(XOR_KEY)]):02x}' for i, c in enumerate(REAL_TOKEN))
print(result)

headers = {
    'X-Token': result,
}

files = {
    'action': (None, 'short'),
}

response = requests.post('http://62.197.49.192:5000/set_command', headers=headers, files=files)
