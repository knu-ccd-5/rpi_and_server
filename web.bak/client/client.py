''' client.py '''

import socket

def run(host='http://ccddev.azurewebsites.net', port=4000):
  with socket.socket() as s:
    s.connect((host, port))
    line = input('>')
    s.sendall(line.encode())
    res = s.recv(1024)
    print(f'={res.decode()}')

if __name__ == '__main__':
  run()