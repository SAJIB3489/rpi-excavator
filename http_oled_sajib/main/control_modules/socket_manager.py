import socket
import struct
from datetime import datetime
import threading
import os
from collections import deque
#from time import sleep

# identification numbers, you can add your own to the list
id_numbers = {
    0: "Excavator",
    1: "Mevea",
    2: "Motion Platform",
    3: "Digicenter"
}

# different datatypes available for send
datatype_encoding = {
    'int': 0,
    'double': 1
}


class MasiSocketManager:
    def __init__(self,
                 endian_specifier='<',              # Little-endian
                 unix_format='d',                   # old 'Q' 8-byte integer
                 handshake_format='i',              # 8-byte signed int
                 checksum_format='B',               # 1-byte unsigned int
                 int_format='b',                    # 1-byte signed int
                 double_format='d',                 # 8-byte double (float)
                 dir_path="log/",                   # Path for log file
                 base_filename="data_recording",    # Name of the file. Date will be added at the end
                 file_extension='.bin',             # log file type
                 ):

        self.endian_specifier = endian_specifier
        self.unix_format = unix_format
        self.handshake_format = handshake_format
        self.checksum_format = checksum_format
        self.int_format = int_format
        self.double_format = double_format
        self.checksum_format_size = struct.calcsize(endian_specifier + checksum_format)

        self.socket_type = None  # Client or Server. User selectable
        self.network_protocol = None  # TCP or UDP. User selectable
        self.filepath = None

        self.local_id_number = None
        self.local_num_inputs = None
        self.local_num_outputs = None
        self.local_socket = None
        self.local_addr = None
        self.local_output_datatype = None
        self.local_datatype_size = None

        self.recvd_id_number = None
        self.recvd_num_inputs = None
        self.recvd_num_outputs = None
        self.connected_socket = None
        self.connected_addr = None
        self.connected_output_datatype = None
        self.connected_datatype_size = None

        self.buffer_size = 100
        #self.data_buffer = []
        self.data_buffer = deque()  # Use deque for more efficient pops
        self.pack_datatype = self.double_format  # for now force floating point numbers
        self.len_buffer_data = None
        self.saving_thread = None
        self.saving_running = None

        self.send_bytes = None
        self.recv_bytes = None
        self.data_recv_running = None
        self.data_reception_thread = None
        self.latest_recvd = None


        self.latest_data_lock = threading.Lock()

        self.data_buffer_lock = threading.Lock()
        self.buffer_not_empty = threading.Condition(self.data_buffer_lock)

        current_date = datetime.now().strftime("%Y-%m-%d")
        self.filepath = os.path.join(dir_path, f"{base_filename}_{current_date}{file_extension}")

        # init done

    def setup_socket(self, addr, port, identification_number, inputs, outputs, socket_type):
        """Set up the socket as a client or server"""
        self.local_id_number = identification_number
        self.local_num_inputs = inputs
        self.local_num_outputs = outputs

        if socket_type == 'client':
            self.__setup_socket_client(addr, port)

        elif socket_type == 'server':
            self.__setup_socket_server(addr, port)
        else:
            print(f"Check socket type! {socket_type} given!")
            return False
        return True

    def handshake(self, local_datatype='double', num_extra_args=3, **kwargs):
        local_datatype_code = datatype_encoding.get(local_datatype, 1)  # Default to 'double'

        """
                Handshake is done so that it will work with Mevea.
                When the connection is accepted, Mevea will send 3x32bit (8-byte) integers
                containing [identification number], [number of outputs], [number of inputs].

                User needs to respond to this with [identification number], [number of inputs], [number of outputs]
                These values need to match!
                Please note that the response does not directly match the received data! (in / out flipped)

                If not communicating with Mevea, handshake will always send one extra argument that is used to inform the datatype.
                You are also able to send [num_extra_args] amount of extra arguments during handshake.
                These can be used to e.g. inform various things.
                As of 17.4.2024 the example extra arguments are:
                - Loop frequency in Hz
                - value for scaling float values to integers

                'local_output_datatype' and 'connected_output_datatype' are used to set the format for sending/receiving.
                As of 17.4.2024, Parameter can be 'int' (Signed 1-byte integer) or 'double' (8-byte floating point number).

                !Python’s float is a double-precision 64-bit (4*16byte) binary format IEEE 754 value (double in C/C++ terms)!
        """

        if local_datatype_code == 0:
            self.local_output_datatype = self.int_format
        else:
            self.local_output_datatype = self.double_format # force doubles if dt code mismatch

        recvd_extra_args = None

        # handle handshake as server
        if self.socket_type == 'server':
            # receive, then send
            packed_handshake = self.connected_socket.recv(12)
            self.recvd_id_number, self.recvd_num_outputs, self.recvd_num_inputs = struct.unpack(
                self.endian_specifier + self.handshake_format * 3, packed_handshake)
            connected_device_name = id_numbers.get(self.recvd_id_number, "Undefined")

            # check if in/out match
            inputs_match = self.recvd_num_inputs == self.local_num_outputs
            outputs_match = self.recvd_num_outputs == self.local_num_inputs

            if not (inputs_match and outputs_match):
                print(f"Error: Mismatch in expected inputs/outputs with {connected_device_name}.")
                return False

            # skip extra args if connected to Mevea
            if connected_device_name == "Mevea":
                self.local_output_datatype = self.double_format
                self.connected_output_datatype = self.double_format
                response_format = self.endian_specifier + self.handshake_format * 3
                response_values = [self.local_id_number, self.local_num_inputs, self.local_num_outputs]
            else:
                packed_datatype = self.connected_socket.recv(struct.calcsize(self.handshake_format))
                connected_datatype_code, = struct.unpack(self.handshake_format, packed_datatype)

                if connected_datatype_code == 0:
                    self.connected_output_datatype = self.int_format
                else:
                    self.connected_output_datatype = self.double_format

                recvd_extra_args = self.__receive_extra_args(num_extra_args)
                extra_args_to_send = self._prepare_extra_args(kwargs, num_extra_args)

                response_format = self.endian_specifier + self.handshake_format * (
                            3 + num_extra_args) + self.handshake_format
                response_values = [self.local_id_number, self.local_num_inputs, self.local_num_outputs,
                                   local_datatype_code] + extra_args_to_send

            response = struct.pack(response_format, *response_values)
            self.connected_socket.send(response)

        # handle connection as client
        elif self.socket_type == 'client':
            # send, then receive
            extra_args_to_send = self._prepare_extra_args(kwargs, num_extra_args)
            response_format = self.endian_specifier + self.handshake_format * (
                        3 + num_extra_args) + self.handshake_format
            response = struct.pack(response_format, self.local_id_number, self.local_num_outputs, self.local_num_inputs,
                                   local_datatype_code, *extra_args_to_send)

            self.local_socket.send(response)
            packed_handshake = self.connected_socket.recv(12)

            self.recvd_id_number, self.recvd_num_inputs, self.recvd_num_outputs = struct.unpack(
                self.endian_specifier + self.handshake_format * 3, packed_handshake)
            connected_device_name = id_numbers.get(self.recvd_id_number, "Undefined")

            # skip extra args if connected to Mevea
            if connected_device_name == "Mevea":
                self.local_output_datatype = self.double_format
                self.connected_output_datatype = self.double_format
            else:
                packed_datatype = self.connected_socket.recv(struct.calcsize(self.handshake_format))
                connected_datatype_code, = struct.unpack(self.handshake_format, packed_datatype)

                if connected_datatype_code == 0:
                    self.connected_output_datatype = self.int_format
                else:
                    self.connected_output_datatype = self.double_format

                recvd_extra_args = self.__receive_extra_args(num_extra_args)

        else:
            print(f"Wrong socket type! What the hell is {self.socket_type}")
            return None

        # calculate dt sizer for further use
        self.local_datatype_size = struct.calcsize(self.endian_specifier + self.local_output_datatype)
        self.connected_datatype_size = struct.calcsize(self.endian_specifier + self.connected_output_datatype)

        # calculate wanted byte sizes when sending and receiving
        self.send_bytes = struct.calcsize(
            (self.endian_specifier + self.local_output_datatype)) * self.local_num_outputs + self.checksum_format_size
        self.recv_bytes = struct.calcsize((
                                                      self.endian_specifier + self.connected_output_datatype)) * self.recvd_num_outputs + self.checksum_format_size

        # debug feature, inform the user about the made connection
        self.__identify(connected_device_name, recvd_extra_args)
        print("Handshake completed successfully.\n------------------------------------------")
        return self.connected_output_datatype, recvd_extra_args

    def tcp_to_udp(self, socket_buffer_size=64):
        print("Reconfiguring to UDP...")
        # Store the TCP address information before closing the socket
        tcp_addr = self.connected_addr if self.socket_type == 'client' else self.local_addr

        # Close existing TCP connection if it's a connected socket distinct from the listening socket
        if hasattr(self, 'connected_socket') and self.connected_socket:
            self.connected_socket.close()
            print("Closed existing TCP connected socket.")

        # Close the listening socket if it exists
        if self.local_socket:
            self.local_socket.close()
            print("Closed existing TCP listening socket.")

        # Create a new socket for UDP
        self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.local_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, socket_buffer_size)

        # Set up as a UDP server or client
        if self.socket_type == 'server':
            self.local_socket.bind(tcp_addr)
            print(f"Socket reconfigured as a UDP-server! Listening on {tcp_addr}...")
        elif self.socket_type == 'client':
            self.connected_addr = tcp_addr  # Keep the server's address for the client
            print(f"Socket reconfigured as a UDP-client! Server address set to {tcp_addr}")

        self.network_protocol = 'udp'
        return True

    def start_data_recv_thread(self):
        if self.data_reception_thread is None or not self.data_reception_thread.is_alive():
            self.data_recv_running = True
            self.data_reception_thread = threading.Thread(target=self.__continuous_data_receiver, daemon=True)
            self.data_reception_thread.start()
            print("Started data receiving thread!")
        else:
            print("Data reception is already running.")

    def stop_data_recv_thread(self):
        self.data_recv_running = False
        if self.data_reception_thread is not None:
            self.data_reception_thread.join()
            self.data_reception_thread = None
            return True

    def start_saving_thread(self):
        if self.saving_thread is None or not self.saving_thread.is_alive():
            self.saving_running = True
            self.saving_thread = threading.Thread(target=self._run_saving_thread, daemon=True)
            self.saving_thread.start()
            print("Started data saving thread!")
        else:
            print("Data saving is already running.")

    def stop_saving_thread(self):
        self.saving_running = False
        with self.buffer_not_empty:
            self.buffer_not_empty.notify()  # Wake up the thread if it's waiting
        if self.saving_thread is not None:
            self.saving_thread.join()
            self.saving_thread = None
            return True

    def stop_all(self):
        self.close_socket()
        if self.stop_data_recv_thread() and self.stop_saving_thread():
            print("Threads stopped succesfully!")

    def send_data(self, data):
        # This method uses self.local_output_datatype for packing data.

        # pack data (without checksum). Use local_output_datatype
        packed_data = struct.pack(self.endian_specifier + self.local_output_datatype * len(data), *data)  # local datatype here??

        if packed_data is not None:
            final_data = self._add_checksum(packed_data)

            if self.network_protocol == 'tcp':
                self.connected_socket.send(final_data)
            else:  # UDP
                self.local_socket.sendto(final_data, self.connected_addr)

            return final_data
        return None

    def get_latest_received(self):
        # This method uses self.connected_output_datatype for unpacking received data.
        with self.latest_data_lock:
            if self.latest_recvd is None:
                return None  # Silently handle the no-data-yet case

            try:
                full_data = self.latest_recvd
                #print(f"(get_latest_recived) raw data: {full_data}")
                received_checksum, = struct.unpack((self.endian_specifier + self.checksum_format),
                                                   full_data[-self.checksum_format_size:])
                computed_checksum = self._compute_checksum(full_data[:-self.checksum_format_size])

                if received_checksum != computed_checksum:
                    print("Checksum mismatch!")
                    return None

                # Ensure data length aligns with expected chunks
                expected_length = len(full_data) - self.checksum_format_size
                if expected_length % self.connected_datatype_size != 0:
                    print(f"Data length {expected_length} is not a multiple of {self.connected_datatype_size}")
                    return None

                decoded_values = [struct.unpack(self.endian_specifier + self.connected_output_datatype,
                                                full_data[i:i + self.connected_datatype_size])[0]
                                  for i in range(0, expected_length, self.connected_datatype_size)]


                self.latest_recvd = None  # Reset after processing
                return decoded_values
            except Exception as e:
                print(f"Error processing the latest received data: {e}")
                return None

    def add_data_to_buffer(self, unpacked_data):
        """Appends raw data along with a timestamp to the buffer."""
        current_timestamp = datetime.now().timestamp()
        microsecond_timestamp = int(current_timestamp * 1e6)
        timestamped_data = (microsecond_timestamp, unpacked_data)

        with self.data_buffer_lock:
            self.data_buffer.append(timestamped_data)
            ready_to_save = len(self.data_buffer) >= self.buffer_size

        if ready_to_save:
            with self.buffer_not_empty:
                self.buffer_not_empty.notify()  # Notify outside of data_buffer_lock

    def clear_file(self):
        # check if the 'wb' matters
        with open(self.filepath, 'wb'):
            pass
        print("Cleared file!")

    def print_bin_file(self, num_values):
        """Prints the binary file in a human-readable format."""

        # TODO: convert the whole dataset to human readable format!

        # Prepare the format string for unpacking
        format_str = self.endian_specifier + (self.pack_datatype * (num_values + 1)) # +1 for timestamp
        data_size = struct.calcsize(format_str)

        if not os.path.exists(self.filepath):
            print(f"Error: File '{self.filepath}' does not exist.")
            return

        with open(self.filepath, 'rb') as f:
            while True:
                packed_data = f.read(data_size)
                if not packed_data:
                    break

                # Unpack the data
                data = struct.unpack(format_str, packed_data)
                print(data)

    def close_socket(self):
        if self.local_socket:
            self.local_socket.close()
            print("Socket closed successfully!")
        else:
            print("something wrong has happened somewhere")

    @staticmethod
    def _compute_checksum(packed_data):
        checksum = 0
        for byte in packed_data:
            checksum ^= byte
        return checksum

    @staticmethod
    def _prepare_extra_args(kwargs, num_extra_args):

        # Additional arguments for non-Mevea connections
        #for key, value in kwargs.items():
         #   print(f"Additional argument added: {key} with value: {value}")

        # Prepare extra arguments for sending
        extra_args_to_send = list(kwargs.values())[:num_extra_args]
        extra_args_to_send.extend([0] * (num_extra_args - len(extra_args_to_send)))  # Fill no data with 0
        return extra_args_to_send

    def _run_saving_thread(self):
        while self.saving_running:
            with self.buffer_not_empty:
                while len(self.data_buffer) < self.buffer_size and self.saving_running:
                    self.buffer_not_empty.wait()
                if not self.saving_running:
                    break

            # Moved outside the with block to avoid holding buffer_not_empty during save
            self.__save_buffer()  # Assumes this function manages data_buffer_lock internally

    def _add_checksum(self, packed_data):
        # Compute checksum
        checksum = self._compute_checksum(packed_data)
        # add the checksum as the last value in the list
        packed_values = packed_data + struct.pack((self.endian_specifier + self.checksum_format), checksum)
        return packed_values

    def __save_buffer(self):
        packed_data_list = []
        while self.data_buffer:
            data = self.data_buffer.popleft()
            try:
                timestamp = int(data[0])
                # Ensure all elements in the list are floats
                sensor_values = [float(d) for d in data[1]]  # data[1] because all sensor values are in a list at index 1
            except ValueError as e:
                print("Type conversion error:", e)
                continue

            format_string = self.endian_specifier + self.unix_format + (self.pack_datatype * len(sensor_values))
            try:
                packed_data = struct.pack(format_string, timestamp, *sensor_values)
                packed_data_list.append(packed_data)
            except struct.error as e:
                print("Struct packing error:", e)
                continue

        with open(self.filepath, 'ab') as f:  # 'ab' denotes appending in binary mode
            f.writelines(packed_data_list)

        print("Saved data to file...")

    def __setup_socket_client(self, addr, port):
        if not self.local_socket:
            self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Set up as client. TCP
            self.local_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print("Socket configured as a TCP-client!")
            self.local_socket.connect((addr, port))

            # Remember for later use
            self.socket_type = 'client'
            self.connected_addr = (addr, port)
            self.connected_socket = self.local_socket
            self.network_protocol = 'tcp'

        else:
            # socket already made, do something?
            print("socket already made!")

    def __setup_socket_server(self, addr, port):
        if not self.local_socket:
            self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Set up as server. TCP
            self.local_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.local_socket.bind((addr, port))
            print(f"Socket configured as a TCP-server! Listening on {addr}:{port}")
            self.local_socket.listen(1)
            self.connected_socket, self.connected_addr = self.local_socket.accept()

            self.socket_type = 'server'
            self.local_addr = (addr, port)
            self.network_protocol = 'tcp'

        else:
            # socket already made, do something?
            print("socket already made!")

    def __continuous_data_receiver(self):
        # now polling, would events be better?
        while self.data_recv_running:
            try:
                data = self.__receive_data()
                if data:
                    with self.latest_data_lock:
                        self.latest_recvd = data
            except Exception as e:
                print(f"Error receiving data (continuous_data_receiver): {e}")

    def __receive_data(self):
        try:
            if self.network_protocol == 'tcp':
                full_data = self.connected_socket.recv(self.recv_bytes)
            else:  # UDP
                full_data, addr = self.local_socket.recvfrom(self.recv_bytes)
                if self.socket_type == 'server':
                    self.connected_addr = addr  # Update only for server

            if not full_data or len(full_data) != self.recv_bytes:
                print("No new data or incomplete data received.")
                return None

            return full_data
        except Exception as e:
            print(f"Error receiving data: {e}")
            return None

    def __receive_extra_args(self, num_args):
        # Receive extra arguments from the TCP connection
        recvd_extra_args = []
        for _ in range(num_args):
            packed_arg = self.connected_socket.recv(struct.calcsize(self.handshake_format))
            arg, = struct.unpack(self.endian_specifier + self.handshake_format, packed_arg)
            recvd_extra_args.append(arg)
        return recvd_extra_args

    def __identify(self, device_name, recvd_extra_args):
        # Let the user know who is who and what is what and whatnot
        if device_name == "Undefined":
            print(
                f"Undefined handshake received from {self.connected_addr} with {self.recvd_num_inputs} inputs and {self.recvd_num_outputs} outputs.")
        elif device_name == "Mevea":
            print(
                f"Handshake confirmed with Mevea device at {self.connected_addr} with {self.recvd_num_inputs} inputs and {self.recvd_num_outputs} outputs.")
        else:
            print(
                f"Handshake received from {device_name} ({self.connected_addr}) with {self.recvd_num_inputs} inputs and {self.recvd_num_outputs} outputs.")

        print(f"Received extra arguments: {recvd_extra_args}")

        print(f"Sent data will be: {self.send_bytes} bytes with ({self.local_output_datatype}) datatype!")
        print(f"Received data should be: {self.recv_bytes} bytes with ({self.connected_output_datatype}) datatype!")