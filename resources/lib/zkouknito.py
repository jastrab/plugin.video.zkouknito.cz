# -*- coding: UTF-8 -*-
#/*
# *      Copyright (C) 2011 Libor Zoubek
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */

import urllib, re, os
import util, resolver
import http.cookiejar
from provider import ContentProvider

def get_url(**kwargs):
		return '{0}?{1}'.format(_url, urlencode(kwargs, 'utf-8'))


class ZkouknitoContentProvider(ContentProvider):

	def __init__(self,username=None,password=None,filter=None):
		ContentProvider.__init__(self,'zkouknito.cz','http://zkouknito.cz/',username,password,filter)
		ck = http.cookiejar.Cookie(version=0, name='confirmed', value='1', port=None, port_specified=False,
										 domain='zkouknito.cz', domain_specified=True, domain_initial_dot=False, 
										 path='/', path_specified=True, secure=False, expires=None, discard=True, 
										 comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
		cj = http.cookiejar.LWPCookieJar()
		cj.set_cookie(ck)
		opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
		urllib.request.install_opener(opener)

	def capabilities(self):
		return ['resolve','categories', 'search']


	def categories(self):
		result = []
		# self.info ('== categories ==')
		# self.info ( self.base_url )
		data = util.substr(util.request(self.base_url+'videa'),'<ul class=\"category','</ul')
	#	util.add_dir('Online TV',{'cat':'http://www.zkouknito.cz/online-tv'})
		pattern='<a href=\"(?P<url>[^\"]+)[^>]+>(?P<cat>[^<]+)</a>'	
		for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
			if m.group('cat').find('18+') > 0:
				continue
			item = self.dir_item()
			item['title'] = m.group('cat')
			item['url'] = m.group('url')
			# self.info (item)
			result.append(item)

		return result

	def search(self, keyword):
			# keyword = get_user_input()
			# return ('what='+urllib.parse.quote(keyword))
			return self.list('https://www.zkouknito.cz/hledej?string=%s'%urllib.parse.quote(keyword))

	def list(self,url):
		result = []
		# self.info ('== list ==')
		# self.info ( url )
		url = self._url(url)
		if '#search#' in url:
			url = search()

		page = util.request(url)
		if '/hledej?string' in url:
			# q = url.find('?')
			# if q > 0:
			# 	url = url[:q]
			data = util.substr(page,'</a> &gt; Vyhledávání</p>','<table class=\"insertedAd\">')
		else:
			data = util.substr(page,'<div id=\"videolist','<div class=\"paging-adfox\">')

		#pattern='<div class=\"img-wrapper\"><a href=\"(?P<url>[^\"]+)\" title=\"(?P<name>[^\"]+)(.+?)<img(.+?)src=\"(?P<img>[^\"]+)(.+?)<p class=\"dsc\">(?P<plot>[^<]+)'
		pattern='<div class=\"img-wrapper\"><a href=\"(?P<url>[^\"]+)\" title=\"(?P<name>[^\"]+)(.+?)<img(.+?)src=\"(?P<img>[^\"]+)(.+?)'
		for m in re.finditer(pattern, data, re.IGNORECASE | re.DOTALL):
			item = self.video_item()
			item['title'] = m.group('name')
			iurl = m.group('url')
			#item['url'] = re.sub('\\\\/', '\\\\', m.group('url'))
			iurl = re.sub('\\\\/', '/', iurl)
			item['url'] = iurl
			item['img'] = m.group('img')
			# self.info ( item )
			#item['plot'] = m.group('plot')
			self._filter(result,item)

		data = util.substr(page,'<div class=\"jumpto\"','</div>')
	
		data = util.substr(page,'<p class=\"paging','</p>')
		# self.info ( data )
		#next = re.search('<a href=\"(?P<url>[^\"]+)\"><img(.+?)next\.png',data,re.IGNORECASE | re.DOTALL)
		next = re.search('<a class=\"next\" href=\"(?P<url>[^\"]+)\">Zobrazit',data,re.IGNORECASE | re.DOTALL)
		# self.info ( next )
		if next:
			item = self.dir_item()
			item['type'] = 'next'
			item['url'] = url+next.group('url')
			result.append(item)

		item = self.dir_item()
		item['title'] = 'Search'
		item['url'] = '#search#'
		item['menu'] = {'$30070':{'list':item['url'], 'action-type':'list'}}
		return result
		
	def resolve(self,item,captcha_cb=None,select_cb=None):
		item = item.copy()
		url = self._url(item['url'])
		# self.info ('resolve == ' + url )
		data = util.request(url)
		resolved = resolver.findstreams(data,["{\"src\":\"(?P<url>[^\"]+).+?poster = \"(?P<poster>[^\"]+).+"])
		result = []
		for i in resolved:
			item = self.video_item()
			item['title'] = i['name']
			iurl = i['url']
			# iurl = re.sub('\\\\/', '\\\\', iurl)
			iurl = re.sub('\\\\/', '/', iurl)
			item['url'] = iurl
			item['quality'] = i['quality']
			item['surl'] = i['surl']
			# self.info ( item )
			result.append(item)     
		if len(result)==1:
			return result[0]
		elif len(result) > 1 and select_cb:
			return select_cb(result)

