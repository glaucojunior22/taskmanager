# -*- coding: utf-8 -*-


if db(db.auth_user).isempty():
	#try:
	group_id = db.auth_group.insert(role='Admin', description='Admin')

	defaults = my_default_values(db.auth_user)
	defaults['first_name'] = 'Admin'
	defaults['last_name'] = 'Admin'
	defaults['email'] = 'admin@admin.app'
	defaults['username'] = 'admin'
	defaults['password'] = db.auth_user.password.validate('admin')[0]
	user_id = db.auth_user.insert(**defaults)

	auth.add_membership(group_id, user_id)
	#except: pass

if db(db.platform).isempty():
	try:
		db.platform.insert(name='Onnix Sistemas')
	except: pass