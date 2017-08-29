"""
moar-chives
Copyright (c) iyra 2017
License: CC0 1.0 Universal Public Domain Dedication
https://creativecommons.org/publicdomain/zero/1.0/

moar-chives is a script designed to back up single webpages by simply fetching them and saving them
it also has a functionality for {4,8}chan threads, in which it will save the thread
and any images/files linked (including multiple images/files as on 8chan)

it writes archived files to ./pub/arch and stores lists of them in ./linkroll.md (simple pages)
and/or ./chanroll.md (imageboard threads)

this means you can use it with `perc' (https://github.com/iyra/perc), running from your site directory:
    ../archive.py http://example.com
assuming archive.py is in ~/site and you are in ~/site/example.com

external dependencies: BeautifulSoup (bs4) on Python 3
Future stability is not guaranteed due to "API" changes on imageboard sites, use at your own risk.
"""

import urllib.parse
import urllib.request
import sys
from bs4 import BeautifulSoup
import datetime
import os
import re
from pathlib import Path
# def loveisover_posts(board, thread, fragment):
#     posts = []
#     op_post = soup.find('article', class_='post_is_op')
#     if fragment=='nil':
#         replies = op_post.find('aside', class_='posts')
#     else:
#         if fragment != thread:
#             replies = [op_post.find('aside', class_='posts').find('article', id=fragment)]
#         else:
#             replies = []
#     posts.append({
#         'op': True,
#         'name': op_post.find('header').find('div', class_='post_data').find('span', class_='post_poster_data').get_text(),
#         'date': op_post.find('header').find('div', class_='post_data').find('span', class_='time_wrap').find('time').get_text(),
#         'id': op_post.find('header').find('div', class_='post_data').find('a').get_text(),
#         'message': op_post.find('div', class_='text').get_text(),
#         'files': []})
#     if op_post.find('div', class_='thread_image_box') is not None:
#          posts[0]['files'].append([
#              op_post.find_all('div', class_='thread_image_box', limit=1).find_all('div', class_='post_file', limit=1).find('a', class_='post_file_filename').get('href'),
#              op_post.find_all('div', class_='thread_image_box', limit=1).find_all('div', class_='post_file', limit=1).get_text(),
#              op_post.find_all('div', class_='thread_image_box', limit=1).find_all('a', class_='thread_image_link', limit=1).find('img', class_='thread_image').get('src'),
#              op_post.find_all('div', class_='thread_image_box', limit=1).find_all('div', class_='post_file', limit=1).find('a', class_='post_file_filename').get_text()])
             
#     for reply in replies:
#         d = {}
#         pdata = reply.find('article', class_='post').find('div', class_='post_wrapper').find('header').find('div', class_='post_data')
#         d['subject'] = pdata.find(class_='post_title').get_text()
#         d['op'] = False
#         d['name'] = pdata.find('span', class_='post_poster_data').get_text()
#         d['date'] = pdata.find('span', class_='time_wrap').find('time').get_text()
#         d['id'] = pdata.find('a').get_text()
#         d['message'] = reply.find('article', class_='post').find('div', class_='post_wrapper').find('div', class_='text').get_text()
#         d['files']
#         if reply.find('article', class_='post').find('div', class_='post_wrapper').find('div', class_='post_file') is not None:
#             fileinf = reply.find('article', class_='post').find('div', class_='post_wrapper').find('div', class_='post_file')
#             d['files'].append([
#                 fileinf.find('a', class_='post_file_filename').get('href'),
#                 fileinf.find('span', class_='post_file_metadata').get_text(),
#                 reply.find('article', class_='post').find('div', class_='post_wrapper').find('div', class_='thread_image_box').find('a', class_='thread_image_link').find('img', class_='post_image').get('src'),
#                 fileinf.find('a', class_='post_file_filename').get_text()])
#         posts.append(d)
#     return posts

user_agent = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
def dlfile(fileurl, filepath):
    if not os.path.exists(filepath):
        os.makedirs(filepath)
    if not os.path.exists(filepath+fileurl.split('/')[-1]):
        # don't re-download things already downloaded so we don't get b&
        if fileurl.startswith('//'):
            fileurl = urllib.parse.urlparse(url).scheme+":"+fileurl
        req=urllib.request.Request(fileurl)
        req.add_header('User-Agent', user_agent)
        try:
            with urllib.request.urlopen(req) as response:
                with open(filepath+fileurl.split('/')[-1], 'wb') as f:
                    f.write(response.read())
            print(fileurl.split('/')[-1]+" downloaded to "+filepath)
        except urllib.request.HTTPError as e:
            print(fileurl+": "+str(e.code))
    else:
        print(fileurl.split('/')[-1]+" already exists in "+filepath+", skipping.")

