
class Person:
    def __init__(self):
        
        # Google Contact entry object
        self.entry = None
        
        self.first_name = None
        self.last_name = None
        self.nickname = None
        self.email = None
        self.phone = None
        self.groups = []
    
    def __str__(self):
        s = [
            "%s %s:" % (self.first_name, self.last_name),
            "  Nickname: %s" % self.nickname,
            "  Email: %s" % self.email,
            "  Phone: %s" % self.phone
        ]
        return("\n".join(s))
        
        
class Group:
    def __init__(self, name):
        # Google Contact Group entry object
        self.entry = None
        
        self.name = name
        