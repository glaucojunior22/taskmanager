# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.logo = A(B('{ ',SPAN('A'),' }'),SMALL('Onnix Sistemas'),
                  _class="brand",_href=URL(f='index'))
#response.title = request.application.replace('_',' ').title()
response.title = 'Onnix Sistemas'
response.subtitle = ''

## read more at http://dev.w3.org/html5/markup/meta.name.html
response.meta.author = 'Onnix Desenv <desenv@onnixsistemas.com.br>'
response.meta.description = 'Control calls and customer requests. Management tasks of development and testing.'
response.meta.keywords = 'web2py, python, framework, tasks, tests, solicitations'
response.meta.generator = 'Web2py Web Framework'

## your http://google.com/analytics id
response.google_analytics_id = None

#########################################################################
## this is the main application menu add/remove items as required
#########################################################################

response.menu = [
    (T('Home'), False, URL('default', 'index'), [])
]

DEVELOPMENT_MENU = auth.is_logged_in() and auth.user.email == 'admin@admin.app'

#########################################################################
## provide shortcuts for development. remove in production
#########################################################################

def dev_menu():
    # shortcuts
    app = request.application
    ctr = request.controller
    # useful links to internal and external resources
    response.menu += [
      (SPAN('Admin', _class='highlighted'), False, None, [
        (T('My Sites'), False, URL('admin', 'default', 'site')),
        (T('This App'), False, URL('admin', 'default', 'design/%s' % app), [
          (T('Controller'), False, URL('admin', 'default', 'edit/%s/controllers/%s.py' % (app, ctr))),
          (T('View'), False, URL('admin', 'default', 'edit/%s/views/%s' % (app, response.view))),
          (T('Layout'), False, URL('admin', 'default', 'edit/%s/views/layout.html' % app)),
          (T('Stylesheet'), False, URL('admin', 'default', 'edit/%s/static/css/web2py.css' % app)),
          (T('DB Model'), False, URL('admin', 'default', 'edit/%s/models/db.py' % app)),
          (T('Menu Model'), False, URL('admin', 'default', 'edit/%s/models/menu.py' % app)),
          (T('Database'), False, URL(app, 'appadmin', 'index')),
          (T('Errors'), False, URL('admin', 'default', 'errors/' + app)),
          (T('About'), False, URL('admin', 'default', 'about/' + app)),
        ]),

        (T('Access Control'), False, None, [
          (T('Users'), False, URL('default', 'auth_user')),
          (T('Groups'), False, URL('default', 'auth_group')),
        ]),

      ])]
if DEVELOPMENT_MENU: dev_menu()

if "auth" in locals(): auth.wikimenu() 
