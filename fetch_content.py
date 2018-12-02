#!/usr/bin/env python3

import argparse
from io import StringIO
import json
import logging
import lxml.html
from lxml import etree
from pathlib import Path
from reprlib import repr as smart_repr
import re
import requests


content_url = 'https://github.com/messa/what-next/blob/master/README.md'

default_cache_dir = '~/.cache/what-next-web'

slugs_by_title = {
    'Další kurzy': 'dalsi-kurzy',
    'Online kurzy': 'online-kurzy',
    'Univerzitní kurzy, OCW, MOOC': 'univerzitni-kurzy',
    'Úlohy na procvičování': 'ulohy-procvicovani',
    'Summer of code, internshipy': 'internshipy',
    'Co sledovat on-line': 'co-sledovat-online',
    'Kam chodit: meetupy': 'meetupy',
    'Kam zajít: konference': 'konference',
    'Co si přečíst nejdřív': 'co-precist-nejdriv',
    'Knížky': 'knizky',
    'Základní Python knihovny, o kterých je dobré vědět': 'zakladni-python-knihovny',
    'Data science, Machine learning': 'machine-learning',
    'Základní pojmy v IT světě': 'zakladni-pojmy',
    'Kam jít pracovat': 'kam-jit-pracovat',
    'Různé': 'ruzne',
    'TODO': 'todo',
}

logger = logging.getLogger(__name__)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--verbose', '-v', action='store_true')
    args = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    cache_dir = Path(default_cache_dir).expanduser()
    html = fetch_content(content_url, cache_dir)
    content = load_content_from_html(html)
    print(json.dumps(content, indent=2).rstrip())


def fetch_content(url, cache_dir):
    cache_filename = re.sub(r'[^a-zA-Z0-9.]+', '-', url)
    cache_path = cache_dir / cache_filename
    if cache_path.is_file():
        logger.debug('URL %s using cache file %s', url, cache_path)
        return cache_path.read_text()
    r = requests.get(url)
    r.raise_for_status()
    html = r.text
    cache_path.parent.mkdir(exist_ok=True, parents=True)
    cache_path.write_text(html)
    logger.debug('Stored response in cache file %s', cache_path)
    return html


def load_content_from_html(html):
    doc = lxml.html.parse(StringIO(html))
    article, = doc.xpath('.//article')
    remove_anchors(article)
    front_matter = {
        'type': 'FrontMatter',
        'titleHTML': None,
        'items': [],
    }
    sections = []
    for n, el in enumerate(article):
        try:
            logger.debug('Processing: %s', smart_repr(element_to_html(el)))
            # process h1
            if n == 0:
                assert el.tag == 'h1'
                front_matter['titleHTML'] = element_contents_as_html(el)
                continue
            assert el.tag != 'h1'
            assert not el.xpath('.//h1')

            # process h2
            if el.tag == 'h2':
                sections.append({
                    'type': 'Section',
                    'titleHTML': element_contents_as_html(el),
                    'slug': slugify(element_contents_as_text(el)),
                    'items': [],
                })
                continue
            assert not el.xpath('.//h2')

            item = {
                'html': element_to_html(el),
            }
            if sections:
                sections[-1]['items'].append(item)
            else:
                front_matter['items'].append(item)
        except Exception as e:
            raise Exception('Failed to process element {}'.format(el)) from e
    return [front_matter] + sections


def element_to_html(element):
    return lxml.html.tostring(element, encoding='UTF-8').decode()


def element_contents_as_html(element):
    out = []
    out.append(element.text or '')
    for el in element:
        out.append(element_to_html(el))
    return ''.join(out)


def element_contents_as_text(element):
    out = []
    out.append(element.text or '')
    for el in element:
        out.append(element_contents_as_text(el))
        out.append(el.tail)
    return ''.join(out)


def slugify(text):
    return slugs_by_title[text]


def remove_anchors(article):
    for a in article.xpath('//a'):
        if a.attrib.get('class') == 'anchor':
            if len(a) == 1 and a[0].tag == 'svg':
                remove_element(a)


def remove_element(el):
    parent = el.getparent()
    if el.tail.strip():
        prev = el.getprevious()
        if prev:
            prev.tail = (prev.tail or '') + el.tail
        else:
            parent.text = (parent.text or '') + el.tail
    parent.remove(el)


def p(element):
    print(etree.tostring(element, pretty_print=True, encoding='utf-8').decode().rstrip())


if __name__ == '__main__':
    main()
