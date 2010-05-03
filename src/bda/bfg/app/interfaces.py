from zope.interface import Attribute
from zope.interface.common.mapping import IReadMapping
from zodict.interfaces import IAttributedNode

class IApplicationNode(IAttributedNode):
    """Application Node interface.
    """
    
    __acl__ = Attribute(u"ACL")

    properties = Attribute(u"Properties for this application Node")
    
    metadata = Attribute(u"IMetadata implementation")
    
    title = Attribute(u"Node Title")

class IFactoryNode(IApplicationNode):
    """Application node for static children.
    """
    
    factories = Attribute(u"Dict containing available keys and the Node class "
                          u"used to create this child.")

class INodeAdapter(IApplicationNode):
    """Interface to adapt other Node implementations you want to hook to the
    application.
    """
    
    attrs = Attribute(u"Return adapted node attrs.")
    
    def __init__(node, name, parent):
        """Name and parent are used to hook the correct application hierarchy.
        """
    
    def __getitem__(key):
        """Call and return adapted node's ``__getitem__``.
        """
    
    def __contains__(key):
        """Call and return adapted node's ``__contains__``.
        """
    
    def __len__():
        """Call and return adapted node's ``__len__``.
        """
    
    def __iter__():
        """Call and yields values returned by adapted node's ``__iter__``.
        """
    
    def keys():
        """Call and return adapted node's ``__keys__``.
        """
    
    def values():
        """Call and return adapted node's ``__values__``.
        """
    
    def items():
        """Call and return adapted node's ``__items__``.
        """
    
    def get(key, default=None):
        """Call and return adapted node's ``get``.
        """

class IMetadata(IReadMapping):
    """Interface for providing metadata for application nodes.
    """
    
    def __getattr__(name):
        """Return metadata by attribute access.
        
        Never throws an AttributeError if attribute does not exists, return
        None instead.
        """
    
    def __setattr__(name, value):
        """Set metadata by attribute access.
        """