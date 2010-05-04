from repoze.bfg.view import bfg_view
from bda.bfg.tile import (
    tile,
    registerTile,
    render_tile,
)
from bda.bfg.app.model import getNodeInfo
from bda.bfg.app.browser import render_main_template
from bda.bfg.app.browser.layout import ProtectedContentTile

@bfg_view('add', permission='login')
def add(model, request):
    return render_main_template(model, request, contenttilename='add')

@tile('add', 'templates/add.pt', permission='login', strict=False)
class AddTile(ProtectedContentTile):
    
    @property
    def addform(self):
        # XXX: better solution maybe with traversal like 'add/factoryname'
        factory = self.request.params.get('factory')
        allowed = self.model.properties.addables
        if not factory or not allowed or not factory in allowed:
            return u'Unknown factory'
        nodeinfo = getNodeInfo(factory)
        addmodel = nodeinfo.node()
        addmodel.__parent__ = self.model
        return render_tile(addmodel, self.request, 'addform')

@bfg_view('edit', permission='login')
def edit(model, request):
    return render_main_template(model, request, contenttilename='edit')

registerTile('edit',
             'bda.bfg.app:browser/templates/edit.pt',
             class_=ProtectedContentTile,
             permission='login',
             strict=False)