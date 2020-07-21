#!/usr/bin/python3

import base64
import datetime
import re
import subprocess

TCPDUMP_CMD = ['tcpdump', '-s 1024', '-l', '-v', '-n', "tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x47455420"]

def http_connections():
    """
    Dumps the output of the tcpdump process as lists of connection details 
    """
    process = subprocess.Popen(TCPDUMP_CMD, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True)
    with process:
        lines = []
        for line in process.stdout:
            if line == '\t\n':
                yield lines
                lines = []
            else:
                lines.append(line)

def connection_seq():
    """
    Splits out interesting connections from the list of all http connections
    """
    for connection in http_connections():
        res = {}
        auth_lines = [line for line in connection if 'Authorization: Basic' in line]
        if not auth_lines:
            continue
        resource = re.match(r'.GET (.*?) HTTP\/.*', connection[2])
        if not resource:
            print('No resource found in ' + connection[2])
            continue
        res['resource'] = resource[1]
        user_key = auth_lines[-1].split(' ')[-1][:-1]
        res['user'] = base64.b64decode(user_key).split(b':')[0].decode('utf8')
        res['dst_port'] = connection[1].split('>')[0].split('.')[-1][:-1]
        res['time'] = datetime.datetime.now()
        yield res

def kill_tcp_connection(dst_port):
    print('killing connection with dest port ' + dst_port)
    cmd = ['timeout', '10s', 'tcpkill', 'dst', 'port', dst_port]
    process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    safe_time = datetime.timedelta(seconds=120)
    user_connections = {}
    for connection in connection_seq():
        user = connection['user']
        path = connection['resource']
        print(user, 'has requested', path)
        if connection['resource'][-1] != '/':
            connections_for_user = user_connections.get(user, [])
            connections_for_user = [conn for conn in connections_for_user
                                    if datetime.datetime.now() - conn['time'] < safe_time]

            while len(connections_for_user):
                conn = connections_for_user.pop(0)
                print('killing ongoing download for', conn['resource'])
                kill_tcp_connection(conn['dst_port'])

            connections_for_user.append(connection)
            user_connections[connection['user']] = connections_for_user

if __name__ == '__main__':
    main()

