#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
import re
import requests
import stat
import sys
import time

def mkdir(path, mode=stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH):

    if not os.path.exists(path):
        os.makedirs(path)

    chmod(path, mode)

def chmod(path, mode=stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IWOTH|stat.S_IXOTH):
    if not os.path.exists(path):
        return

    try:
        os.chmod(path, mode)
    except PermissionError as e:
        print(e)

def getMatches(content, pattern):

    matches = re.findall(pattern, content)

    if matches is None or 0 == len(matches):
        return None

    return matches

def get(url, **kwargs):

    retries = 3
    timeout = 3

    for i in range(retries):
        try:
            return requests.get(url, timeout=timeout, **kwargs)
        except Exception as e:
            print('Error to get', url, ':', e)

        if i > 0:
            # Sleep a while
            time.sleep(1)

    return None

def saveResource(url, pathname):

    userAgent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:71.0) Gecko/20100101 Firefox/71.0'

    # Headers
    headers = {'User-Agent': userAgent}

    print('Try to download', url, 'to', pathname)

    r = get(url, headers=headers)

    if r is None:
        print('Error to get:', url)
        return False

    if 200 is not r.status_code:
        print('Error status: (', r.status_code, '):\n', r.text)
        return False

    dirpath = os.path.dirname(pathname) 

    mkdir(dirpath)

    with open(pathname, 'wb') as fp:
        fp.write(r.content)

    chmod(pathname)

    print('Downloaded ' + pathname)

    return True

def download(url, basedir):

    pt = '/nutrish/'

    pos = url.find(pt)

    if pos > 0:
        pos += len(pt)
    else:
        pos = url.find('/')
        pos += 1

    filename = url[pos:]

    pos = filename.rfind('/')

    if pos < 0:
        return None, None

    pos = filename.find('.', pos)

    if pos < 0:
        return None, None

    suffix = filename[pos+1:]

    if suffix not in ['png', 'gif', 'jpg', 'jpeg']:
        return None, None

    resdir = os.path.join(basedir, suffix)

    respath = os.path.join(resdir, filename)

    url = 'https://{}'.format(url)

    if os.path.exists(respath):
        return url, respath

    saved = saveResource(url, respath)

    if not saved:
        return None, None

    return url, respath

def getPathPrefix(pathname, basedir):

    curdir = os.path.dirname(pathname)
    curdir = curdir[len(basedir):]

    prefix = ''
    pos = 0

    while pos >= 0:

        pos = curdir.find('/', pos)

        if pos >= 0:
            prefix += '../'
            pos += 1

    return prefix

def findAndReplace(pathname, basedir):

    print('------------------------------------------------------\n', pathname)

    pathname = os.path.realpath(pathname)

    with open(pathname) as fp:
        content = fp.read()

    allurls = list()

    pattern = r'[\'"\(][ \t]*https://([^ \t]+?)[ \t]*[\'"\)]'
    urls = getMatches(content, pattern)

    if urls is not None:
        allurls.extend(urls)

    if len(allurls) is 0:
        return;

    pathPrefix = getPathPrefix(pathname, basedir)

    urls = sorted(set(allurls)) # Unique

    print(str(len(urls)) + ' are found.')

    for url in urls:

        url, respath = download(url, basedir)

        if url is not None:
            respath = '{}{}'.format(pathPrefix, respath[len(basedir)+1:])
            content = content.replace(url, respath)

    # Replace httrack strings
    content = re.sub(r'>( )*<', r'>\n<', content)
    content = re.sub(r'<!-- Mirrored from (.*)-->', '', content)
    content = re.sub(r'<!-- [/]*Added by HTTrack -->', '', content)

    with open(pathname, 'w+') as fp:
        fp.write(content)

def run(basedir):

    basedir = os.path.realpath(basedir)

    for root, d_names, filenames in os.walk(basedir):
        for filename in filenames:
            if filename.endswith('.html'):
                pathname = os.path.join(root, filename)
                findAndReplace(pathname, basedir)

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print('Usage:\n\t', sys.argv[0], 'base-dir\n')
        exit()

    run(sys.argv[1])
