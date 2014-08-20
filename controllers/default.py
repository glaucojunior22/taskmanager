# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################


testable_tasks = (db.task.status == TASK_STATUS_SET[2]) & (db.task.test_status.belongs(TEST_STATUS_SET[0], TEST_STATUS_SET[3])) 

@auth.requires_login()
def index():
    news_solicitations = db(db.solicitation.is_new == True).select()
    my_tasks = db((db.task.user_task == auth.user_id) &
        (db.task.status.belongs(TASK_STATUS_SET[0], TASK_STATUS_SET[1], TASK_STATUS_SET[2]) )
        ).select()
    waiting_test = db(testable_tasks).select(orderby=db.task.test_release)

    return dict(news_solicitations=news_solicitations, my_tasks=my_tasks, waiting_test=waiting_test)


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/manage_users (requires membership in
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    if request.args(0) == 'profile':
        response.view = 'default/profile.html'
        response.title = T('Profile')+'...'
    return dict(form=auth())

@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())


def _get_crud_id():
    if not request.args(1) or not request.args[1].isdigit():
        raise HTTP(404)
    return int(request.args[1])


def app_crud(table, **attr):
    action = request.args(0) or ''
    if not action in ('new','edit', 'remove', 'delete'):
        raise HTTP(404)

    if action == 'new':
        response.subtitle = T('New Record')
        content = crud.create(table, **attr)
    else:
        id = _get_crud_id()

        if isinstance(table._format,str):
            registro = table._format % table[id]
        else:
            registro = table._format(table[id])

        if action == 'remove':
            response.subtitle = T('Confirm delete "')+ registro +'" ?'
            content = crud.read(table, id)
        elif action == 'delete':
            crud.delete(table, id, **attr)
        else:
            response.subtitle = T('Editing: ')+ registro
            content = crud.update(table, id, deletable=False, **attr)
    response.title = T(table._plural)    
    return content


from gluon.dal import Table
def app_crud_grid(table, controller=request.controller, function=request.function, **attr):
    exportclasses = dict(
        csv_with_hidden_cols=False,
        json=False,
        tsv_with_hidden_cols=False,
        tsv=False
    )

    links = []
    extra_links = attr.get('extra_links', [])
    links += [link for link in extra_links]

    if attr.get('show_link_edit', True):
        caption = '' if len(extra_links) else ' '+T('Edit')
        links += [lambda row: A(
            SPAN(_class="icon pen icon-pencil")+ caption,
            _href=URL(c=controller, f=function, args=['edit', row.id]), 
            _class="w2p_trap button btn btn-small")]

    if attr.get('show_link_remove', True):
        links += [lambda row: A(
            SPAN(_class="icon icon-trash"),
            _href=URL(c=controller, f=function, args=['remove', row.id]), 
            _class="w2p_trap button btn btn-small")]

    local_attr = dict(
        user_signature=False,
        exportclasses=exportclasses,
        deletable=False,
        editable=False,
        details=False,
        create=False,
        links=links,
        args=[],
        paginate=25,
        maxtextlength=50,
        #maxtextlengths=maxtextlengths,      
        #field_id=None,
        #left=None,
        #headers={},
        #orderby=None,
        #groupby=None,
        #searchable=True,
        #sortable=True,
        #selectable=None,
        #csv=True,
        #links_in_grid=True,
        #upload='<default>',
        #onvalidation=None,
        #oncreate=None,
        #onupdate=None,
        #ondelete=None,
        #sorter_icons=(XML('&#x2191;'), XML('&#x2193;')),
        #ui = 'web2py',
        #showbuttontext=True,
        #_class="web2py_grid",
        #formname='web2py_grid',
        #search_widget='default',
        #ignore_rw = False,
        #formstyle = 'table3cols',
        #formargs={},
        #createargs={},
        #editargs={},
        #viewargs={},
        #buttons_placement = 'right',
        #links_placement = 'right'
        )
    local_attr.update(attr)

    for kname in ['extra_links', 'show_link_edit', 'show_link_remove']:
        if local_attr.has_key(kname):
            del local_attr[kname]

    grid = SQLFORM.grid(table, **local_attr)
    if isinstance(table, Table):
        response.title = T(table._plural)    
        response.subtitle = T('Listing')
    return grid


