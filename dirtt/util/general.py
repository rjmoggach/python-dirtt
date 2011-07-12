import re
import pwd
import grp


def get_gid_for_name(group, default=0):
	"""
	returns gid for a given name string
	"""
	if not group is None:
		try: gid = grp.getgrname(group).gr_gid
		except KeyError: gid = default
	return gid


def get_uid_for_name(username, default=0):
	"""
	returns gid for a given name string
	"""
	if not username is None:
		try:
			uid = pwd.getpwnam(username).pw_uid
		except KeyError:
			uid = default
	return uid


def print_array(array,tab=0):
	'''
	function to iterate through an array
	'''
	# are there any keys?
	indexes = array.keys()
	indexes.sort()
	for i in indexes:
		# check if the value is another array?
		if type(array[i]) is dict:
			# value is an array
			print "%s * %s =>" % ('\t'*tab,i)
			# print the key, and spawn print_array again to print the next level of the array
			print_array(array[i],tab=tab+1)
		else:
			# value is not an array - print the key and the value
			print "%s + %s => %s" % ('\t'*tab,i,array[i])


def randstring():
	"""
	Generate an 8 random character name for tempfiles
	"""
	chars = string.letters + string.digits
	rnd = ''
	for i in range(8):
		rnd = rnd + choice(chars)
	return rnd


def clean_string(bad_text):
	## convert the text
	# lower case everything - and trim before and after
	#wash = string.lower(bad_text).strip()
	wash = string.strip(bad_text)
	# change - & " " to _
	#soap = re.sub('([\ -])','_',wash)
	soap = re.sub('([\ ])','_',wash)
	# strip out strange characters
	rinse = re.sub('[^A-za-z0-9-_\.<>%]','',soap)
	# squeeze reapeting "_"'s
	spin = re.sub('[_]+','_',rinse)
	return spin


def convert_bytes_to_readable(bytes):
	"""Convert bytes to KB, MB, GB, or TB depending
	   on how long the number is"""
	if bytes < 1024:
		converted = bytes
		unit = 'Bytes'
	elif bytes < 2**20:
		converted = "%.2f" % (bytes/float(2**10))
		unit = 'KB'
	elif bytes < 2**30:
		converted = "%.2f" % (bytes/float(2**20))
		unit = 'MB'
	elif bytes < 2**40:
		converted = "%.2f" % (bytes/float(2**30))
		unit = 'GB'
	elif bytes < 2**50:
		converted = "%.2f" % (bytes/float(2**40))
		unit = 'TB'
	else:
		converted = "%.2f" % (bytes/float(2**50))
		unit = 'PB'
	return converted,unit
