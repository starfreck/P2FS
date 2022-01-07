from Client_Requests_Classes import request


class Download(request.clientRequest):
    def __init__(self,  request_type, file_name=None, reason=None) -> object:
        super().__init__(request_type)
        self.file_name = file_name
        self.reason = reason

    def getHeader(self):
        if self.request_type == "DOWNLOAD":
            header_string = '\n['+self.request_type + ' | ' + str(self.rid) + ' | ' + self.file_name + ']\n'
            return header_string
        else:
            header_string = '\n[' + self.request_type + ' | ' + str(self.rid) + ' | ' + self.reason + ']\n'
            return header_string