import yaml
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor
import struct


class DataExchangeServer:
    def __init__(self, config):
        self.config = config
        self.client_data = {
            client: {
                "received_values": None,
                "local_values": [],
                "last_timestamp": 0,
                "last_checksum": None
            }
            for client in config['clients']
        }
        self.executor = ThreadPoolExecutor(max_workers=10)

    def update_latest(self, client_id, values, timestamp, checksum):
        if client_id not in self.client_data:
            return False, "Invalid client ID"

        if timestamp <= self.client_data[client_id]["last_timestamp"]:
            return False, "Message is old"

        calculated_checksum = self.calculate_checksum(values, timestamp)
        if calculated_checksum != checksum:
            return False, "Checksum mismatch"

        self.client_data[client_id]["local_values"] = values
        self.client_data[client_id]["last_timestamp"] = timestamp
        self.client_data[client_id]["last_checksum"] = checksum

        other_client_id = next(c for c in self.config['clients'] if c != client_id)
        self.client_data[other_client_id]["received_values"] = values

        return True, "Update successful"

    def get_latest(self, client_id):
        if client_id not in self.client_data:
            return None, "Invalid client ID"

        values = self.client_data[client_id]["received_values"]
        # Reset the received_values to None after retrieval
        self.client_data[client_id]["received_values"] = None
        return values, "Data retrieved and reset"

    @staticmethod
    def calculate_checksum(values, timestamp):
        data = json.dumps(values) + str(timestamp)
        return hashlib.md5(data.encode()).hexdigest()


class RequestHandler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def do_GET(self):
        if not self.path.startswith('/receive'):
            self.send_error(404)
            return

        client_id = self.path.split('/')[-1]
        values, message = server.get_latest(client_id)

        if values is None:
            self.send_response(204)  # No Content
            self.end_headers()
            return

        timestamp = time.time()
        checksum = server.calculate_checksum(values, timestamp)
        response_data = {
            'values': values,
            'timestamp': timestamp,
            'checksum': checksum,
            'message': message
        }
        response_json = json.dumps(response_data)

        # Calculate the message size and prepare the header
        message_size = len(response_json)
        size_header = struct.pack('>I', message_size)  # 4-byte unsigned integer, big-endian

        self.send_response(200)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(4 + message_size))  # 4 bytes for size + actual message size
        self.end_headers()
        self.wfile.write(size_header)
        self.wfile.write(response_json.encode())

    def do_POST(self):
        if not self.path.startswith('/send'):
            self.send_error(404)
            return

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # Extract the message size from the first 4 bytes
        size_header = post_data[:4]
        message_size = struct.unpack('>I', size_header)[0]

        # Extract and parse the JSON data
        json_data = post_data[4:4 + message_size].decode()
        data = json.loads(json_data)

        client_id = self.path.split('/')[-1]
        success, message = server.update_latest(
            client_id,
            data['values'],
            data['timestamp'],
            data['checksum']
        )

        response_data = {'status': message}
        response_json = json.dumps(response_data)
        message_size = len(response_json)
        size_header = struct.pack('>I', message_size)

        self.send_response(200 if success else 400)
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(4 + message_size))
        self.end_headers()
        self.wfile.write(size_header)
        self.wfile.write(response_json.encode())


def load_config(config_file):
    with open(config_file, 'r') as file:
        return yaml.safe_load(file)


def run_server(config):
    server_address = (config['server']['host'], config['server']['port'])
    httpd = ThreadingHTTPServer(server_address, RequestHandler)
    print(f"Server running on {server_address}")
    print("Clients:")
    for client in config['clients']:
        print(f"  - {client}")
    httpd.serve_forever()


if __name__ == "__main__":
    config = load_config('server_config.yaml')
    server = DataExchangeServer(config)
    run_server(config)