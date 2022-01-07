class clientRequest:
    __NEXT_RID = 1

    def __init__(self, request_type):
        self.request_type = request_type
        self.rid = clientRequest.__NEXT_RID
        clientRequest.__NEXT_RID += 1
