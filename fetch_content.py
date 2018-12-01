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
    content = {
        'titleHTML': None,
        'sections': [
            {
                'items': [],
            },
        ],
    }
    for n, el in enumerate(article):
        try:
            logger.debug('Processing: %s', smart_repr(element_to_html(el)))
            # process h1
            if n == 0:
                assert el.tag == 'h1'
                content['titleHTML'] = element_contents_as_html(el)
                continue
            assert el.tag != 'h1'
            assert not el.xpath('.//h1')

            # process h2
            if el.tag == 'h2':
                content['sections'].append({
                    'titleHTML': element_contents_as_html(el),
                    'items': [],
                })
                continue
            assert not el.xpath('.//h2')

            content['sections'][-1]['items'].append({
                'html': element_to_html(el),
            })
        except Exception as e:
            raise Exception('Failed to process element {}'.format(el)) from e
    return content


def element_to_html(element):
    return lxml.html.tostring(element, encoding='UTF-8').decode()


def element_contents_as_html(element):
    out = []
    out.append(element.text or '')
    for el in element:
        out.append(element_to_html(el))
    return ''.join(out)


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
