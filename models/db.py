# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'
## (optional) static assets folder versioning
# response.static_version = '0.0.0'
#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables

from os import path
URL_PROFILE = path.join(request.folder,'uploads','profile','photos')
auth.settings.extra_fields['auth_user']= [
    Field('job_title', 'string', label=T('Job Title')),
    Field('photo', 'upload', label=T('Photo'), uploadfolder=URL_PROFILE, autodelete=True),
    Field('phone', 'string', label=T('Phone')),
    Field('birthday', 'date', label=T('Birthday')),
    Field('about', 'text', label=T('About Me')),
    ]
auth.define_tables(username=True, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'you@gmail.com'
mail.settings.login = 'username:password'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

## after defining tables, uncomment below to enable auditing
# auth.enable_record_versioning(db)


import uuid
oplink_field = Field('oplink', 'string', 
    label=T('Operation Link'), 
    default=uuid.uuid4, 
    writable=False, 
    readable=False)


db.define_table('platform',
    Field('name', 'string', label=T('Name')),
    migrate="platform.table",
    format='%(name)s')
db.platform.name.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db, 'platform.name')]    


db.define_table('customer',
    oplink_field,
    Field('name', 'string', label=T('Name')),
    Field('phone', 'string', label=T('Phone')),
    Field('contact', 'string', label=T('Contact')),
    Field('email', 'string', label=T('Email')),
    Field('note', 'text', label=T('Note')),
    migrate="customer.table",
    format='%(name)s')
db.customer.name.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db, 'customer.name')]
        

def defaultPlatform():
    r = db(db.platform).select().first()
    return r.id        


PRIORITY_SET = ['Normal', 'Warning', 'Damage']
PRIORITY_REP = {
            PRIORITY_SET[0]:'<span class="label">%s</span>',
            PRIORITY_SET[1]:'<span class="label label-warning">%s</span>',
            PRIORITY_SET[2]:'<span class="label label-damage">%s</span>',
        }


from gluon.tools import prettydate

signature_fields = db.Table(db, 'signature',
    Field('created_on', 'datetime', default=request.now, writable=False, readable=False),
    Field('created_by', db.auth_user, default=auth.user_id, writable=False, readable=False),
    Field('updated_on', 'datetime', update=request.now, writable=False, readable=False),
    Field('updated_by', db.auth_user, update=auth.user_id, writable=False, readable=False))


db.define_table('solicitation',
    oplink_field,
    signature_fields,
    Field('platform_id', db.platform, label=T('Platform'), readable=False, writable=False),
    Field('customer_id', db.customer, label=T('Customer')),
    Field('customer_detail', 'string', label=T('Customer Detail')),
    Field('priority', 'string', label=T('Priority')),
    Field('subject', 'string', label=T('Subject')),
    Field('content_txt', 'text', label=T('Content')),
    Field('is_new', 'boolean', label=T('Is New?')),
    migrate='solicitation.table',
    format='%(subject)s')
db.solicitation.platform_id.requires = IS_IN_DB(db, db.platform, db.platform._format)
db.solicitation.platform_id.default = defaultPlatform
db.solicitation.customer_id.requires = IS_IN_DB(db, db.customer, db.customer._format)
db.solicitation.priority.requires = IS_IN_SET(PRIORITY_SET)
db.solicitation.priority.default = PRIORITY_SET[0]
db.solicitation.priority.represent = lambda value,row: XML(PRIORITY_REP[value] % value)
db.solicitation.subject.requires = [IS_NOT_EMPTY()]
db.solicitation.subject.represent = lambda value,row: XML(value, sanitize=False)
db.solicitation.is_new.default = True


owner_fields = db.Table(db, 'owner',
    Field('owner_table', 'string', label=T('Owner Table'), writable=False, readable=False),
    Field('owner_key', 'string', label=T('Owner Key'), writable=False, readable=False),
    )


url_attachments = path.join(request.folder,'uploads','attachments')

