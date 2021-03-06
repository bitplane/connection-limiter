#!/usr/bin/python3
"""
Crude, hacky incoming connection limiter for web server
"""

import base64
import datetime
import re
import subprocess


def tcp_filter_string(filter_string):
    """
    Create a packet capture filter based on the first string seen in a TCP stream
    """
    extract_high_nibble = '(({} & 0xf0) >> 2)'
    tcp_data_start = extract_high_nibble.format('tcp[12:1]')
    string_in_hex = bytes(filter_string, encoding='utf8').hex() 
    return "tcp[{start}:{length}] = 0x{hex_str}".format(start=tcp_data_start,
                                                        length=len(filter_string),
                                                        hex_str=string_in_hex)

def http_connections():
    """
    Dumps the output of the tcpdump process as lists of connection details
    """
    tcpdmp_cmd = ['tcpdump', '-s 1024', '-l', '-v', '-n', tcp_filter_string('GET ')]

    process = subprocess.Popen(tcpdmp_cmd, stdout=subprocess.PIPE,
                               bufsize=1, universal_newlines=True)
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
    """
    Close a TCP connection that we don't own, based on the destination port number.
    """
    print('killing connection with dest port ' + dst_port)
    cmd = ['timeout', '10s', 'tcpkill', 'dst', 'port', dst_port]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run():
    """
    Main loop
    """
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

            while connections_for_user:
                conn = connections_for_user.pop(0)
                print('killing ongoing download for', conn['resource'])
                kill_tcp_connection(conn['dst_port'])

            connections_for_user.append(connection)
            user_connections[connection['user']] = connections_for_user


if __name__ == '__main__':
    run()
