# 0. Import the socket and datetime module
import glob
import socket
import os
import pickle
from datetime import datetime
from Client_Requests_Classes import register, unregister, update_contact, \
    retrieve_all, retrieve_infot, search_file, publish, remove
from Client_Requests_Classes.download import Download
from Client_Requests_Classes.file import File
from config import BUFFER_SIZE, CHUNK_SIZE, UDP_TIMEOUT
import threading
import sys


# 1. init() - sets the host and port address for the UDP Server upon object creation
class Client:
    def __init__(self, name, host, UDP_port, TCP_port, server_address):
        self.name = name  # Client name
        self.host = host  # Host Address
        self.UDP_port = UDP_port  # Host UDP port client always listening to
        self.TCP_port = TCP_port  # Host TCP Port client always listening to
        self.UDP_sock = None  # Host UDP Socket
        self.TCP_sock = None  # Host TCP Socket
        self.timeout = UDP_TIMEOUT
        self.BUFFER_SIZE = BUFFER_SIZE
        self.SERVER_ADDRESS = server_address
        self.DATA_FOLDER = "./Data"
        self.list_of_available_files = self.get_all_file()
        self.list_of_files_to_remove = self.get_all_file()
        self.Lock = None  # Lock for user input

    # 2. printwt() - messages are printed with a timestamp before them. Timestamp is in this format 'YY-mm-dd
    # HH:MM:SS:' <message>.
    @staticmethod
    def printwt(msg):
        current_date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        print(f'[{current_date_time}] {msg}')

    # 3. configure_client() - Creates a UDP socket that uses IPv4 and binds the client to a specific address for
    # listening.
    def configure_client(self):

        # 3.1. Create the UDP socket with IPv4 Addressing
        self.printwt('Creating UDP client socket...')
        self.UDP_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.printwt(f'Binding UDP client...')
        self.UDP_sock.bind((self.host, self.UDP_port))
        self.UDP_port = self.UDP_sock.getsockname()[1]
        self.printwt(f'Bound UDP client to {self.host}: {self.UDP_port}')
        self.UDP_sock.settimeout(5)

        # 3.2. Create the TCP socket with IPv4 Addressing
        self.printwt('Creating TCP client socket...')
        self.TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.printwt('Binding TCP client socket...')
        self.TCP_sock.bind((self.host, self.TCP_port))
        self.TCP_port = self.TCP_sock.getsockname()[1]
        self.printwt(f'Bound TCP client socket {self.host}: {self.TCP_port}')
        #  set time out for TCP socket and implement it.
        t = threading.Thread(target=self.run_tcp_server, args=())
        t.setDaemon(True)
        t.start()

    def run_tcp_server(self):
        try:
            # 5 is MAX Client
            self.TCP_sock.listen(5)  # TODO add to config
            while True:
                try:
                    conn, address = self.TCP_sock.accept()
                except OSError:
                    return
                tcp_thread = threading.Thread(target=self.handle_tcp_client, args=(conn, address))
                tcp_thread.start()
                tcp_thread.join()
        finally:
            self.TCP_sock.close()

    def handle_tcp_client(self, conn, addr):
        print('New client from', addr)
        try:
            obj = conn.recv(BUFFER_SIZE)
            obj = pickle.loads(obj)

            if isinstance(obj, Download):
                if obj.file_name in self.list_of_available_files:
                    #  Start sending the file
                    chunks = self.get_file_as_chunks(obj.file_name)
                    for i, chunk in enumerate(chunks):
                        if i + 1 >= len(chunks):
                            #  It's a last chunk
                            chunk_obj = pickle.dumps(
                                File(request_type="FILE-END", file_name=obj.file_name, chunk_id=i + 1, text=chunk))
                        else:
                            #  It's not a last chunk
                            chunk_obj = pickle.dumps(
                                File(request_type="FILE", file_name=obj.file_name, chunk_id=i + 1, text=chunk))
                        conn.sendall(chunk_obj)
                else:
                    # File Doesn't exist, Send [DOWNLOAD-ERROR]
                    conn.sendall(pickle.dumps(Download(request_type="DOWNLOAD-ERROR", reason="File Doesn't exist")))
        finally:
            # Close the connection after sending the File
            conn.close()

    # 4. Interactions with the server
    # 4.1. register() - registers the client with the server.
    def register(self):

        # Send the server formatted data that it can expect for registration.
        self.printwt('Attempting to register with the server...')

        # Create a registration object that can be sent to the server using the pickle library.
        client_registration_object = register.Register(self.name, self.host, self.UDP_port, self.TCP_port)
        print(client_registration_object.getHeader())

        # create a local variable that holds the serialized registration object to keep code neat and tidy.
        register_object = pickle.dumps(client_registration_object)

        # send the pickled object to the server using a function we define below. #5 sendToServer().
        self.printwt('Sending registration data to server...')
        self.sendToServer(register_object, 'register')

    # 4.2 unregister() - unregister the client with the server.
    def unregister(self):
        self.printwt('Attempting to unregister with the server...')

        client_unregister_object = unregister.Unregister(self.name)
        print(client_unregister_object.getHeader())

        unregister_object = pickle.dumps(client_unregister_object)

        self.printwt('Sending de-registration data to the server...')
        self.sendToServer(unregister_object, 'unregister')

    # 4.3 publish() - publish the file names that a client has ready to be shared
    def publish(self):
        self.printwt("Select the files which you want to publish[Add File No. Seprated by ',']:")
        count = 1
        for file in self.list_of_available_files:
            self.printwt(str(count) + ". " + file)
            count += 1
        self.printwt("0. Add all files")
        choice = input(">>")
        if choice.isnumeric():
            choice = int(choice)
            if choice != 0:
                self.list_of_available_files = [self.list_of_available_files[choice - 1]]

        else:
            choice = [int(x) for x in choice.split(",")]
            user_choices = []
            for c in choice:
                user_choices.append(self.list_of_available_files[c - 1])
            self.list_of_available_files = user_choices
        self.printwt("These Files will be published: " + str(self.list_of_available_files))
        self.printwt("attempt to add a file to client's list at the server")

        client_publishing_object = publish.publish_req(self.name, self.host, self.UDP_port,
                                                       self.list_of_available_files)
        self.printwt(client_publishing_object.getHeader())

        publishing_object = pickle.dumps(client_publishing_object)
        self.printwt("send publishing request to server")
        self.sendToServer(publishing_object, 'publish')

    #  4.4 remove() - remove the files that a client has already published
    def remove(self):
        self.printwt("Select the files which you want to remove[Add File No. Separated by ',']:")
        count_remove = 1
        for file in self.list_of_files_to_remove:
            self.printwt(str(count_remove) + ". " + file)
            count_remove += 1
        self.printwt("0. remove all files")
        choice_to_remove = input(">>")
        if choice_to_remove.isnumeric():
            choice_to_remove = int(choice_to_remove)
            if choice_to_remove != 0:
                self.list_of_files_to_remove = [self.list_of_files_to_remove[choice_to_remove - 1]]
        else:
            choice_to_remove = [int(x) for x in choice_to_remove.split(",")]
            user_choices = []
            for c in choice_to_remove:
                user_choices.append(self.list_of_files_to_remove[c - 1])
            self.list_of_files_to_remove = user_choices
        self.printwt("These Files will be removed: " + str(self.list_of_files_to_remove))
        self.printwt("attempt to remove a file from client's list at the server")

        client_removing_object = remove.remove_req(self.name, self.host, self.UDP_port,
                                                   self.list_of_files_to_remove)
        self.printwt(client_removing_object.getHeader())

        removing_object = pickle.dumps(client_removing_object)
        self.printwt("send remove request to server")
        self.sendToServer(removing_object, 'remove')

    # 4.5 retrieveAll() - retrieve all the information from the server
    def retrieveAll(self):
        self.printwt('Attempting retrieving all information from the server...')

        client_retrieve_all_object = retrieve_all.RetrieveAll(self.name, self.host, self.UDP_port)
        print(client_retrieve_all_object.getHeader())

        retrieve_object = pickle.dumps(client_retrieve_all_object)

        self.printwt('Sending retrieving all request to server...')
        self.sendToServer(retrieve_object, 'retrieve-all')

    #  4.6 retrieveInfoT() - retrieve info about a specific peer
    def retrieveInfot(self, peer_name):
        self.printwt('retrieving all files for specific client...')
        client_retrieve_infot = \
            retrieve_infot.RetrieveInfot(self.name, self.host, self.UDP_port, peer_name)
        print(client_retrieve_infot.getHeader())

        retrieve_infot_object = pickle.dumps(client_retrieve_infot)
        self.printwt('Sending retrieving specific peer files request to server...')
        self.sendToServer(retrieve_infot_object, 'retrieve-infot')

    def searchFile(self, filename):
        self.printwt('searching specific file ...')
        client_search_file = search_file.SearchFile(self.name, self.host, self.TCP_port, filename)
        print(client_search_file.getHeader())

        search_file_object = pickle.dumps(client_search_file)
        self.printwt('Sending search specific file request to server...')
        return self.sendToServer(search_file_object, 'search-file')

    @staticmethod
    def get_file(fileName, search_path):
        result = []
        # Walking top-down from the root
        for root, DIR, files in os.walk(search_path):
            if fileName in files:
                result.append(os.path.join(root, fileName))
            else:
                print("File Not Found")
        return result

    def get_all_file(self):
        """Get all files and make a list to process each files."""
        files = []
        os.chdir(self.DATA_FOLDER)
        for file in glob.glob("*"):
            files.append(file)
        os.chdir("..")
        return files

    # 4.8 download() -
    def get_file_as_chunks(self, requested_file_name):
        # open file and count the number of characters
        self.printwt("Creating Chunks for: " + str(requested_file_name))
        file_to_process = self.DATA_FOLDER + "/" + requested_file_name
        with open(file_to_process, "r") as a_file:
            data = a_file.read()
            number_of_characters = len(data)
            self.printwt('Number of characters in ' + str(requested_file_name) + ':' + str(number_of_characters))

            if int(number_of_characters) < 1:
                self.printwt("file is empty")
            elif int(number_of_characters) > 1:
                if int(number_of_characters) <= CHUNK_SIZE:
                    self.printwt("file will be sent in 1 segment")
                    return [data]
                else:
                    # chuck the file into segments each 200 char
                    self.printwt("file will be fragmented")
                    data = []
                    with open(file_to_process) as f:
                        while True:
                            d = f.read(CHUNK_SIZE)
                            if not d:
                                break
                            else:
                                data.append(d)

                    print(data)
                    return data

    def get_file_from_peer(self, host, port, file_name):
        port = int(port)
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            conn.connect((host, port))
            download_request = Download(request_type="DOWNLOAD", file_name=file_name)
            self.printwt(download_request.getHeader())
            download_request = pickle.dumps(download_request)
            # Send Download Request
            conn.sendall(download_request)
            # Get Response
            obj = conn.recv(BUFFER_SIZE)
            obj = pickle.loads(obj)

            if isinstance(obj, Download):
                # DOWNLOAD-ERROR
                self.printwt(obj.getHeader())
            elif isinstance(obj, File):
                data = []
                self.printwt(obj.getHeader())
                data.append(obj.text)
                while True:
                    # Get Response
                    obj = conn.recv(BUFFER_SIZE)

                    if obj == b'':
                        break

                    obj = pickle.loads(obj)
                    # Check the chunk type
                    if isinstance(obj, File) and obj.request_type == "FILE":
                        self.printwt(obj.getHeader())
                        data.append(obj.text)
                        continue
                    elif isinstance(obj, File) and obj.request_type == "FILE-END":
                        self.printwt(obj.getHeader())
                        data.append(obj.text)
                        break

                self.printwt(file_name + " is successfully retrieved")
                with open(self.DATA_FOLDER + "/new_" + file_name, "w") as f:
                    f.write(''.join(data))
                self.printwt(file_name + " is successfully created in Data Folder")

        finally:
            conn.close()
            self.printwt("Closing the connection with " + str(host) + ":" + str(port))

    # 4.9 updateContact()  - client can update their client information
    def updateContact(self, ip_address, udp_port, tcp_port):
        # must update this clients sockets also
        self.host = ip_address
        self.UDP_port = udp_port
        self.TCP_port = tcp_port

        # close the old sockets and create and bind the new ones and update the binding
        self.printwt('Closing old sockets and rebinding the new ones...')
        self.UDP_sock.close()
        self.TCP_sock.close()

        self.UDP_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP_sock.bind((self.host, self.UDP_port))
        self.UDP_port = self.UDP_sock.getsockname()[1]
        self.printwt(f'Bound UDP client to {self.host}: {self.UDP_port}')

        self.TCP_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_sock.bind((self.host, self.TCP_port))
        self.TCP_port = self.TCP_sock.getsockname()[1]
        self.printwt(f'Bound TCP client socket {self.host}: {self.TCP_port}')
        t = threading.Thread(target=self.run_tcp_server, args=())
        t.setDaemon(True)
        t.start()
        self.printwt('Attempting to update contact with the server...')

        # Create the updateContact object
        client_update_contact_object = update_contact.UpdateContact(self.name, self.host, self.UDP_port, self.TCP_port)
        print(client_update_contact_object.getHeader())

        update_object = pickle.dumps(client_update_contact_object)

        # send the object to the server
        self.printwt('Sending update contact data to server...')
        self.sendToServer(update_object, 'update-contact')

    # 5. sendtoServer() - sends command to server and handles the reply as well, also helps with retransmission
    def sendToServer(self, command_object, requestType):
        flag = True
        trials = 5
        while flag:
            # try to send the command and receive a reply from the server
            try:
                self.printwt(f'Server Address: {self.SERVER_ADDRESS}')
                self.UDP_sock.sendto(command_object, self.SERVER_ADDRESS)
                self.printwt('Sent ' + requestType + ' request to server')

                # once we sent the request, remove from the amount of trials if reply not received.
                trials -= 1
                if trials == 0:
                    # if we exceeded the amount of trials we exit
                    flag = False
                    self.printwt('Attempted to send ' + requestType + ' request to server and failed 5 times')
                    break
            except socket.error:
                # if sending failed
                self.printwt('Failed to send ' + requestType + ' request to server')

            # try to receive a reply from the server.
            try:
                msg_from_server, server_address = self.UDP_sock.recvfrom(self.BUFFER_SIZE)
                self.printwt(f'Received {requestType} reply from server : {server_address}')
                print('\n' + msg_from_server.decode() + '\n')

                # Coded for 'search-file' ----------------------------
                if "SEARCH-" in msg_from_server.decode('utf-8'):
                    msg = str(msg_from_server.decode('utf-8'))
                    msg = msg.replace("[", "")
                    msg = msg.replace("]", "")
                    msg = [x.strip() for x in msg.split('|')]
                    if msg[0] == "SEARCH-FILE" or msg[0] == "SEARCH-ERROR":
                        return msg
                # ---------------------------------------------------------
                # if we received a reply, set the flag to false, so we don't try again
                flag = False
            except socket.timeout:
                self.printwt(
                    'Failed to receive ' + requestType + ' reply from server attempting ' + str(trials) + ' more times')
                if ConnectionResetError:
                    self.printwt('Connection Reset Error: Server might be down or IPV4 address provided is wrong')
                    self.close_sockets()
                    sys.exit()

    def close_sockets(self):
        self.printwt('Closing sockets...')
        self.UDP_sock.close()
        self.TCP_sock.close()
        self.printwt('Sockets closed')

    @staticmethod
    def handle_commands(client, query):
        client.try_acquireLock()
        if query == '?' or query == 'help':
            print(
                '<register> <unregister> <publish> <remove> <retrieveAll> <retrieveInfot> <searchFile> <updateContact> <download>')
        elif query == 'register':
            client.register()
        elif query == 'unregister':
            client.unregister()
        elif query == 'publish':
            client.publish()
        elif query == 'remove':
            client.remove()
        elif query == 'retrieveAll':
            client.retrieveAll()
        elif query == 'retrieveInfot':
            peer_name = input('> Enter specific client name: ')
            client.retrieveInfot(peer_name)
        elif query == 'searchFile':
            filename = input('> Enter file name to search: ')
            client.searchFile(filename)
        elif query == 'updateContact':
            newIp = input('> Enter new ip address: ')
            newUDPPort = int(input('> Enter new UDP port: '))
            newTCPPort = int(input('> Enter new TCP port: '))
            client.updateContact(newIp, newUDPPort, newTCPPort)
        elif query == 'download':
            filename = input('> Enter file name to search: ')
            response = client.searchFile(filename)
            if response[0] == "SEARCH-FILE":
                client.get_file_from_peer(host=response[3], port=response[4], file_name=filename)
            elif response[0] == "SEARCH-ERROR":
                pass
                #  Add Reason from response
        else:
            print(query)
        client.releaseLock()

    def try_acquireLock(self):
        # if lock is free take it and leave
        if self.Lock != 1:
            self.Lock = 1
            return
        while self.Lock == 1:
            if self.Lock != 1:
                self.Lock = 1
                return

    def releaseLock(self):
        self.Lock = 0


def main():
    query = input('> Enter Server IPv4 Address: ')
    serverAddress = (query, 3001)
    query = input('> Enter Client Name: ')
    client = Client(query, socket.gethostbyname(socket.gethostname()), 0, 0, serverAddress)
    client.configure_client()

    try:
        print('type [help] or [?] for a list of commands at any time.')
        print('type [exit] to exit, or terminate the client')
        while query != 'exit':

            client.try_acquireLock()
            query = input('Query: ')
            client.releaseLock()

            if query == 'exit':
                client.close_sockets()
                break

            client_thread = threading.Thread(target=client.handle_commands, args=(client, query))
            client_thread.daemon = True
            client_thread.start()

    except KeyboardInterrupt:
        client.close_sockets()


if __name__ == '__main__':
    main()