def threadlocation(domain,board,thread,fragpost):
    return "pub/arch/chan-"+"".join([c for c in os.path.splitext(domain)[0] if c.isalpha() or c.isdigit() or c==' ']).rstrip()+"/"+board+"-"+thread+"-"+fragpost+"/"

def writethread(domain, board, thread, threadposts, fragpost, url, title):
    print(str(fragpost))
    tdir = threadlocation(domain,board,thread,fragpost)
    if not os.path.exists(tdir+"thumbs/"):
        os.makedirs(tdir+"thumbs/")
    c = "<!doctype html><head><meta charset='utf-8'><style type=\"text/css\">body { background-color:#ffffee; color:#800000; } .rtd { background-color:#f0e0d6; } .quote { color:#789922; } a { color:#0000ee; } </style><title>"+title+"</title></head><body><h2>ue's archive: /"+board+"/ @ "+domain+" archived thread: \""+title+"\"</h2>"
    for post in threadposts:
        c += "<a id=\"p"+post['id']+"\"></a>"
        #c += "<div class=\"post\">"
        if len(post['flag']) > 0:
            dlfile(urllib.parse.urlsplit(url).scheme+"://"+urllib.parse.urlsplit(url).netloc+post['flag'][0], 'pub/arch/flags/')
        if len(post['files']) > 0:
            for i, postfile in enumerate(post['files']):
                # 4chan at least does a weird thing with the urls where in
                # html they're stored as "//i.4cdn..." which urllib does not like
                dlfile(postfile[0], tdir)
                if postfile[2].startswith('/') and not postfile[2].startswith('//'):
                    # to deal with some thubmbs/flags/whatever on 8chan stored in "/static/x.png" or whatever
                    # complete this relative path to a full url
                    dlfile(urllib.parse.urlsplit(url).scheme+"://"+urllib.parse.urlsplit(url).netloc+postfile[2], tdir+"thumbs/")
                else:
                    dlfile(postfile[2], tdir+"thumbs/")
                #c += postfile[1]+"<a href=\""+postfile[0].split('/')[-1]+"\"><img src=\""+postfile[2].split('/')[-1]+"\"></a>"
        #c += "<p>"+post['message']+"</p></div>"

        if post['op']:
            c += "<div class=\"thre\">"
        else:
            c += """<table border=0>
    <tr>
      <td class=rts>...</td>
      <td class=rtd>"""

        for i, postfile in enumerate(post['files']):
            if len(post['files']) > 1:
                c += "<div class=\"file\" style=\"float:left; max-width:400px; word-break:break-all;\">"
            else:
                c += "<div class=\"file\">"
            c += """Filename: <a href="{fileurl}" target="_blank">{fileorig}</a>-{filesize}<small>Thumbnail</small><br>
    <a href="{fileurl}" target="_blank">
    <img src="{thumburl}" border=0 align=left hspace=20>
  </a></div>""".format(fileurl=postfile[0].split('/')[-1],
                       fileorig=postfile[3],
                       filesize=postfile[1],
                       thumburl="thumbs/"+postfile[2].split('/')[-1])
        if len(post['files']) > 1:
            c += "<div style=\"clear:both;\">"
        flagtext = ""
        if len(post['flag']) > 0:
            flagtext = "<img src=\"/pub/arch/flags/"+post['flag'][0].split('/')[-1]+"\" title=\""+post['flag'][1]+"\">"
        c += """<font color='#cc1105'><b>{subject}</b></font> 
  Name <font color='#117743'><b>{name} </b></font>{flagtext} {date} <a href="#p{postnum}">No.</a>{postnum}
  <blockquote>{message}</blockquote>""".format(subject=post['subject'],
                                               name=post['name'],
                                               flagtext=flagtext,
                                               date=post['date'],
                                               postnum=post['id'],
                                               message=post['message'])

        if not post['op']:
            c += "</td></tr></table>"
    c += "</div>" # close div thre

    c += "<footer><a href=\"/chanroll\">Go to ue's list of backed up threads</a></footer>"
    with open(tdir+"index.html", 'w') as f:
        f.write(c)
    return tdir

if len(sys.argv) < 2:
    print("Must provide at least one URL as argument to bookmark.")
    sys.exit()

urls = sys.argv[1:]
titles = {}
chans = {}
values = {}