def _get_tags_widget(oplink, searchable=False):
    if searchable:
        tr = TR(
            LOAD(f='tags_list.load', args=['solicitation', oplink], vars={'searchable':True}, ajax=True),)
    else:
        tr = TR(
            LOAD(f='tags_list.load', args=['solicitation', oplink], ajax=True),
            LOAD(f='tags_form.load', args=['solicitation', oplink], ajax=True),)
    return TABLE(tr)


def solicitation_accept(form):
    id = int(form.vars.id)
    row = db(db.solicitation.id == id).select().first()
    db(db.tags.owner_key == session.auth.hmac_key).update(owner_key=row.oplink)
    return


@auth.requires_login()
def solicitation():
    action = request.args(0) or ''

    if action == '':
        extra_links =  [lambda row: A(
            SPAN(_class="icon icon-eye-open")+' '+T('Detail'),
            _href=URL(f='solicitation_detail', args=[row.id]), 
            _class="w2p_trap button btn btn-small")]
        content = app_crud_grid(db.solicitation, 
            controller=request.controller, 
            function=request.function,
            **dict(extra_links=extra_links, orderby=~db.solicitation.id) )
    else:
        my_extra_element = None
        attr = dict(
            next=URL(f='index') if action == 'delete' else URL(f='solicitation_detail')+'/[id]',
            )

        if action == 'new':
            content = crud.create(db.solicitation, onaccept=lambda form:solicitation_accept(form), **attr)
            my_extra_element = TR(LABEL(T('Tags')+':'), _get_tags_widget(session.auth.hmac_key))
            response.title = T(db.solicitation._plural)    
            response.subtitle = T('New Record')
        else:
            if action == 'edit':
                row = db(db.solicitation.id == _get_crud_id()).select().first()
                my_extra_element = TR(LABEL(T('Tags')+':'), _get_tags_widget(row.oplink))
            content = app_crud(db.solicitation, **attr)

        if my_extra_element:
            content[0].insert(-1,my_extra_element)
        if action in ('new', 'edit'):
            my_extra_element = nic_editor_js('solicitation_content_txt')
            content[0].insert(-1, my_extra_element)

    return dict(content=content)


@auth.requires_login()
def solicitation_detail():
    if not request.args(0) or not request.args[0].isdigit():
        raise HTTP(404)
    id = int(request.args[0])

    record = db(db.solicitation.id == id).select().first()

    response.title = T(db.solicitation._plural)    
    response.subtitle = T('Detail')
    return dict(record=record)


def solicitation_preview():
    record = None
    if request.vars.get('oplink'):
        oplink = request.vars.get('oplink')
        record = db(db.solicitation.oplink == oplink).select().first()
    elif request.vars.get('record_id'):
        id = int(request.vars.get('record_id'))
        record = db(db.solicitation.id == id).select().first()
    if not record:
        response.view = 'default/gadget_error.html'        
        return dict(msg='solicitation preview dont work!')

    tags = _get_tags_widget(record.oplink, searchable=True)
    return dict(record=record, tags=tags)


@auth.requires_login()
def customer():
    response.view = 'default/generic_crud.html'
    action = request.args(0) or ''

    if action == '':
        content = app_crud_grid(db.customer, controller=request.controller, function=request.function)
    else:
        content = app_crud(db.customer)
    return dict(content=content)


def attachments():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='attachments dont work!')
    
    delete_id = request.vars.get('delete', 0)
    if delete_id:
        db(db.attachments.id == delete_id).delete()

    db.attachments.owner_table.default = owner_table
    db.attachments.owner_key.default = owner_key
    query = ((db.attachments.owner_table == owner_table) & (db.attachments.owner_key == owner_key))

    form = SQLFORM(db.attachments, upload=url_attachments)

    if request.vars.attachment != None:
        form.vars.name = request.vars.attachment.filename
        form.post_vars = form.vars.name
    form.process()

    content = db(query).select()
    return dict(form=form, content=content)


def attachment_download():
    if not request.args(0) or not request.args[0].isdigit():
        raise HTTP(404)
    id = int(request.args[0])
    import cStringIO 
    import contenttype as c
    s=cStringIO.StringIO() 
     
    (filename,file) = db.attachments.attachment.retrieve(db.attachments[id].attachment)
    s.write(file.read())  
    response.headers['Content-Type'] = c.contenttype(filename)
    response.headers['Content-Disposition'] = "attachment; filename=%s" % filename  
    return s.getvalue()


