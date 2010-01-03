from repoze.bfg.security import has_permission
from bda.bfg.tile import (
    tile, 
    registerTile, 
    Tile, 
    TileRenderer, 
    render_template
)
from bda.bfg.app.appstate import appstate
from _kss import ksstile
from _kss import KSSTile
from utils import (
    authenticated, 
    nodepath, 
    make_query, 
    make_url, 
    HTMLRenderer
)

class AppStateAware(object):
    """Mixin for easy AppState access.
    
    Expects 'self.request' on deriving object.
    """
    
    @property
    def appstate(self):
        return appstate(self.request)

class AjaxAware(AppStateAware):
    """Mixin for AJAX handling tiles.
    
    Provide the current valid model context via 'self.curmodel'
    """
    
    @property
    def curmodel(self):
        """Expects 'self.model' on deriving object. Return model by
        'self.appstate.path' if 'self.appstate.ajax' is set.
        """
        model = self.model.root
        if self.appstate.ajax:
            for path in self.appstate.path:
                if not path:
                    continue
                model = model[path]
        else:
            model = self.model
        return model

class PermissionAware(object):
    """Mixin for checking permissions on models.
    
    Expects 'self.request' on deriving object.
    """
    
    def checkpermission(self, permission, model):
        return has_permission(permission, model, self.request)

# XXX this is superfluos since tiles can be less strict.
#class AuthenticationAwareTile(Tile):
#    """Tile mixin. Only rendering if user is authenticated.
#    """
#    
#    @property
#    def show(self):
#        return authenticated(self.request)
#
#class AuthenticationAwareKSSTile(KSSTile, AuthenticationAwareTile):
#    """KSS tile mixin. Only rendering if user is authenticated.
#    """

class KSSMainRenderer(KSSTile):
    """KSS renderer mixin. Rendering the application specific parts to it's
    slots.
    """
    
    def renderpartsformodel(self, model):
        """Render 'mainmenu', 'content' and 'navtree' and 'personaltools'
        tiles on root model.
        """
        core = self.getCommandSet('core')
        core.replaceInnerHTML('#menu',
                              TileRenderer(model,
                                           self.request)('mainmenu'))
        if authenticated(self.request):
            core.replaceInnerHTML('#content',
                                  TileRenderer(model,
                                               self.request)('content'))
        else:
            core.replaceInnerHTML('#content',
                                  TileRenderer(model,
                                               self.request)('loginform'))
        core.replaceInnerHTML('#navtree',
                              TileRenderer(model,
                                           self.request)('navtree'))
        core.replaceInnerHTML('#personaltools',
                              TileRenderer(model,
                                           self.request)('personaltools'))

@ksstile('kssroot')
class KSSRoot(KSSMainRenderer):
    """KSS root tile.
    
    Invoked at logo click (at least).
    """
    
    def render(self):
        self.renderpartsformodel(self.model.root)

@ksstile('content')
class KSSContent(KSSMainRenderer, AjaxAware):
    """KSS content tile.
    
    Invoke this to render content refered by href via AJAX.
    """
    
    def render(self):
        self.renderpartsformodel(self.curmodel)

@tile('personaltools', 'templates/personaltools.pt', strict=False)
class PersonalTools(Tile):
    """Personal tool tile.
    """

@tile('mainmenu', 'templates/mainmenu.pt', strict=False)
class MainMenu(Tile, PermissionAware):
    """Main Menu tile.
    """
    
    @property
    def menuitems(self):
        ret = list()
        count = 0
        path = nodepath(self.model)
        if path:
            curpath = path[0]
        else:
            curpath = ''
        # XXX: self.model.root.values() seem to make troubles if model is
        #      already root.
        for key in self.model.root.keys():
            if not self.checkpermission('view', self.model.root[key]):
                continue
            url = make_url(self.request, path=[key])
            item = dict()
            item['title'] = key
            item['url'] = url
            item['selected'] = curpath == key
            item['first'] = count == 0
            ret.append(item)
            count += 1
        return ret

@ksstile('mainmenu')
class KSSMainMenu(KSSMainRenderer, AjaxAware):
    """KSS main menu tile.
    
    Rendering when a main menu link is clicked.
    """
    
    def render(self):
        self.renderpartsformodel(self.curmodel)

