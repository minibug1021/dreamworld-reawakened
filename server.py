#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from urllib.parse import urlparse, parse_qs
import time
import json
import random
import os.path

class S(BaseHTTPRequestHandler):
    def do_GET(self):
        print(self.headers["User-Agent"])
        logging.info("GET %s\n", str(self.path))
        path = urlparse(self.path).path
        if(path == "/api/"):
            queryString = urlparse(self.path).query
            query = parse_qs(queryString, strict_parsing=True)
            apiName = query["p"][0]
            print(apiName)
            if(apiName == "pgl.news.information_list"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"list":[], "total_count":0}')
            elif(apiName == "pgl.member.profile.my_state"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")
            elif(apiName == "pdw.home.my_island"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"island_id":201, "arranged_interior_list":[]}')
            elif(apiName == "pdw.croft.my_croft_list"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"croft_list":[:"kinomi_state":0, "my_croft_id": 0, "pokeitem_id": 0, "kinomi": 0, "kinomi_id": 52, "dirt_hp": 0, "x": 1, "y": 1}, :"kinomi_state":0, "my_croft_id": 0, "pokeitem_id": 0, "kinomi": 0, "kinomi_id": 52, "dirt_hp": 0, "x": 2, "y": 1}], "diglett_flag":0}')
            elif(apiName == "pdw.croft.tutorial_start"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')
            elif(apiName == "pdw.croft.tutorial_end"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')
            elif(apiName == "pdw.home.my_bridge"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{}')
            elif(apiName == "pdw.dreamland.top"):
                response = {
                    "dreamland_area_id": random.randint (3, 9),
                    "object_list" : [],
                }
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
            elif(apiName == "pdw.dreamland.tree_top"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"pokemon_list":[], "encount_list":[{}]}')
            elif(apiName == "pgl.top.init"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"")
            return
            
        if(path == "/"):
            if(self.headers["User-Agent"] == "Shockwave Flash"):
                self.send_response(302)
                self.send_header('Location', "http://127.0.0.1:8080/src/swf/theme/assets/common/main.swf")
                self.end_headers()

            # support for flash-enabled browsers
            with open('./Dream_Park.htm', "rb") as f:
                self.send_response(200)
                data = f.read()
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        # strip bugged trailing &s that PDW likes to add sometimes
        if("&") in path:
            splitPath = path.split("&")
            path = splitPath[0]

        if(os.path.isfile('./'+path)):
            with open('./'+path, "rb") as f:
                self.send_response(200)
                data = f.read()
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.wfile.write(b"Error: Not found")

    def do_POST(self):
        logging.info("POST %s\n", str(self.path))
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        query = parse_qs(post_data.decode(), strict_parsing=True)
        print(query)
        apiName = query["p"][0]
        print(apiName)
        if(apiName == 'pdw.home.pdw_timecheck'):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")
        elif(apiName == 'pgl.member.profile.pdw_login'):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"{}")
        elif(apiName == 'pdw.home.pdw_start'):
            response = {
                "started_at": int(time.time()),
            }
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"")
        return
        
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.wfile.write(b"Error: Not found")

def run(server_class=HTTPServer, handler_class=S, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('127.0.0.1', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting server...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping server...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