def comments_list():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='comments/reply dont work!')

    def get_comments(t, k):
        clist = []
        query = ((db.comments.owner_table == t) & (db.comments.owner_key == k))
        for row in db(query).select():
            clist.append( (row, get_comments('comments', row.oplink)) )
        return clist 

    def html_comments(clist, is_reply):
        comments = []
        for (row, reply) in clist:
            reply_mark = SPAN(' ', T('reply'), _class='muted')
            remove_link = A(' '+T('Remove'), _href='javascript:void(0);', _id='comment_%s' % row.id, _class='remove-comment')
            dh_mark = SMALL([
                SPAN(prettydate(row.updated_on, T), _class='muted'),
                remove_link if row.updated_by == auth.user.id else ''] )
            right_wgt = DIV(dh_mark, _class='pull-right')            
            
            header_wgt = DIV(
                STRONG('%(first_name)s %(last_name)s' % db.auth_user[row.updated_by]),
                reply_mark if is_reply else '',
                right_wgt)

            reply_rows = html_comments(reply, True)

            hidden_wgt = INPUT(_id='owner_key', _value=row.oplink, _type='hidden')

            reply_link = DIV(
                A(T('Reply'), _href='javascript:void(0);', _class='reply-link'),
                hidden_wgt,
                _id='reply_%s' % row.id
                )
            comment_wgt = DIV(
                P(row.comment_str),
                reply_link,
                reply_rows
                )

            img_wgt = DIV(
                DIV(IMG(_src=get_user_photo_url(row.updated_by)), 
                    _style='width:64px; height:64px; max-width:64px; overflow:hidden;'),
                    _class='span1')
            body_wgt = DIV(
                header_wgt, 
                comment_wgt,
                _class='span11')
            row_wgt = DIV(img_wgt, body_wgt, _class='row-fluid')

            comments += [row_wgt]

        js = '''
            $(document).ready(function() {
                $(".reply-link").click(function () {
                    var parentTag = $( this ).parent();
                    var k = $(parentTag).find("#owner_key").val();
                    var url = '%(url_reply)s?reply='+k+'&wgt='+parentTag.get(0).id;
                    $.web2py.component(url, parentTag.get(0).id );
                });
                $(".reply-cancel").click(function () {
                    $.web2py.component('%(url_list)s','comments_list');
                });    
                $(".remove-comment").click(function () {
                    var str = $(this).get(0).id;
                    var id = str.split("_")[1];

                    var url = '%(url_remove)s';
                    ajax(url + '?delete=' + id, [], '');
                });
            });             
            ''' % {
                'url_remove':URL(f='comments_remove', args=[owner_table, owner_key]),
                'url_reply': URL(f='comments_form.load', args=[owner_table, owner_key]),
                'url_list': URL(f='comments_list.load', args=[owner_table, owner_key]),
                }
        comments += [SCRIPT(js, _type='text/javascript')]
        return DIV(comments, _id='comments_list')

    clist = get_comments(owner_table, owner_key)
    comments = html_comments(clist, False)
    return dict(comments=comments)


def comments_form():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='comments dont work!')
    
    db.comments.owner_table.default = owner_table
    db.comments.owner_key.default = owner_key
    reply_key = request.vars.get('reply')
    if reply_key:
        db.comments.owner_table.default = 'comments'
        db.comments.owner_key.default = reply_key

    form = SQLFORM(db.comments)
    form.elements('#comments_comment_str')[0] ['_placeholder'] = T('Comment...') 
    form.elements('#comments_comment_str')[0] ['_style'] = 'width:100%;'

    if form.process().accepted:
        response.js = "web2py_component('%s','comments_list');" % URL(f='comments_list.load', args=[owner_table, owner_key])

    return dict(form=form)


def comments_remove():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    delete_id = request.vars.get('delete', 0)
    if delete_id:
        db(db.comments.id == delete_id).delete()    
        response.js = "web2py_component('%s','comments_list');" % URL(f='comments_list.load', args=[owner_table, owner_key])
    pass


