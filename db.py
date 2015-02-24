# -*- coding: utf-8 -*-

import settings
import cPickle


def load():
	try:
		ads = cPickle.load(open(settings.DBLOCATION))
	except IOError as exc:
		if exc.errno != 2:
			raise
		else:
			return None
	return ads

def save(ads):
	cPickle.dump(ads, open(settings.DBLOCATION, "w"))

# "models"
class AD:
	def __init__(self, link, adid, imagelist, parsed):
		self.link = link
		self.adid = adid
		self.imagelist = imagelist
		self.parsed = parsed
		self.copies = []
