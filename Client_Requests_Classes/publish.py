from Client_Requests_Classes import request


class publish_req(request.clientRequest):
    def __init__(self, name, host, udp_socket, list_of_available_files=[]):
        super().__init__('publish_req')
        self.name = name
        self.host = host
        self.udp_socket = udp_socket
        self.list_of_available_files = list_of_available_files
        # self.file_name = file_name

    def getHeader(self):
        header_string = '\n[' + self.request_type + ' | ' + str(self.rid) + ' | ' + self.name + ' | ' + str(
            self.list_of_available_files) + ']\n'
        return header_string