@auth.requires_login()
def tag():
    response.view = 'default/generic_crud.html'
    action = request.args(0) or ''

    if action == '':
        content = app_crud_grid(db.tag, controller=request.controller, function=request.function)
    else:
        content = app_crud(db.tag)
    return dict(content=content)


def tags_form():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='tags dont work!')
    
    form = SQLFORM.factory(Field('tag_name', notnull=True))
    form.elements('#no_table_tag_name')[0] ['_placeholder'] = T('Enter to post...') 
    form.elements('#no_table_tag_name')[0] ['_list'] = 'tagname_list'
    form.elements('#no_table_tag_name')[0] ['_style'] = 'width:120px;'
    if form.process().accepted:
        record = db(db.tag.name == request.vars.tag_name).select().first()
        if record:
            tag_id = record.id
        else:
            tag_id = db.tag.insert(name=request.vars.tag_name)

        query = ((db.tags.owner_table == owner_table) & (db.tags.owner_key == owner_key) & (db.tags.tag_id == tag_id))
        record = db(query).select().first()
        if not record:
            db.tags.insert(
                owner_table=owner_table,
                owner_key=owner_key,
                created_on=request.now,
                created_by=auth.user_id,
                updated_on=request.now,
                updated_by=auth.user_id,
                tag_id=tag_id, )
            response.js = "web2py_component('%s','tags_list');" % URL(f='tags_list.load', args=[owner_table, owner_key])
    tagname_list = [row.name for row in db(db.tag).select(orderby=db.tag.name)]
    return dict(form=form, tagname_list=tagname_list)


def tags_list():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='tags dont work!')

    searchable = request.vars.get('searchable', False)

    clist = []
    query = ((db.tags.owner_table == owner_table) & (db.tags.owner_key == owner_key) & (db.tag.id == db.tags.tag_id))
    for row in db(query).select():
        if searchable:
            tag = A(
                SPAN(T(row.tag.name), _class='label label-info'), 
                _href=URL(c='default', f='report.html', vars=dict(tag=row.tag.name)))
        else:
            tag = A(
                SPAN(T(row.tag.name), _class='label label-info'), 
                _href='javascript:void(0);', _id='tag_%s' % row.tags.id, _class='remove-tag')
        clist.append(tag)
        clist.append(SPAN(' '))

    if not searchable:
        js = '''
            $(document).ready(function() {
                $(".remove-tag").click(function () {
                    var str = $(this).get(0).id;
                    var id = str.split("_")[1];

                    var url = '%(url_remove)s';
                    ajax(url + '?delete=' + id, [], '');
                });
            });             
            ''' % {
                    'url_remove':URL(f='tags_remove', args=[owner_table, owner_key]),
                    }
        clist.append( SCRIPT(js, _type='text/javascript') )
    tags = DIV(clist, _id='tags_list')
    return dict(tags=tags)


def tags_remove():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    delete_id = request.vars.get('delete', 0)
    if delete_id:
        db(db.tags.id == delete_id).delete()    
        response.js = "web2py_component('%s','tags_list');" % URL(f='tags_list.load', args=[owner_table, owner_key])
    pass


@auth.requires_login()
def releases():
    response.view = 'default/generic_crud.html'
    action = request.args(0) or ''

    if action == '':
        content = app_crud_grid(db.releases, controller=request.controller, function=request.function)
    else:
        content = app_crud(db.releases)
    return dict(content=content)


@auth.requires_login()
def task():
    action = request.args(0) or ''

    if action == '':
        extra_links =  [lambda row: A(
            SPAN(_class="icon icon-eye-open")+' '+T('Detail'),
            _href=URL(f='task_detail', args=[row.id]), 
            _class="w2p_trap button btn btn-small")]
        content = app_crud_grid(db.task, 
            controller=request.controller, 
            function=request.function,
            **dict(extra_links=extra_links,orderby=~db.task.id) )
    else:
        attr = dict(
            next=URL(f='index') if action == 'delete' else URL(f='task_detail')+'/[id]',
            fields=['user_task', 'priority', 'status', 'what'],
            )
        if request.vars.get('next'):
            attr['next'] = request.vars['next']
        
        if action == 'delete':
            del attr['fields']
        elif action == 'new':#spare task
            db.task.owner_table.default = 'task'
            db.task.owner_key.default = uuid.uuid4()

        content = app_crud(db.task, **attr)
        if action in ('new', 'edit'):
            my_extra_element = nic_editor_js('task_what')
            content[0].insert(-1, my_extra_element)
        if action == 'edit':
            response.subtitle = T('Editing...')
    return dict(content=content)


