import socket
import threading
import json
import os
from typing import Dict, Tuple
import api.users, api.login_flow, api.messages, api.chats
import ipaddress
from multiprocessing import Process

from api.flask_app import app

# import so the modules are executed (defines endpoints for flask app)
from api import login_flow, chats, friends, invites, members, messages, roles, servers, users
from api import db

from flask import request
import requests

from api import server_config as sc
from uuid import uuid4




basepath = os.path.dirname(os.path.realpath(__file__))
blacklist = []

with open(os.path.join(basepath, "blacklist.txt")) as f:
    for line in f.read().split("\n"):
        if "/" in line:
            blacklist.append(ipaddress.ip_network(line))
        else:
            blacklist.append(ipaddress.ip_address(line))


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(("0.0.0.0", sc.SOCKET_PORT))

print("Server up!")
print("Running on " + str(s.getsockname()[0]) + ":" + str(s.getsockname()[1]))

connections: Dict[str, socket.socket] = {}
""" map of `{token -> socket obj}` for all connected sockets """

def handle_message(data: dict):
    payload = json.dumps({
        "author": data["author"],
        "content": data['content'],
    }).encode()
    print(f"[handle message] content={data['content']} author={data['author']}")
    print(f"^ sending to {len(connections)} sockets (incl. author)")
    
    marked_for_removal = [] # sockets that were found to be dc'ed
    # we have to remove them all last cuz dict size cant change during iteration
    
    for other in connections:
        # if other != data["token"]:
        
        # ^^^ crystaltine -> trigtbh: im still sending the message to the author just for consistency;
        # the author's client will wait for the server's confirmation that the message was indeed sent;
        # it shouldnt render on the authors side until the server confirms it was sent to all other clients asw
        try:
            connections[other].sendall(payload)
        except:
            print(f"\x1b[31mError sending to socket with token={other}, marking as removed...\x1b[0m")
            marked_for_removal.append(other)
            
    for token in marked_for_removal:
        del connections[token]

def handle_connection(conn: socket.socket, addr):
    print(f"\x1b[33mHandling connection {addr=}\x1b[0m")
    # expect them to immediately send their token
    try:
        data = conn.recv(1024)
        token = data.decode()
    except:
        print(f"\x1b[31mjust kidding ({addr} disconnected during init handshake)\x1b[0m")
        
    print(f"\x1b[32msocket {addr=} {token=} completed init handshake (connected!)\x1b[0m")
    connections[token] = conn

    # receive loop
    while True:
        try:
            data = conn.recv(1024)
        except:
            pass
        else:
            if not data:
                print(f"\x1b[31msocket {token=} {addr=} disconnected\x1b[0m")
                del connections[addr]
                return

            # data received - assume it's a sent message

            parsed = json.loads(data.decode())
            
            print(f"socket \x1b[33m{addr=} {token=}\x1b[0m received data (assuming it's a message): \x1b[33m{parsed}\x1b[0m")
            handle_message(parsed)
            

def socket_accept_thread():
    s.listen()

    while True: 
        try:
            conn, addr = s.accept()
        except OSError as err:
            # connection probably closed
            break

        # check blacklist (doesnt work for now)
        #for net in blacklist:
        #    if (isinstance(net, ipaddress.ip_address) and ipaddress.ip_address(addr[0]) == net) or (isinstance(net, ipaddress.ip_network) and ipaddress.ip_address(addr[0]) in net):
        #        print("Blocked connection from " + addr[0])
        #        conn.close()
        #        continue
        
        print(f"new socket connection from {addr}! starting thread...")
        threading.Thread(target=handle_connection, args=(conn, addr)).start()
    
socket_thread = threading.Thread(target=socket_accept_thread)
socket_thread.start()


@app.route("/")
def index():
    return "This port is running Viscord.<br>Scrapers, please go away.<br><br>Thank you <3"
    # ...

    # ip = request.remote_addr
    # json_data = requests.get(f"http://ip-api.com/json/{ip}").json()
    # print(json_data)
    # if "lat" not in json_data or "long" not in json_data:
    #     return "Error checking geolocation"
    
    # SEA_LAT = 47.6061
    # SEA_LONG = 122.3328

    # if abs(json_data["latitude"] - SEA_LAT) > 1 or abs(json_data["longitude"] - SEA_LONG) > 1:
    #     return f"<h1>Viscord</h1><br><p>This address is intended for the Viscord project.<br>Your IP address is <b>{request.remote_addr}</b><br>This service is only intended for users in or around Seattle, WA.</p>"
    # else:
    #     return "<h1>Viscord</h1><br><p>Welcome to Viscord."

def apprun():
    app.run(host=sc.HOST, port=sc.HTTP_PORT)

if __name__ == "__main__":
    http_process = Process(target=apprun)
    http_process.start()

    # cli
    while True:
        cmd = input("> ")
        if cmd in ["exit", "quit", "stop"]:
            s.close()
            socket_thread.join()
            http_process.terminate()    
            http_process.join()
            print(f"\x1b[34mGracefully exiting...\x1b[0m")
            exit(0)
        elif cmd == 'listsockets':
            print(connections)
        elif cmd == 'pingsockets':
            # check if the sockets are still alive
            for token, conn in connections.items():
                if conn.fileno() == -1:
                    print(f"\x1b[31msocket {token}: disconnected (fileno={conn.fileno()})\x1b[0m")
                else:
                    print(f"\x1b[32msocket {token}: connected (fileno={conn.fileno()})\x1b[0m")
        elif cmd == "help":
            print("available commands: \n- exit|quit|stop\n- listsockets, \n- pingsockets")
        else:
            print("\x1b[0mUnknown command. Type 'help' for a list of commands.")
