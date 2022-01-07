from Client_Requests_Classes import request


class SearchFile(request.clientRequest):
    def __init__(self, name, host, tcp_port, filename) -> object:
        super().__init__('search-file')
        self.name = name
        self.host = host
        self.tcp_port = tcp_port
        self.filename = filename

    def getHeader(self):
        header_string = '\n[' + self.request_type + ' | ' + str(self.rid) + ' | ' + str(self.name) + ' | ' + str(self.host) + ' | ' + str(self.tcp_port) + ' | ' + self.filename + ']\n'
        return header_string