@tile('navtree', 'templates/navtree.pt', strict=False)
class NavTree(Tile, AjaxAware, PermissionAware):
    """Navigation tree tile.
    """
    
    def navtreeitem(self, title, url, path):
        item = dict()
        item['title'] = title
        item['url'] = url
        item['selected'] = False
        item['path'] = path
        item['showchildren'] = False
        item['children'] = list()
        return item
    
    def fillchildren(self, model, path, tree):
        if path:
            curpath = path[0]
        else:
            curpath = None
        for key in model:
            node = model[key]
            if not self.checkpermission('view', node):
                continue
            if not node.in_navtree:
                continue
            title = node.title
            url = make_url(self.request, node=node)
            curnode = curpath == key and True or False
            child = self.navtreeitem(title, url, nodepath(node))
            child['showchildren'] = curnode
            if curnode:
                self.fillchildren(node, path[1:], child)
            selected = False
            if nodepath(self.curmodel) == nodepath(node):
                selected = True
            child['selected'] = selected
            child['showchildren'] = curnode
            tree['children'].append(child)
    
    def navtree(self):
        root = self.navtreeitem(None, None, '')
        model = self.model.root
        path = nodepath(self.model)
        self.fillchildren(model, path, root)
        return root
    
    def rendertree(self, children, level=1):
        return render_template('bda.bfg.app.views:templates/navtree_recue.pt',
                               model=self.model,
                               request=self.request,
                               context=self,
                               children=children,
                               level=level)

@ksstile('navtree')
class KSSNavTree(KSSMainRenderer, AjaxAware):
    """KSS navigation tree tile.
    
    Rendering when a navigation tree. link is clicked.
    """
    
    def render(self):
        self.renderpartsformodel(self.curmodel)

class Batch(Tile):
    """An abstract batch tile.
    
    You have to implement 'self.vocab' and you may override 'self.batchrange',
    'self.display' and 'self.batchname'.   
    """
    dummypage = {
        'page': '',
        'current': False,
        'visible': False,
        'url': '',
    }
    
    ellipsis = u'...'
    
    def render(self):
        return render_template('templates/batch.pt', request=self.request,
                               model=self.model, context=self)
    
    @property
    def vocab(self):
        return []

    @property
    def display(self):
        return True
    
    @property
    def batchrange(self):
        return 30
    
    @property
    def currentpage(self):
        for page in self.vocab:
            if page['current']:
                return page
        return None
    
    @property
    def firstpage(self):
        firstpage = None
        for page in self.vocab:
            if page['visible']:
                firstpage = page
                break
        if not firstpage and self.vocab:
            firstpage = self.vocab[0]
        return firstpage

    @property
    def lastpage(self):
        lastpage = None
        count = len(self.vocab)
        while count > 0:
            count -= 1
            page = self.vocab[count]
            if page['visible']:
                lastpage = self.vocab[count]
                break
        if not lastpage and self.vocab:
            lastpage = self.vocab[len(self.vocab) - 1]
        return lastpage

    @property
    def prevpage(self):
        prevpage = None
        position = self._getPositionOfCurrentInVocab() - 1
        while position >= 0:
            page = self.vocab[position]
            if page['visible']:
                prevpage = self.vocab[position]
                break
            position -= 1
        if not prevpage and self.vocab:
            prevpage = self.dummypage
        return prevpage

    @property
    def nextpage(self):
        nextpage = self.dummypage
        position = self._getPositionOfCurrentInVocab() + 1
        if position == 0 and self.vocab:
            return nextpage
        if position == 0 and not self.vocab:
            return None
        while position < len(self.vocab):
            page = self.vocab[position]
            if page['visible']:
                nextpage = self.vocab[position]
                break
            position += 1
        return nextpage

    @property
    def leftellipsis(self):
        return self._leftOverDiff < 0 and self.ellipsis or None

    @property
    def rightellipsis(self):
        return self._rightOverDiff < 0 and self.ellipsis or None

    @property
    def pages(self):
        position = self._getPositionOfCurrentInVocab()
        count = len(self.vocab)
        start = max(position - self._siderange - max(self._rightOverDiff, 0), 0)
        end = min(position + self._siderange + max(self._leftOverDiff, 0) + 1,
                  count)
        return self.vocab[start:end]
    
    @property
    def _siderange(self):
        return self.batchrange / 2

    @property
    def _leftOverDiff(self):
        currentPosition = self._getPositionOfCurrentInVocab()
        return self._siderange - currentPosition

    @property
    def _rightOverDiff(self):
        position = self._getPositionOfCurrentInVocab()
        count = len(self.vocab)
        return position + self._siderange - count + 1
    
    def _getPositionOfCurrentInVocab(self):
        #TODO: wildcard handling
        current = self.currentpage
        if current is None:
            return -1
        pointer = 0
        for page in self.vocab:
            if page['page'] == current['page']:
                return pointer
            pointer += 1
        return -1