for url in urls:
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii')
    req = urllib.request.Request(url)
    req.add_header('User-Agent', user_agent)
    try:
        with urllib.request.urlopen(req) as response:
            p = response.read()
            domain = "{0.netloc}".format(urllib.parse.urlsplit(url))
            #if domain not in ["8ch.net", "boards.4chan.org", "archive.loveisover.me"]:
            if domain not in ["8ch.net", "boards.4chan.org"]:
                soup = BeautifulSoup(p, "html.parser")
                titles[url] = [soup.title.string, p, response.headers.get_content_charset()]
            else:
                target = urllib.parse.urlparse(url)
                board = ''
                thread = ''
                post = 'nil'
                if domain=="boards.4chan.org":
                    path_pat = re.compile('^\/([A-Za-z0-9]+)\/thread\/(\d+)\/?(.+)?')
                    frag = re.compile('^p(\d+)')
                    m = path_pat.match(target.path)
                    if m:
                        board = m.group(1)
                        thread = m.group(2)
                        if len(target.fragment) > 0 and frag.match(target.fragment) and target.fragment != thread:
                            m = frag.match(target.fragment)
                            post = m.group(1)
                    else:
                        print(url+": malformed 4chan thread URL")    
                if domain=="8ch.net":
                    path_pat = re.compile('^\/([A-Za-z0-9]+)\/res/(\d+).html')
                    frag = re.compile('^(\d+)')
                    m = path_pat.match(target.path)
                    if m:
                        board = m.group(1)
                        thread = m.group(2)
                        if len(target.fragment) > 0 and frag.match(target.fragment) and target.fragment != thread:
                            m = frag.match(target.fragment)
                            post = m.group(1)
                    else:
                        print(url+": malformed 8chan thread URL")
                # if domain=="archive.loveisover.me":
                #     path_pat = re.compile('^\/([A-Za-z0-9]+)\/thread/(\d+)\/?')
                #     frag = re.compile('^(\d+)')
                #     m = path_pat.match(target.path)
                #     if m:
                #         board = m.group(1)
                #         thread = m.group(2)
                #         if len(target.fragment) > 0 and frag.match(target.fragment) and target.fragment != thread:
                #             m = frag.match(target.fragment)
                #             post = m.group(1)
                #     else:
                #         print(url+": malformed loveisover thread URL")
                # contents, charset, board, thread, post
                chans[url] = [domain, p, response.headers.get_content_charset(), board, thread, post]
    except urllib.request.HTTPError as e:
        print(url+": "+e)