db.define_table('attachments',
    owner_fields,
    oplink_field,
    signature_fields,
    Field('attachment', 'upload', label=T('Attachment'), uploadfolder=url_attachments, autodelete=True),
    Field('name', 'string', label=T('Name'), readable=False, writable=False),
    Field('file_size', 'double', label=T('Size'), readable=False, writable=False),
    migrate='attachments.table',
    format='%(name)s')
db.attachments.file_size.compute = lambda row: path.getsize(path.join(url_attachments,row.attachment))/1024
db.attachments.file_size.represent = lambda value,row: 'teste'


db.define_table('comments',
    owner_fields,
    oplink_field,
    signature_fields,
    Field('comment_str', 'string', label=T('Comment')),
    migrate='comments.table',
    format='%(comment)s')


db.define_table('tag',
    Field('name', 'string', label=T('Name')),
    migrate="tag.table",
    format='%(name)s')
db.tag.name.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db, 'tag.name')]    


db.define_table('tags',
    owner_fields,
    signature_fields,
    Field('tag_id', db.tag, label=T('Tag')),
    migrate='tags.table',
    format='%(tag_id)s')
db.tags.tag_id.requires = IS_IN_DB(db, db.tag, db.tag._format)


db.define_table('releases',
    Field('name', 'string', label=T('Name')),
    Field('started', 'datetime', label=T('Started')),
    Field('is_final', 'boolean', label=T('Is Final')),
    migrate="releases.table",
    format='%(name)s')
db.releases.name.requires = [IS_NOT_EMPTY(),IS_NOT_IN_DB(db, 'releases.name')]
db.releases.started.default = request.now
db.releases.is_final.default = True


TASK_STATUS_SET = ['Analysis', 'Development', 'Test', 'Released']
TEST_STATUS_SET = ['Waiting', 'Success', 'Error', 'Retest']

db.define_table('task',
    owner_fields,
    oplink_field,
    signature_fields,
    Field('platform_id', db.platform, label=T('Platform'), readable=False, writable=False),
    Field('user_task', db.auth_user, label=T('User Task')),
    Field('priority', 'string', label=T('Priority')),
    Field('status', 'string', label=T('Status')),
    Field('what', 'text', label=T('What?')),
    Field('note', 'text', label=T('Note')),
    Field('test_status', 'string', label=T('Test Status')),
    Field('test_release', db.releases, label=T('Test Release')),
    Field('final_release', db.releases, label=T('Final Release')),
    migrate='task.table',
    format='%(what)s')
db.task.platform_id.requires = IS_IN_DB(db, db.platform, db.platform._format)
db.task.platform_id.default = defaultPlatform
db.task.user_task.default = auth.user_id
db.task.user_task.represent = lambda value,row: '%(first_name)s %(last_name)s' % db.auth_user[value]
db.task.priority.requires = IS_IN_SET(PRIORITY_SET)
db.task.priority.default = PRIORITY_SET[0]
db.task.priority.represent = lambda value,row: XML(PRIORITY_REP[value] % value)
db.task.status.requires = IS_IN_SET(TASK_STATUS_SET)
db.task.status.default = TASK_STATUS_SET[0]
db.task.what.requires = [IS_NOT_EMPTY()]
db.task.test_status.requires = IS_EMPTY_OR(IS_IN_SET(TEST_STATUS_SET))
db.task.test_release.requires = IS_EMPTY_OR(IS_IN_DB(db, db.releases, db.releases._format))
db.task.final_release.requires = IS_EMPTY_OR(IS_IN_DB(db, db.releases, db.releases._format))


TEST_RESULT_SET = ['Success', 'Error']
TEST_RESULT_REP = {
            TEST_RESULT_SET[0]:'<span class="label label-success">%s</span>',
            TEST_RESULT_SET[1]:'<span class="label label-important">%s</span>',
        }

db.define_table('test',
    owner_fields,
    signature_fields,
    Field('test_result', 'string', label=T('Result')),
    Field('note', 'text', label=T('Note')),
    migrate='test.table',
    format='%(note)s')
db.test.test_result.requires = IS_IN_SET(TEST_RESULT_SET)
db.test.test_result.default = TEST_RESULT_SET[0]
db.test.test_result.represent = lambda value,row: XML(TEST_RESULT_REP[value] % value)
