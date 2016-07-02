from evernote.api import client
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.constants import NoteSortOrder
from lxml import etree
from lxml.cssselect import CSSSelector
import re
from local_settings import token

from logging_config import getLogger
logger = getLogger(__name__)

BACKLINK_PREFIX = u"[[[Backlink:"
BACKLINK_SUFIX = u"]]]"

client = client.EvernoteClient(token=token, sandbox=False)

store = None
user = None


def get_store():
    global store
    if not store:
        store = client.get_note_store()

    return store


def get_user():
    global user
    if not user:
        user = client.get_user_store().getUser()

    return user


def find_recent_notes_metadata(recent_days=1):
    filter = NoteFilter()
    filter.ascending = False
    filter.order = NoteSortOrder.UPDATED
    filter.words = "updated:day-" + str(recent_days)
    spec = NotesMetadataResultSpec()
    spec.includeTitle = True
    spec.includeUpdated = True

    offset = 0
    pagesize = 50
    while True:
        result = get_store().findNotesMetadata(token, filter, offset, pagesize, spec)
        for metadata in result.notes:
            yield metadata

        if result.totalNotes <= offset:
            break

        offset += pagesize


def note_by_guid(guid):
    return get_store().getNote(token, guid, True, False, False, False);


def find_recent_notes(recent_days=1):
    metas = find_recent_notes_metadata(recent_days).notes
    for meta in metas:
        yield note_by_guid(meta.guid)


def get_link_prefixes():
    shard_id = get_user().shardId
    id = get_user().id

    external = "https://www.evernote.com/shard/{0}/nl/{1}/".format(shard_id, get_user().id)
    internal = "evernote:///view/{1}/{0}/".format(shard_id, get_user().id)

    return (external, internal)


def note_link_elements(note):
    content_tree = etree.fromstring(note.content)
    links = CSSSelector('a')(content_tree)

    prefixes = get_link_prefixes()
    for link in links:
        for prefix in prefixes:
            href = link.get("href")
            if href.startswith(prefix):
                yield link


def note_hrefs(note):
    hrefs = [link.get("href") for link in note_link_elements(note)]
    # set for unique links, list for indexed access
    return list(set(hrefs))


def note_back_hrefs(note):
    for link in note_link_elements(note):
        parent_text = link.getparent().text
        if parent_text and parent_text.startswith(BACKLINK_PREFIX):
            yield link.get("href")


def guid_by_note_href(note_href):
    # Get non-empty link parts (split by "/)
    link_parts = filter(lambda x: x, note_href.split("/"))
    guid = link_parts[-1]
    return guid


def add_backlink(src_note, dst_note):
    external_prefix, internal_prefix = get_link_prefixes()
    url = internal_prefix + "{0}/{0}/".format(dst_note.guid)

    backlink_text = "<span>{0}<a href='{1}' style='color:#69aa35'>{2}</a>{3}</span><br/>"
    backlink = backlink_text.format(BACKLINK_PREFIX, url, dst_note.title, BACKLINK_SUFIX)

    note_regex = re.compile("(<en-note.*?>)")
    src_note.content = note_regex.sub(r'\1' + backlink, src_note.content)
    get_store().updateNote(token, src_note);


def process_notes():
    for note in find_recent_notes():
        hrefs = note_hrefs(note)

        for href in hrefs:
            linked_note = note_by_guid(guid_by_note_href(href))
            backlink_guids = [guid_by_note_href(href) for href in note_back_hrefs(linked_note)]
            if note.guid not in backlink_guids:
                add_backlink(src_note=linked_note, dst_note=note)
