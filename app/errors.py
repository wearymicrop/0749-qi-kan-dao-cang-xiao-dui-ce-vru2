class LedgerError(ValueError):
    def __init__(self, code, message, status=422):
        super().__init__(message)
        self.code = code
        self.status = status

    def payload(self):
        return {"code": self.code, "message": str(self)}
