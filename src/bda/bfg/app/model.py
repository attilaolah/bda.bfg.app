from zope.interface import implements
from zodict.node import LifecycleNode, AttributedNode
from repoze.bfg.threadlocal import get_current_request
from repoze.bfg.security import Everyone
from repoze.bfg.security import Allow
from repoze.bfg.security import Deny
from repoze.bfg.security import ALL_PERMISSIONS
from repoze.bfg.security import authenticated_userid
from bda.bfg.app.interfaces import (
    IApplicationNode,
    IFactoryNode,
    IAdapterNode,
    IProperties,
    IMetadata,
    INodeInfo,
)

_node_info_registry = dict()

def registerNodeInfo(name, info):
    _node_info_registry[name] = info

def getNodeInfo(name):
    if name in _node_info_registry:
        return _node_info_registry[name]

class BaseNode(AttributedNode):
#class BaseNode(LifecycleNode):
    implements(IApplicationNode)
    
    __acl__ = [
        (Allow, 'group:authenticated', 'view'),
        (Allow, Everyone, 'login'),
        (Deny, Everyone, ALL_PERMISSIONS),
    ]
    
    # set this to name of registered node info on deriving class
    node_info_name = ''
    
    @property
    def properties(self):
        props = Properties()
        props.in_navtree = False
        return props
    
    @property
    def metadata(self):
        name = self.__name__
        if not name:
            name = 'No Title'
        metadata = BaseMetadata()
        metadata.title = name
        return metadata
    
    @property
    def nodeinfo(self):
        info = getNodeInfo(self.node_info_name)
        if not info:
            info = BaseNodeInfo(self.attrs)
            info.title = str(self.__class__)
            info.node = self.__class__
        return info

class FactoryNode(BaseNode):
    implements(IFactoryNode)
    
    factories = {}
    
    def __iter__(self):
        keys = set()
        for key in self.factories.keys():
            keys.add(key)
        for key in AttributedNode.__iter__(self):
        #for key in LifecycleNode.__iter__(self):
            keys.add(key)
        for key in keys:
            yield key
    
    iterkeys = __iter__
    
    def __getitem__(self, key):
        try:
            child = AttributedNode.__getitem__(self, key)
            #child = LifecycleNode.__getitem__(self, key)
        except KeyError, e:
            if not key in self:
                raise KeyError
            child = self.factories[key]()
            self[key] = child
        return child

class AdapterNode(BaseNode):
    implements(IAdapterNode)
    
    def __init__(self, model, name, parent):
        self.model = model
        self.__name__ = name
        self.__parent__ = parent
    
    def __getitem__(self, key):
        return self.model[key]
    
    def __contains__(self, key):
        return key in self.model.keys()
    
    def __len__(self):
        return len(self.model)
    
    def __iter__(self):
        for key in self.model:
            yield key
    
    iterkeys = __iter__
    
    def keys(self):
        return self.model.keys()
    
    def itervalues(self):
        for value in self.model.itervalues():
            yield value
    
    def values(self):
        return list(self.itervalues())
    
    def iteritems(self):
        for item in self.model.iteritems():
            yield item
    
    def items(self):
        return list(self.iteritems())
    
    def get(self, key, default=None):
        return self.model.get(key, default)
    
    @property
    def attrs(self):
        return self.model.attrs

class Properties(object):
    implements(IProperties)
    
    def __init__(self, data=None):
        if data is None:
            data = dict()
        object.__setattr__(self, '_data', data)
    
    def __getitem__(self, key):
        return object.__getattribute__(self, '_data')[key]
    
    def get(self, key, default=None):
        return object.__getattribute__(self, '_data').get(key, default)
    
    def __contains__(self, key):
        return key in object.__getattribute__(self, '_data')
    
    def __getattr__(self, name):
        return object.__getattribute__(self, '_data').get(name)
    
    def __setattr__(self, name, value):
        object.__getattribute__(self, '_data')[name] = value

class BaseMetadata(Properties):
    implements(IMetadata)

class BaseNodeInfo(Properties):
    implements(INodeInfo)