class Form(Tile, HTMLRenderer, AppStateAware):
    """An abstract form tile.
    """
    
    @property
    def factory(self):
        raise NotImplementedError(u"``factory`` property must be provided "
                                   "by deriving object.")
    
    @property
    def formname(self):
        return ''
    
    @property
    def actionnames(self):
        return dict()
    
    @property
    def defaultvalues(self):
        return dict()
    
    @property
    def nexturl(self):
        return self.request.application_url
    
    @property
    def formaction(self):
        return make_url(self.request, node=self.model)
    
    def textinput(self, name):
        value = self.form.data[name]
        payload = self.tag('input',
                           type='text',
                           name=name,
                           value=value)
        return self.wraperror(name, payload)
    
    def passwordinput(self, name):
        payload = self.tag('input',
                           type='password',
                           name=name)
        return self.wraperror(name, payload)
    
    def hiddeninput(self, name, value):
        return self.tag('input', type='hidden', name=name, value=value)
    
    def renderedaction(self, name):
        if name == 'default':
            fieldname = self.formname
        else:
            fieldname = '%s.%s' % (self.formname, name)
        return self.tag('input',
                        type='submit',
                        name=fieldname,
                        _class='formaction',
                        alt='/'.join(nodepath(self.model)),
                        value=self.actionnames.get(name, name))
    
    def wraperror(self, name, payload):
        message = self.form.errors._dict.get(name)
        if not message:
            return self.tag('div',
                            payload,
                            _class='field')
        message = ', '.join(message._messages)
        return self.tag('div',
                        self.tag('div', message, _class='message'),
                        self.tag('div', payload, _class='field'),
                        _class='error')
    
    def __call__(self, model, request):
        self.model = model
        self.request = request
        self.succeed = False
        self.processform()
        self.prepare() # XXX maybe remove.
        if not self.show:
            return ''
        if not self.path:
            raise ValueError(u"Could not render form without template.")
        try: # XXX: do not catch exception.
            if self.succeed and self.appstate.ajax:
                # form returns True in case of success processing. needed
                # for ajax next page rendering.
                return True
            if self.succeed and self.nexturl and not self.appstate.ajax:
                self.redirect(self.nexturl)
            return render_template(self.path, request=request,
                                   model=model, context=self)
        except Exception, e:
            return u"Error:<br /><pre>%s</pre>" % e
    
    def processform(self):
        params = dict()
        params.update(self.request.params)
        appstate = self.appstate
        if appstate.ajax and appstate.formaction:
            params[appstate.formaction] = ''
        self.form = self.factory(data=self.defaultvalues,
                                 params=params,
                                 prefix=self.formname)
        if self.form.action:
            # XXX: request should be allowed additionally
            # XXX: make model providing on form via annotation
            setattr(self.form, '_request', self.request)
            setattr(self.form, 'model', self.model)
            if self.form.validate():
                self.form()
                self.succeed = True

class KSSForm(KSSTile, Form, AjaxAware):
    """Abstract KSS form.
    """
    
    formtile = ''
    formname = ''
    
    def render(self):
        core = self.getCommandSet('core')
        core.replaceHTML('#%s' % self.formname,
                         TileRenderer(self.curmodel,
                                      self.request)(self.formtile))

class ContentReplacingKSSForm(KSSForm):
    """A KSS Form replacing the entire content area instead of the form markup.
    """
    
    nexttile = u'content'
    
    def render(self):
        tile = TileRenderer(self.curmodel, self.request)(self.formtile)
        if tile is True:
            tile = TileRenderer(self.curmodel, self.request)(self.nexttile)
        core = self.getCommandSet('core')
        core.replaceInnerHTML('#content', tile)