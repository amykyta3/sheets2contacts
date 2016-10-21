import logging
logging.getLogger("person")

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
        
        # store group hrefs before resolving them into Group objects
        self._group_hrefs = []
        
        self.log = logging.getLogger("person")
    
    def update(self, P):
        """
        Update self with potential new data form a different Person object
        entries with None are not updated
        
        Returns True if anything got updated
        """
        changed = False
        
        self.log.debug("Updating '%s %s'" % (self.first_name, self.last_name))
        
        if((P.first_name != None) and (P.first_name != self.first_name)):
            self.log.debug("first_name changed: '%s' --> '%s'" % (self.first_name, P.first_name))
            self.first_name = P.first_name
            changed = True
        
        if((P.last_name != None) and (P.last_name != self.last_name)):
            self.log.debug("last_name changed: '%s' --> '%s'" % (self.last_name, P.last_name))
            self.last_name = P.last_name
            changed = True
        
        if((P.nickname != None) and (P.nickname != self.nickname)):
            self.log.debug("nickname changed: '%s' --> '%s'" % (self.nickname, P.nickname))
            self.nickname = P.nickname
            changed = True
        
        if((P.email != None) and (P.email != self.email)):
            self.log.debug("email changed: '%s' --> '%s'" % (self.email, P.email))
            self.email = P.email
            changed = True
        
        if((P.phone != None) and (P.phone != self.phone)):
            self.log.debug("phone changed: '%s' --> '%s'" % (self.phone, P.phone))
            self.phone = P.phone
            changed = True
        
        if(set(P.groups) != set(self.groups)):
            self.log.debug("groups changed: '%s' --> '%s'" % (self.groups, P.groups))
            self.groups = P.groups
            changed = True
        
        return(changed)
        
    def __str__(self):
        s = [
            "%s %s:" % (self.first_name, self.last_name),
            "  Nickname: %s" % self.nickname,
            "  Email: %s" % self.email,
            "  Phone: %s" % self.phone
        ]
        return("\n".join(s))
        
#===============================================================================
class Group:
    def __init__(self, name):
        # Google Contact Group entry object
        self.entry = None
        
        self.name = name
        
    def __repr__(self):
        return("<%s>" % self.name)

#===============================================================================
def get_group_by_name(Groups, group_name):
    """
    Lookup a group by name
    """
    for G in Groups:
        if(G.name == group_name):
            return(G)
    return(None)

#---------------------------------------------------------------------------
def get_group_by_id(Groups, gid):
    """
    Lookup a group by ID
    """
    for G in Groups:
        if(G.entry and G.entry.id.text == gid):
            return(G)
    return(None)