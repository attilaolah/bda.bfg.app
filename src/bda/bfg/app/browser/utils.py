from repoze.bfg.security import authenticated_userid

def authenticated(request):
    return authenticated_userid(request)

def nodepath(node):
    return [p for p in node.path if p is not None]

def make_query(**kw):
    query = list()
    for name, param in kw.items():
        if param is None:
            continue
        if isinstance(param, basestring):
            param = [param]
        for p in param:
            query.append('%s=%s' % (name, p))
    return '?%s' % '&'.join(query)

def make_url(request, path=[], node=None, resource=None, query=None):
    if node is not None:
        path = nodepath(node)
    if resource is not None:
        path.append(resource)
    if not query:
        return '%s/%s' % (request.application_url, '/'.join(path))
    return '%s/%s%s' % (request.application_url, '/'.join(path), query)

class AppUtil(object):
    """Instance of this object gets Passed to main template when rendering.
    """
    
    def authenticated(self, request):
        return authenticated(request)
    
    def nodepath(self, node):
        return nodepath(node)
    
    def make_url(self, request, path=[], node=None, resource=None, query=None):
        return make_url(request, path, node, resource, query)
    
    def make_query(self):
        return make_query(**kw)