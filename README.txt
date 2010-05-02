Overview
========

``bda.bfg.app`` provides a common web application stub.

This includes a base web application layout, authentication integration,
application model handling, view helpers and commonly needed UI widgets and
AJAX helpers.


Setup
=====

Application egg
---------------

Create your application egg and make it depend on ``bda.bfg.app``. You must
depend your application as well to your prefered ``repoze.what`` plugin, i.e. 
``repoze.what.plugins.ini`` which is used in example below.

Include the package ``bda.bfg.app`` in the ``configure.zcml`` of your 
application egg to make sure everything needed to run the framework is
available.
::

    <configure xmlns="http://namespaces.repoze.org/bfg">
        <include package="bda.bfg.app" />
        ...
    </configure>


Buildout
--------

Assuming ``Paster`` for WSGI deployment and buildout for the application setup,
your (self contained) buildout configuration might look like this.
::

    [buildout]
    parts = instance
    eggs-directory = ${buildout:directory}/eggs
    find-links = 
        http://dist.repoze.org/bfg/1.3/
    develop = .
        
    [instance]
    recipe = repoze.recipe.egg:scripts
    eggs =
        your.application.egg


Authentication and Authorization Configuration
----------------------------------------------

Configure ``repoze.who`` and ``repoze.what`` by providing the
corresponding configuration files.

We configure ``repoze.who`` to use HTTP basic auth via a ``htaccess`` file.
A Plugin that fit our needs for form authentication is shipped with the
``bda.bfg.app`` package.

This is how our ``who.ini`` looks like.
::

    [plugin:loginform]
    use = bda.bfg.app.authentication:make_plugin
    login_form_qs = loginform.__do_login
    rememberer_name = auth_tkt
    
    [plugin:auth_tkt]
    use = repoze.who.plugins.auth_tkt:make_plugin
    secret = secret
    cookie_name = __ac__
    secure = False
    include_ip = False
    
    [plugin:htpasswd]
    use = repoze.who.plugins.htpasswd:make_plugin
    filename = %(here)s/etc/htpasswd
    check_fn = repoze.who.plugins.htpasswd:crypt_check
    
    [general]
    request_classifier = repoze.who.classifiers:default_request_classifier
    challenge_decider = repoze.who.classifiers:default_challenge_decider
    remote_user_key = REMOTE_USER
    
    [identifiers]
    plugins =
          loginform
          auth_tkt
    
    [authenticators]
    plugins = htpasswd
    
    [challengers]
    plugins = loginform


Create ``repoze.what`` configuration, defining plugins to use recognizing 
permissions and groups.
 
The file ``what.ini`` looks like this for using the ``repoze.what.plugins.ini``
adapters.
::

    [plugin:ini_group]
    use = repoze.what.plugins.ini:INIGroupAdapter
    filename = %(here)s/etc/repositories.ini
    
    [plugin:ini_permission]
    use = repoze.what.plugins.ini:INIPermissionsAdapter
    filename = %(here)s/etc/permissions.ini
    
    [what]
    group_adapters = ini_group
    permission_adapters = ini_permission


Read the documentation of ``repoze.what.plugins.ini`` for information about
group and permission configuration via INI files.


Configure the WSGI pipeline
---------------------------

Here we use ``Paster`` to server our application.

We have to provide a configuration for it which wires all the things together.

Create a file like ``yourapplication.ini`` which looks similar to this.
::

    [DEFAULT]
    debug = true
    
    [server:main]
    use = egg:Paste#http
    host = 0.0.0.0
    port = 8080
    
    [app:yourapplication]
    use = egg:yourapplication#app
    reload_templates = true
    filter-with = what
    
    [filter:what]
    use = egg:repoze.what.plugins.config#config
    config_file = %(here)s/what.ini
    who_config_file = %(here)s/who.ini
    
    [pipeline:main]
    pipeline =
        yourapplication


Provide the application
-----------------------

Provide the entry point ``yourapplication#app`` defined in the configuration
above in your ``setup.py``. This entry point returns a WSGI app.
::

    >>> setup(  
    ...     #...  
    ...     entry_points="""\
    ...         [paste.app_factory]
    ...         app = yourapplication.run:app
    ...     """
    ...     #...
    ... )

``yourapplication/run.py`` looks like this.
::

    >>> from repoze.bfg.configuration import Configurator
    >>> from yourapplication.model import get_root
    
    >>> def app(global_config, **settings):
    ...     """ This function returns a WSGI application.
    ...     """
    ...     zcml_file = settings.get('configure_zcml', 'configure.zcml')
    ...     config = Configurator(root_factory=get_root, settings=settings)
    ...     config.begin()
    ...     config.load_zcml(zcml_file)
    ...     config.end()
    ...     return config.make_wsgi_app()


Provide the application model
-----------------------------

The imported get_root function above is responsible to return the application
model root node. Create a file ``model.py`` which looks like.
::

    >>> from bda.bfg.app.model import BaseNode
    
    >>> class Root(BaseNode):
    ...     """Your application root Node.
    ...     """
    ...     title = "YourApplication"
    
    >>> root = Root()
    
    >>> def get_root(environ):
    ...     return root

See documentation of package ``zodict`` for more info about Nodes and section
"Application model" for how it is used in ``bda.bfg.app``. 


Provide a view for your root node
---------------------------------

Now we have to provide a tile. Name it ``content`` and register it for the root 
node in order to render it.

See documentation of package ``bda.bfg.tile`` for more info about tiles and
section "Reserved Tiles" which describe the application layout view hooks for
your model.

Create a package named ``browser`` in you application egg. Define the root 
content tile in ``__init__.py`` of browser package.
::

    >>> from bda.bfg.tile import registerTile
    >>> from bda.bfg.app.browser.layout import ProtectedContentTile
    >>> from yourapplication.model import Root
    
    >>> registerTile('content',
    ...              'yourapplication:browser/templates/root.pt',
    ...              interface=Root,
    ...              class_=ProtectedContentTile,
    ...              permission='login',
    ...              strict=False)

Also create a page template named ``root.pt`` at the pointed location.
::

    <div>
      Root content
    </div>

Now add the following line to your applications ``configure.zcml`` to scan the
available views.
::

     <scan package=".browser" />


Test the setup
--------------

Now the base application setup is done. Test your setup by
::

  - running buildout
  
  - and starting the WSGI pipline like
    ``./bin/paster serve yourapplication.ini``

You should be able now to browse the application at ``localhost:8080``.


The application Model
=====================

XXX


The Application Layout
======================

Tiles and the application
-------------------------

XXX


Reserved tiles
--------------

XXX


Application Widgets
===================

Forms
-----

XXX


Batches
-------

XXX


Application security
====================

Dealing with ACL's
------------------

XXX