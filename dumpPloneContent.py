# trs22@psu.edu
# Start Zope with:
#    sudo  /opt/plone-4.1.6/zeocluster/bin/client1 debug
# 
# Paste below into debug prompt (after >>>)

from zope.component import getSiteManager
from zope.component import getUtility
from Products.CMFCore.utils import getToolByName
from DateTime import DateTime
from Testing.makerequest import makerequest
from zope.app.component.hooks import setSite, getSite
from Products.CMFPlone.utils import safe_unicode
import Missing

def getExtension(i):
    c = i.content_type
    return {'image/png' : 'png',
            'image/gif' : 'gif',
            'image/jpeg' : 'jpg',
            'application/pdf' : 'pdf',
    }.get(c, 'data')

def getText(object):
    if object.portal_type in ['Folder', 'PhotoFolder'] or object.meta_type in ['Blog', 'Subsite', 'Section', 'ATFolder', 'PhotoFolder', 'FormFolder']:
        try:
            text = object.folder_text()
        except AttributeError:
            text = ""
    elif object.portal_type in ['File', 'Image', 'Link', 'FSDFacultyStaffDirectoryTool'] or object.portal_type.startswith('Form'):
        text = ''
    elif object.portal_type in ['FSDPerson']:
        text = object.getBiography()
    elif hasattr(object, 'getRawText'):
        text = object.getRawText()
    elif hasattr(object, 'getText'):
        text = object.getText()
    else:
        text = ""
    return text

def scrub(v):
    if hasattr(v, '__call__'):
        return scrub(v())
    if isinstance(v, bool):
        return repr(v)
    if isinstance(v, DateTime):
        try:
            return v.strftime('%Y-%m-%dT%H:%M:%S%Z')
        except ValueError:
            return ''
    if isinstance(v, int):
        return '%d' % v
    if isinstance(v, tuple) or isinstance(v, list):
        return repr(v)
    if not v:
        return ''
    v = " ".join(v.split()).strip()
    v = safe_unicode(v).encode('utf-8')
    return v

app = makerequest(app)

app._p_jar.sync()

site=app['huck']

setSite(site)

from AccessControl.SecurityManagement import newSecurityManager
admin = app.acl_users.getUserById('admin')
admin = admin.__of__(app.acl_users)
newSecurityManager(None, admin) 

portal_catalog = getToolByName(site, "portal_catalog")

#types = sorted(portal_catalog.uniqueValuesFor('portal_type'))

types = ['Document', 'Event', 'File', 'Folder', 'Image', 'Link', 'News Item', ]
types = ['Announcement', 'Center', 'Conference', 'ConferenceStudent', 'Document', 'Equipment', 'Event', 
    'ExternalMeeting', 'FSDPerson', 'Facility', 'File', 'Folder', 'Graduate Program', 'Image', 'Institute',  
    'Link', 'News Item', 'Protocol', 'PublicationSynopsis', 'SymLink', 'TalkEvent', 'TalkEventStudent', 
    'Training', ]

metadata = portal_catalog.schema()

object_data = """
getEmail
imageCaption
contact_name
contact_email
contact_phone

""".strip().split()

object_data_types = """
FSDPerson
""".strip().split()

results = sorted(portal_catalog.searchResults({'portal_type' : types,}), key=lambda x: len(x.getURL()))

import os

output_dir = "/tmp/export_plone"

blob_dir = "%s/blobs" % output_dir

output_tsv = "%s/export.tsv" % output_dir


try:
    os.mkdir(output_dir)
except OSError:
    pass

try:
    os.mkdir(blob_dir)
except OSError:
    pass


output_file = open(output_tsv, "w")
headings = ['URL']
headings.extend(metadata)
headings.extend(object_data)

output_file.write("\t".join(headings))
output_file.write("\n")

for r in results:
    print "Exporting %s" % r.Title
    data = [r.getURL().replace('http://foo/huck', '')]
    for i in metadata:
        v = r.__getattribute__(i)
        v = scrub(v)
        data.append(v)
    o = r.getObject()
    for i in object_data:
        if hasattr(o, i):
            v = getattr(o,i)
            v = scrub(v)
            data.append(v)
        else:
            data.append('')
    output_file.write("\t".join(data))
    output_file.write("\n")
    # Image data for News Items
    if r.portal_type in ['News Item', 'FSDPerson']:
        img_field = o.getField('image').get(o)
        if img_field and img_field.size:
            try:
                img = img_field.data.data
            except AttributeError:
                img = img_field.data
            ext = getExtension(img_field)
            img_file = open("%s/%s.%s" % (blob_dir, r.UID, ext), "wb")
            img_file.write(img)
            img_file.close()
    text = getText(o)
    if text:
        html_file = open("%s/%s.%s" % (blob_dir, r.UID, 'html'), "wb")
        html_file.write(text)
        html_file.close()


output_file.close()
