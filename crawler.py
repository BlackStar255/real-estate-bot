# -*- coding: utf-8 -*-

import requests, time
from bs4 import BeautifulSoup as bs

import settings, db, parser


def __do_fetch(url, funcname):
	# set custom headers here
	headers = {"User-Agent": settings.USERAGENT}

	r = requests.get(url, headers=headers)
	if r.status_code != 200:
		# TODO: we should handle this better
		raise RuntimeError("[-] Failed to fetch url %s, status code: %s"%(url, r.status_code))
	if funcname == "html":
		# be graceful and sleep so we don't get kicked out
		time.sleep(1)
		return bs(r.text)
	else:
		# don't sleep for image fetches, statics can be hammered lightly
		return r

def fetch_page(url):
	'''Fetch url, sleep for a second, then return the beautifulsoup html from url'''
	return __do_fetch(url, "html")

def fetch_image(url):
	'''Fetch url, return the request object as is'''
	return __do_fetch(url, "image")


def fetch_new_ads(oldadids):
	# fetch ad index pages
	adpages = []
	nexturl = settings.FILTERURL
	while nexturl != None:
		print "[+] Fetching", nexturl
		html = fetch_page(settings.BASEURL + nexturl)
		nexturl, adurls = parser.parse_index_page(html)
		adpages.extend(adurls)

	# extract adids and fetch detailed result pages if necessary
	newads, pagecount = {}, 0
	for adid, pageurl in adpages:
		if adid in oldadids:
			print "[+] Skipped page %s"%pageurl
			continue

		detailed = fetch_page(pageurl)
		parsed, imagelist = parser.parse_ad_page(detailed)

		newads[adid] = db.AD(pageurl, adid, imagelist, parsed)
		pagecount += 1
		print "[+] Fetched page ad %s/%s"%(pagecount, len(adpages))

	# download images if necessary
	for ad in newads.values():
		for imgname, imgurl in ad.imagelist:
			imagefilename = settings.IMAGELOCATION + imgname
			try:
				open(imagefilename)
			except IOError as exc:
				if exc.errno != 2:
					raise
				else:
					r = fetch_image(imgurl)
					with open(imagefilename, "wb") as outfile:
						for chunk in r.iter_content(40960):
							outfile.write(chunk)
					print "[+] Saved image %s"%(imgname)
	return newads
