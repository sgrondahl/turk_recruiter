from model import Model

class Admin(Model) :
    def __init__(self, email) :
        self.email = email
    @classmethod
    def from_dict(cls, d) :
        return cls(d['email'])
    def to_dict(self) :
        return { 'email' : self.email }
