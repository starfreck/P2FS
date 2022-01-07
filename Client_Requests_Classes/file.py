from Client_Requests_Classes import request


class File(request.clientRequest):
    def __init__(self, request_type, file_name, chunk_id, text ) -> object:
        super().__init__(request_type)
        self.file_name = file_name
        self.chunk_id = chunk_id
        self.text = text

    def getHeader(self):
        header_string = '\n['+self.request_type + ' | ' + str(self.rid) + ' | ' + self.file_name + ' | ' + str(self.chunk_id) + ' | ' + str(self.text) + ']\n'
        return header_string