if len(chans.items()):
    stored_threads = []
    stored_titles = []
    tdirs = []
    if not os.path.exists("pub/chan_threads"):
        open("pub/chan_threads", 'a').close()
    else:
        with open("pub/chan_threads", 'r') as f:
            for line in f:
                stored_threads.append(line[:-1].split('\t')[:-1])
                stored_titles.append(line[:-1].split('\t')[-1])
    for u,info in chans.items():
        info[1] = info[1].decode(info[2])
        soup = BeautifulSoup(info[1], "html.parser")
        threadposts = []
        if [info[0], info[3], info[4], info[5]] not in stored_threads:
            stored_threads.append([info[0], info[3], info[4], info[5]])
            stored_titles.append(soup.title.string.replace('\t', ' ').replace('\n', ' '))
        if info[0]=="boards.4chan.org":
            posts = soup.find_all(class_='post')
            if info[5] != 'nil':
                posts = soup.find_all(id="p"+info[5])
            if not len(posts):
                print(u+": could not find post {} in the thread you specified.".format(info[5]))
            for post in posts:
                d = {}
                d['files'] = []
                d['op'] = False
                if 'op' in post['class']:
                    d['op'] = True
                print(post)
                d['id'] = post.find('span', class_='postNum').find_all('a')
                if d['id']:
                    d['id'] = d['id'][1].get_text()
                d['name'] = post.find(class_='nameBlock').find('span').contents
                if d['name']:
                    d['name'] = d['name'][0]
                d['subject'] = post.find(class_='subject')
                if d['subject'] is not None:
                    print(d['subject'])
                    d['subject'] = d['subject'].get_text()
                else:
                    d['subject'] = ''
                d['message'] = ''
                d['flag'] = ''
                msgobj = post.find(class_='postMessage').contents
                for q in msgobj:
                    d['message'] += str(q)
                d['message'] = d['message'].replace('</br>', '') # have to do this because BS inserts </br> to close <br>s
                d['date'] = post.find(class_='dateTime').contents
                if d['date']:
                    d['date'] = d['date'][0]
                if post.find(class_='file') is not None:
                    pf = post.find(class_='file').find(class_='fileText')
                    pt = post.find(class_='file').find(class_='fileThumb').find('img').get('src')
                    d['files'].append([pf.find('a').get('href'), pf.contents[2], pt, pf.find('a').get_text()]) # [file url, file size/dims, thumbnail, original name]
                if d['name'] is None or d['message'] is None or d['date'] is None or d['id'] is None:
                    print(u+": Could not parse id, name, message and date required from HTML")
                else:
                    threadposts.append(d)
        if info[0]=="8ch.net":
            #print(soup.find_all(class_='post'))
            posts = soup.find_all(class_='post')
            if info[5] != 'nil':
                if info[5] == info[4]:
                    # we only want to archive the op post
                    posts = soup.find_all(id="op_"+info[5])
                else:
                    posts = soup.find_all(id="reply_"+info[5])
            if not len(posts):
                print(u+": could not find post {} in the thread you specified.".format(info[5]))
            for post in posts:
                d = {}
                d['files'] = []
                d['op'] = False
                if 'op' in post['class']:
                    d['op'] = True
                    
                d['id'] = post.find(class_='intro').find('a').get('id')
                d['name'] = post.find(class_='intro').find('label').find(class_='name').get_text()
                d['subject'] = ''
                if post.find(class_='intro').find('label').find(class_='subject') is not None:
                    d['subject'] = post.find(class_='intro').find('label').find(class_='subject').get_text()
                d['date'] = post.find(class_='intro').find('label').find('time').get_text()
                #print(d['date'])
                d['message'] = str(post.find(class_='body'))
                #<a href="/leftypol/res/1925360.html#1925373" onclick="highlightReply('1925373', event);">&gt;&gt;1925373</a>
                d['message'] = re.sub(r'<a href="\/[A-Za-z0-9]+\/res/\d+\.html#\d+" onclick="highlightReply.+">&gt;&gt;(\d+)</a>', r'<a href="#p\1">&gt;&gt;\1</a>', d['message'])
                d['flag'] = []
                if post.find(class_='intro').find('label').find('img') is not None:
                    d['flag'] = [post.find(class_='intro').find('label').find('img').get('src'), post.find(class_='intro').find('label').find('img').get('title')]
                d['message']
                if post.find(class_='files') is not None:
                    filelist = post.find(class_='files').find_all('div', class_='file')
                    for fitem in filelist:
                        print(fitem)
                        print(fitem.find(class_='fileinfo'))
                        print(fitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename'))
                        tt = fitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename').get_text()
                        if fitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename').get('title') is not None:
                            tt = fitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename').get('title')
                        d['files'].append([
                            fitem.find(class_='fileinfo').find('a').get('href'),
                            fitem.find(class_='fileinfo').find(class_='unimportant').get_text(),
                            fitem.find(class_='post-image').get('src'), # 8chan puts the post-image attribute on the thumbnail image for some reason
                            tt])
                threadposts.append(d)
            for gitem in soup.find(class_='thread').find(class_='files').find_all('div', class_='file'):
                tt = gitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename').get_text()
                if gitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename').get('title') is not None:
                    tt = gitem.find(class_='fileinfo').find(class_='unimportant').find(class_='postfilename').get('title')
                threadposts[0]['files'].append([
                    gitem.find(class_='fileinfo').find('a').get('href'),
                    gitem.find(class_='fileinfo').find(class_='unimportant').get_text(),
                    gitem.find(class_='post-image').get('src'), # 8chan puts the post-image attribute on the thumbnail image for some reason
                    tt])
        if info[0] == "archive.loveisover.me":
            threadposts = loveisover_posts(info[3], info[4], info[5])
        # threadposts contains all the posts in the thread now
        print(str(threadposts))
        writethread(info[0], info[3], info[4], threadposts, info[5], u, soup.title.string)
    with open("pub/chan_threads", 'w') as f:
        for i,st in enumerate(stored_threads):
            f.write('\t'.join(st)+"\t"+stored_titles[i]+"\n")
    with open("chanroll.md", 'w') as f:
        f.write("Chanroll\n# Chanroll\nA list of selected threads from 4chan and 8chan I have chosen to archive for posterity. All post files are included.\n\n")
        for i,st in enumerate(stored_threads):
            f.write("* <a href=\"{}index.html\">{} backup</a> ({})\n".format(threadlocation(st[0],st[1],st[2],st[3]), stored_titles[i], datetime.datetime.now().strftime("%Y-%m-%d")))

with open("linkroll.md", 'a') as f:
    for key, value in titles.items():
        bakloc = "pub/arch/"+ datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")+"".join([c for c in os.path.splitext(key)[0] if c.isalpha() or c.isdigit() or c==' ']).rstrip()+".html"
        f.write("* <a href=\"{}\">{}</a> ({}, {}, <a href=\"/{}\">backup</a>)\n".format(key, value[0], "{0.netloc}".format(urllib.parse.urlsplit(key)), datetime.datetime.now().strftime("%Y-%m-%d"), bakloc))
        if not os.path.exists("pub/arch"):
            os.makedirs("pub/arch")
        with open(bakloc, 'w') as g:
            g.write(value[1].decode(value[2]))
