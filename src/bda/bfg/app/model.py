import os
import types
import ConfigParser
from lxml import etree
from datetime import datetime
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
        props.editable = False
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
        BaseNode.__init__(self, name)
        self.model = model
        self.__name__ = name
        self.__parent__ = parent
    
    def __iter__(self):
        for key in self.model:
            yield key
    
    iterkeys = __iter__
    
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

class XMLProperties(Properties):
    
    def __init__(self, path, data=None):
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_data', dict())
        if data:
            object.__getattribute__(self, '_data').update(data)
        self._init()
    
    def __call__(self):
        file = open(object.__getattribute__(self, '_path'), 'w')
        file.write(self._xml_repr())
        file.close()
    
    def __delitem__(self, name):
        data = object.__getattribute__(self, '_data')
        if name in data:
            del data[name]
        else:
            raise KeyError(u"property %s does not exist" % name)
    
    def _init(self):
        path = object.__getattribute__(self, '_path')
        if not path or not os.path.exists(path):
            return
        file = open(path, 'r')
        tree = etree.parse(file)
        file.close()
        root = tree.getroot()
        data = object.__getattribute__(self, '_data')
        for elem in root.getchildren():
            children = elem.getchildren()
            if children:
                val = list()
                for subelem in children:
                    val.append(self._r_value(subelem.text.strip()))
                data[elem.tag] = val
            else:
                data[elem.tag] = self._r_value(elem.text.strip())
        file.close()
    
    def _xml_repr(self):
        root = etree.Element('properties')
        data = object.__getattribute__(self, '_data')
        for key, value in data.items():
            sub = etree.SubElement(root, key)
            if type(value) in [types.ListType, types.TupleType]:
                for item in value:
                    subsub = etree.SubElement(sub, 'item')
                    subsub.text = self._w_value(item)
            else:
                sub.text = self._w_value(value)
        return etree.tostring(root, pretty_print=True)
    
    def _w_value(self, val):
        if isinstance(val, datetime):
            return self._dt_to_iso(val)
        return unicode(val)
    
    def _r_value(self, val):
        try:
            return self._dt_from_iso(val)
        except ValueError:
            return unicode(val)
    
    def _dt_from_iso(self, str):
        return datetime.strptime(str, '%Y-%m-%dT%H:%M:%S')
    
    def _dt_to_iso(self, dt):
        iso = dt.isoformat()
        if iso.find('.') != -1:
            iso = iso[:iso.rfind('.')]
        return iso
    
    # testing
    def _keys(self):
        return object.__getattribute__(self, '_data').keys()
    
    def _values(self):
        return object.__getattribute__(self, '_data').values()

class ConfigProperties(Properties):
    
    def __init__(self, path, data=None):
        object.__setattr__(self, '_path', path)
        object.__setattr__(self, '_data', dict())
        if data:
            object.__getattribute__(self, '_data').update(data)
        self._init()
    
    def __call__(self):
        path = object.__getattribute__(self, '_path')
        config = self.config()
        with open(path, 'wb') as configfile:
            config.write(configfile)
    
    def __getitem__(self, key):
        try:
            return self.config().get('properties', key)
        except ConfigParser.NoOptionError:
            raise KeyError(key)
    
    def get(self, key, default=None):
        try:
            return self.config().get('properties', key)
        except ConfigParser.NoOptionError:
            return default
    
    def __contains__(self, key):
        try:
            value = self.config().get('properties', key)
            return True
        except ConfigParser.NoOptionError:
            return False
    
    def __getattr__(self, name):
        try:
            return self.config().get('properties', name)
        except ConfigParser.NoOptionError:
            return
    
    def __setattr__(self, name, value):
        self.config().set('properties', name, value)
    
    def __delitem__(self, name):
        config = self.config()
        try:
            value = config.get('properties', name)
        except ConfigParser.NoOptionError:
            raise KeyError(u"property %s does not exist" % name)
        config.remove_option('properties', name)
    
    def config(self):
        try:
            return object.__getattribute__(self, '_config')
        except AttributeError:
            pass
        config = ConfigParser.ConfigParser()
        path = object.__getattribute__(self, '_path')
        if os.path.exists(path):
            config.read(path)
        else:
            config.add_section('properties')
        object.__setattr__(self, '_config', config)
        return object.__getattribute__(self, '_config')
    
    def _init(self):
        data = object.__getattribute__(self, '_data')
        config = self.config()
        for key, value in data.items():
            config.set('properties', key, value)