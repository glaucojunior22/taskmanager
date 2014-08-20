# -*- coding: utf-8 -*-


SMALL = lambda x, **kwargs: XML(TAG.small(x, **kwargs).xml())
SUP = lambda x, **kwargs: XML(TAG.sup(x, **kwargs).xml())


def getlist(x, index, default=None):
	return x[index] if len(x) > index else default


def alert_gedgat_error(msg):
	alert = DIV(
		BUTTON('&times;', _type='button', _class='close', **{'_data-dismiss':'alert'}),
		STRONG(T('ERROR!')),
		SPAN(T(msg)),
		_class='alert alert-error')
	return alert


def my_represent_field(field, value, row):

	def format(table, record):
		if isinstance(table._format,str):
			return table._format % record
		elif callable(table._format):
			return table._format(record)
		else:
			return '#'+str(record.id)

	if callable(field.represent):
		return field.represent(value, row)

	referee = field.type[10:]
	if referee:
		record = db[referee]('id')
		value = format(db[referee], record)

	return value


def my_default_values(table):
    defaults = {}
    for fname in table.fields:
        if table[fname].default:
            if callable(table[fname].default):
                defaults[fname] = table[fname].default()
            else:
                defaults[fname] = table[fname].default
    return defaults


def nic_editor_js(field_name, width='750px'):
    js = '''
        jQuery(document).ready(function(){
            jQuery('#%(field_name)s').css('width','%(width)s').css('height','100px');

            var wysiwygfield = new nicEditor({
                fullPanel : true,
                iconsPath :"%(iconsPath)s",
                uploadURI :"%(uploadURI)s",
            })
            wysiwygfield.panelInstance("%(field_name)s");
            jQuery('input[type=submit]').click(function(){
                wysiwygfield.panelInstance("%(field_name)s");});
        }); 
        ''' % {
            'field_name':field_name,
            'width': width,
            'iconsPath':URL(c='static', f='nicEdit/nicEditorIcons.gif'),
            'uploadURI':URL(c='uploads', f='nicedit_image', args=[field_name]),
        }
    return SCRIPT(js, _type='text/javascript')


def get_user_photo_url(user_id):
    url = URL('static','images/user-comment.png')
    if user_id == auth.user_id:
        if auth.user.photo:
            url = URL('default', 'download', args=auth.user.photo)
    elif db.auth_user[user_id].photo:
        url = URL('default', 'download', args=db.auth_user[user_id].photo)
    return url
