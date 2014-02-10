import models

class AdminController(object):
    def __init__(self, db) :
        self.db = db
        self.db.admin.ensure_index('email', unique=True)
    def get_emails(self) :
        res = self.db.admin.find({}, {'email' : True})
        return [r['email'] for r in res]
    def get_by_email(self, email) :
        try:
            d = self.db.admin.find_one({'email' : email})
            return models.Admin.from_dict(d)
        except TypeError as e:
            return None
        except Exception as e:
            print type(e)
            print e
            raise
    def create(self, d) :
        c = models.Admin.from_dict(d)
        self.db.admin.insert(c.to_dict())
        return c
    def remove(self, d) :
        c = self.get_by_email(d['email'])
        print c
        self.db.admin.remove(c.to_dict())