@auth.requires_login()
def solicitation_to_task():
    owner_key = request.args(0) or ''
    solicitation = db(db.solicitation.oplink == owner_key).select().first()
    if not solicitation:
        raise HTTP(404)
    
    defaults = my_default_values(db.task)
    defaults['owner_table'] = 'solicitation'
    defaults['owner_key'] = owner_key
    defaults['what'] = solicitation.content_txt

    id = db.task.insert(**defaults)
    db(db.solicitation.oplink == owner_key).update(is_new=False)

    redirect(URL(f='task_detail', args=[id]))
    return


def tasks_list():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='tasks dont work!')

    query = ((db.task.owner_table == owner_table) & (db.task.owner_key == owner_key))
    
    tasks = db(query).select()
    return dict(tasks=tasks)


def tasks_modal_form():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='task form dont work!')

    edit_id = request.vars.get('edit', 0)
        
    db.task.owner_table.default = owner_table
    db.task.owner_key.default = owner_key

    form = SQLFORM(db.task, edit_id, fields=['user_task', 'priority', 'status', 'what'])

    my_extra_element = nic_editor_js('task_what', '500px')
    form[0].insert(-1, my_extra_element)

    if form.process().accepted:
        if owner_table == 'solicitation':
            db(db.solicitation.oplink == owner_key).update(is_new=False)
        response.js = "$('#dialog_modal').modal('hide'); web2py_component('%s','tasks_list');" % URL(f='tasks_list.load', args=[owner_table, owner_key])

    return dict(form=form)


@auth.requires_login()
def task_detail():
    if not request.args(0) or not request.args[0].isdigit():
        raise HTTP(404)
    id = int(request.args[0])
    table = db.task

    record = db(db.task.id == id).select().first()

    has_test = db((db.test.owner_table == 'task') & (db.test.owner_key == record.oplink)).count()

    response.title = T(table._plural)    
    response.subtitle = T('Detail')
    return dict(record=record,has_test=has_test)


def task_remove():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    delete_id = request.vars.get('delete', 0)
    if delete_id:
        db(db.task.id == delete_id).delete()    
        response.js = "web2py_component('%s','tasks_list');" % URL(f='tasks_list.load', args=[owner_table, owner_key])
    pass


def task_detail_form():
    if not request.args(0) or not request.args[0].isdigit():
        raise HTTP(404)
    id = int(request.args[0])

    form = SQLFORM(db.task, id, fields=['note', 'status', 'final_release', 'test_status', 'test_release'])

    my_extra_element = DIV( nic_editor_js('task_note', '100%'), _id='task_detail_form_nic')
    form[0].insert(-1, my_extra_element)

    form.elements('#task_status')[0] ['_style'] = 'width:100%;'
    form.elements('#task_final_release')[0] ['_style'] = 'width:100%;'
    form.elements('#task_test_status')[0] ['_style'] = 'width:100%;'
    form.elements('#task_test_release')[0] ['_style'] = 'width:100%;'

    if form.process().accepted:
        response.js = 'window.location.reload(true);'

    return dict(form=form)


@auth.requires_login()
def tests():
    if not request.args(0) or not request.args[0].isdigit():
        raise HTTP(404)
    id = int(request.args[0])
    table = db.task

    record = db(db.task.id == id).select().first()
    next_test = db((db.task.id > id) &
        (db.task.test_release == record.test_release) &
        testable_tasks).select(limitby=(0,1)).first()

    response.title = T('Tests')    
    response.subtitle = T('Task')

    db.test.owner_table.default = 'task'
    db.test.owner_key.default = record.oplink

    form = SQLFORM(db.test, fields=['note', 'test_result'])

    my_extra_element = DIV( nic_editor_js('test_note', '100%'), _id='test_form_nic')
    form[0].insert(-1, my_extra_element)
    form.elements('#test_test_result')[0] ['_style'] = 'width:100%;'

    if form.process().accepted:
        record.update_record(test_status=form.vars.test_result)        
        next = form.vars.get('next')
        redirect(next or URL(f='index'))

    has_test = db((db.test.owner_table == 'task') & (db.test.owner_key == record.oplink)).count()

    return dict(record=record,next_test=next_test, form=form, has_test=has_test)


