import json
import os
from datetime import datetime
import time

import sys

import pync
from evernote.api import client
from evernote.edam.notestore.ttypes import NoteFilter, NotesMetadataResultSpec
from evernote.edam.type.constants import NoteSortOrder
from lxml import etree
from lxml.cssselect import CSSSelector
import re
from local_settings import token

from logging_config import getLogger
from colorclass import Color

logger = getLogger(__name__)

INTERNAL_LINK_PREFIX = "evernote:///view/"
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


def note_by_guid(guid):
    logger.debug("function starting - note_by_guid: %s", guid)
    note = get_store().getNote(token, guid, True, False, False, False);
    logger.debug("found note title: %s", note.title)
    return note


def find_recent_notes(recent_days=1):
    logger.info("function starting - find_recent_notes: %d", recent_days)
    filter = NoteFilter()
    filter.ascending = True
    filter.order = NoteSortOrder.UPDATED
    filter.words = "updated:day-" + str(recent_days)
    spec = NotesMetadataResultSpec()
    spec.includeTitle = True
    spec.includeUpdated = True

    offset = 0
    pagesize = 50
    while True:
        logger.info("fetching, offset: %d", offset)
        result = get_store().findNotesMetadata(token, filter, offset, pagesize, spec)
        logger.info("fetched %d out of %d notes", len(result.notes), result.totalNotes)
        for metadata in result.notes:
            yield note_by_guid(metadata.guid)

        offset += pagesize

        if result.totalNotes <= offset:
            break

def get_link_prefixes():
    logger.debug("function starting - get_link_prefixes")

    shard_id = get_user().shardId
    id = get_user().id

    external = "https://www.evernote.com/shard/{0}/nl/{1}/".format(shard_id, id)
    logger.debug("external prefix: %s", external)

    return [external, INTERNAL_LINK_PREFIX]


def note_link_elements(note):
    logger.debug("function starting - note_link_elements: %s", note.title)

    parser = etree.XMLParser(remove_blank_text=True, resolve_entities=False)
    content_tree = etree.fromstring(note.content, parser)
    links = CSSSelector('a')(content_tree)

    prefixes = get_link_prefixes()
    for link in links:
        logger.debug("checking href: %s", etree.tostring(link))
        for prefix in prefixes:
            href = link.get("href")
            if href and href.startswith(prefix):
                yield link


def is_backlink(link_element):
    logger.debug("function starting - is_backlink: %s", etree.tostring(link_element))
    parent_text = link_element.getparent().text
    logger.debug("parent element: %s", parent_text)
    is_backlink_result = bool(parent_text) and parent_text.startswith(BACKLINK_PREFIX)
    logger.debug("result: %s", is_backlink_result)

    return is_backlink_result


def note_hrefs(note):
    logger.debug("function starting - note_hrefs: %s", note.title)

    hrefs = [link.get("href") for link in note_link_elements(note) if is_backlink(link) == False]
    # set for unique links, list for indexed access
    unique_hrefs = list(set(hrefs))
    logger.debug("found hrefs: %s", unique_hrefs)

    return unique_hrefs


def note_back_hrefs(note):
    logger.debug("function starting - note_back_hrefs: %s", note.title)

    for link in note_link_elements(note):
        if is_backlink(link):
            href = link.get("href")
            logger.debug("found backlink: %s", href)
            yield href


def guid_by_note_href(note_href):
    logger.debug("function starting - guid_by_note_href: %s", note_href)

    # Get non-empty link parts (split by "/)
    link_parts = filter(lambda x: x, note_href.split("/"))
    guid = link_parts[-1]
    logger.debug("found guid: %s", guid)
    return guid


def add_backlink(src_note, dst_note):
    logger.debug("function starting - add_backlink")
    logger.info("adding backlink '%s' -> '%s'", src_note.title, dst_note.title)

    url = INTERNAL_LINK_PREFIX + "{1}/{0}/{2}/{2}/".format(get_user().shardId, get_user().id, dst_note.guid)

    backlink_text = "<span>{0} <a href='{1}' style='color:#69aa35'>{2}</a>{3}</span><br/>"
    backlink = backlink_text.format(BACKLINK_PREFIX, url, dst_note.title, BACKLINK_SUFIX)

    note_regex = re.compile("(<en-note.*?>)")
    src_note.content = note_regex.sub(r'\1' + backlink, src_note.content)
    get_store().updateNote(token, src_note);
    logger.info("note updated")


def write_last_processed_updated(note):
    logger.debug("function starting - write_last_processed_updated")

    note_updated = note.updated / 1000
    days_since_timestamp(note_updated)

    script_dir = os.path.dirname(os.path.realpath(__file__))
    with file(os.path.join(script_dir, "last_run_date.txt"), mode='w') as f:
        data = {"last_note_updated": note_updated}
        logger.debug("writing to file: %s", data)
        f.write(json.dumps(data))


def days_since_timestamp(timestamp):
    updated_date = datetime.fromtimestamp(timestamp)
    updated_time_delta = datetime.now() - updated_date
    logger.debug("days since processed note: %d", updated_time_delta.days)

    return updated_time_delta.days


def read_last_processed_updated():
    logger.debug("function starting - read_last_processed_updated")

    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, "last_run_date.txt")
    if os.path.exists(file_path):
        with file(file_path) as f:
            data = json.loads(f.read())
            logger.debug("read data: %s", data)

            value = data["last_note_updated"]
            logger.debug("found updated value: %s", value)
            return value
    else:
        logger.info("last-processed file does't exist")
        return None


def process_notes():
    try:
        logger.debug("function starting - process_notes")

        days_since = 100
        last_processed_updated = read_last_processed_updated()
        if last_processed_updated:
            days_since = days_since_timestamp(last_processed_updated)

        for note in find_recent_notes(days_since):
            try:
                logger.info(Color('{green}processing note: %s{/green}'), note.title)
                hrefs = note_hrefs(note)
                logger.info("found %s link to notes", len(hrefs))
                for href in hrefs:
                    linked_note = note_by_guid(guid_by_note_href(href))
                    try:
                        logger.info("linked note: " + linked_note.title)
                        backlink_guids = [guid_by_note_href(href) for href in note_back_hrefs(linked_note)]
                        if note.guid not in backlink_guids:
                            logger.info("backlink not found")
                            add_backlink(src_note=linked_note, dst_note=note)
                        else:
                            logger.info("backlink found")

                        write_last_processed_updated(note)
                    except Exception as e:
                        logger.exception("processing note failed: " + linked_note.title)
                        pync.Notifier.notify('Failed to process note {}: {}'.format(linked_note.title, str(e)), title='Evernote-Backlinker')
            except Exception as e:
                logger.exception("processing note failed: " + note.title)
                pync.Notifier.notify('Failed to process note and all the notes that link to it {}: {}'.format(note.title, str(e)), title='Evernote-Backlinker')

    except Exception as e:
        logger.exception("processing failed")
        pync.Notifier.notify('Failed: {}'.format(str(e)), title='Evernote-Backlinker')
        # notifier didn't work from launchd without sleep for some reason :|
        # http://stackoverflow.com/questions/37010132/launchd-python-notifier-notify-not-producing-expected-output
        time.sleep(1)
        sys.exit(1)

if __name__ == "__main__":
    process_notes()
