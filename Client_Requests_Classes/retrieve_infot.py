from Client_Requests_Classes import request


class RetrieveInfot(request.clientRequest):
    def __init__(self, name, host, udp_socket, peer_name) -> object:
        super().__init__('retrieve-infot')
        self.name = name
        self.host = host
        self.udp_socket = udp_socket
        self.peer_name = peer_name



    def getHeader(self):
        header_string = '\n[' + self.request_type + ' | ' + str(self.rid) + ' | ' + str(self.peer_name) + ']\n'
        return header_string