def tests_list():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key):
        response.view = 'default/gadget_error.html'        
        return dict(msg='tests dont work!')

    query = ((db.test.owner_table == owner_table) & (db.test.owner_key == owner_key))
    
    tests = db(query).select()
    return dict(tests=tests)


@auth.requires_login()
def release_history():
    orderby = (~db.releases.is_final | ~db.releases.id)
    releases = db(db.releases.id > 0).select(orderby=orderby)
    if not request.args(0) or not request.args[0].isdigit():
        release_id = releases[0].id
    else:
        release_id = int(request.args[0])    

    history = app_crud_grid((db.task.final_release == release_id),
        controller=request.controller, 
        function=request.function,
        **dict(show_link_edit=False, show_link_remove=False))
    response.title = T('Release History')    
    response.subtitle = T('Report')
    return dict(releases=releases, history=history)


@auth.requires(auth.has_membership(role='Admin'))
def auth_user():
    action = request.args(0) or ''

    if action == '':
        content = app_crud_grid(db.auth_user)
    else:
        attr = dict()
        if action == 'new':
            attr['next'] = URL(f='auth_user', args=['edit'])+'/[id]'
        else:
            next = URL(f='auth_user')

        content = app_crud(db.auth_user, **attr)
    return dict(content=content)


@auth.requires(auth.has_membership(role='Admin'))
def auth_group():
    action = request.args(0) or ''

    if action == '':
        content = app_crud_grid(db.auth_group)
    else:
        content = app_crud(db.auth_group, **dict(next=URL(f='auth_group')))
    return dict(content=content)


def auth_groups():
    owner_table = getlist(request.args, 0)
    owner_key  = getlist(request.args, 1)
    if not (owner_table and owner_key and owner_key.isdigit()):
        response.view = 'default/gadget_error.html'        
        return dict(msg='access control groups dont work!')

    def getContentLocal():
        if owner_table == 'user':
            return [(row.auth_group.id, row.auth_group.role, row.auth_membership.id or 0) for row in 
                db().select(db.auth_group.ALL, db.auth_membership.id, 
                    left=db.auth_membership.on((db.auth_membership.group_id==db.auth_group.id) & (db.auth_membership.user_id == int(owner_key))))]
        else:
            return [(row.auth_user.id, '%(first_name)s %(last_name)s' % row.auth_user, row.auth_membership.id or 0) for row in 
                db().select(db.auth_user.ALL, db.auth_membership.id, 
                    left=db.auth_membership.on((db.auth_membership.user_id==db.auth_user.id) & (db.auth_membership.group_id == int(owner_key))))]

    content = getContentLocal()
    fields = [Field('record_'+str(k), 'boolean') for k, d, m in content]
    buttons = [INPUT(_type='submit', _value=T('Connect'), _class='btn')]
    form = SQLFORM.factory(*fields, buttons=buttons)
    if form.process(formname='auth_groups_form').accepted:
        for k, d, m in content:
            user_id, group_id = k, int(owner_key)
            if owner_table == 'user':
                user_id, group_id = int(owner_key), k

            checked = form.vars.get('record_'+str(k), False)
            if checked != (m>0):
                if checked:
                    db.auth_membership.insert(user_id=user_id, group_id=group_id)
                else:
                    db(db.auth_membership.id==m).delete()
        content = getContentLocal()
    return dict(form=form, content=content)


@auth.requires_login()
def test_history():
    orderby = (~db.releases.is_final | ~db.releases.id)
    releases = db(db.releases.id > 0).select(orderby=orderby)
    if not request.args(0) or not request.args[0].isdigit():
        release_id = releases[0].id
    else:
        release_id = int(request.args[0])    

    history = app_crud_grid((db.task.test_release == release_id),
        controller=request.controller, 
        function=request.function,
        **dict(show_link_edit=False, show_link_remove=False))
    response.title = T('Test History')    
    response.subtitle = T('Report')
    response.view = 'default/release_history.html'        
    return dict(releases=releases, history=history)