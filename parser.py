# -*- coding: utf-8 -*-

import re

import settings

def parse_index_page(html):
	# get next url
	nexturl = html.find("a", attrs={"class": "button next"})

	# get urls to ads and their ids
	adurls = []
	for adurl in html.find_all("a", title=u"Részletek"):
		adid = int(re.findall("\d{3,}", adurl["href"])[0])
		pageurl = settings.BASEURL + adurl["href"]
		adurls.append((adid, pageurl))

	if nexturl != None:
		nexturl = nexturl["href"]
	return nexturl, adurls


def parse_ad_page(html):
	# TODO Migrate to lxml for XPath

	fieldparser = {
		"title": 	("find", "h1", {"id": "id-holder", "class": "pageTitle"}, "text"),
		"important":	("all",  "h1", {"class": "importantInformation"}, "parent"),
		"details":	("find", "table", {"id": "table"}),
		"subtitle":	("find", "p", {"id": "pageSubTitle"}, "text"),
		"description":	("find", "div", {"id": "commentText"}, "text"),
		"sellername":	("find", "div", {"id": "officeName"}, "text"),
		"sellerphoto":	("find", "a", {"class": "referens photo"}, "img"),
	}

	# extract relevant fields
	parsed, imagelist = {}, []
	for fieldname, fielddesc in fieldparser.iteritems():
		if fielddesc[0] == "find":
			tmp = html.find(fielddesc[1], fielddesc[2])
			if len(fielddesc) > 3 and tmp != None:
				tmp = getattr(tmp, fielddesc[3])
		else:
			tmp = html.find_all(fielddesc[1], fielddesc[2])
			if len(fielddesc) > 3:
				tmp = [getattr(x, fielddesc[3]) for x in tmp]

		if len(fielddesc) > 3 and fielddesc[3] == "text":
			if tmp != None:
				tmp = tmp.strip().replace("\n", " ")

		if fieldname == "important":
			tmp = [unicode(getattr(x, "text")) for x in tmp]
		if fieldname == "details":
			pairs = {}
			for tr in tmp.find_all("tr"):
				odd = [x for x in tr.children][::2]
				even = [x for x in tr.children][1::2]
				for pair in zip(odd, even):
					if pair[0] == "" and pair[1] == "":
						continue
					pairs[pair[0].text] = pair[1].text
			tmp = pairs
		else:
			if fielddesc[0] == "find":
				tmp = unicode(tmp)
			else:
				tmp = [unicode(x) for x in tmp]

#		print "[+] Extracted", fieldname, tmp
		parsed[fieldname] = tmp

	# fetch images
	for tag in html.find_all("div", {"class": "highslide-gallery"}):
		for img in tag.find_all("img"):
			imgname = img["src"].split("/")[-1]
			imagelist.append((imgname, img["src"]))

	return parsed, imagelist
