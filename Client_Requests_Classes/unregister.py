from Client_Requests_Classes import request


class Unregister(request.clientRequest):
    def __init__(self, name)-> object:
        super().__init__('unregister')
        self.name = name

    def getHeader(self):
        header_string = '\n[' + self.request_type + ' | ' + str(self.rid) + ' | ' + str(self.name) + ']\n'
        return header_string
