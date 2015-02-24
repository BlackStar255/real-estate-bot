#!/usr/bin/python
# -*- coding: utf-8 -*-

import smtplib, random
from email.mime.text import MIMEText

import settings, db, crawler, deduplicator

# TODO file locking should be implemented, so that calling this from cron is safe

def send_mail(mailto, mailfrom, subject, data):
	for addr in mailto:
		msg = MIMEText(data)
		msg["Subject"] = subject
		msg["From"] = mailfrom
		msg["To"] = addr
		s = smtplib.SMTP("localhost", 25)
		s.sendmail(mailfrom, addr, msg.as_string())
		s.quit()

def find_duplicates(newads, ads):
	'''Prepare images for comparison, check which ones need to be compared'''
	def removestreetnum(ad):
		# title is actually the street address
		addr = ad.parsed["title"].split(" ")
		try:
			int(addr[-1]) # if it's a number
		except ValueError as exc:
			pass
		else:
			addr = addr[:-1]
		return " ".join(addr)


	images = []
	for ad in newads.values() + ads.values():
		for imgname, imgurl in ad.imagelist:
			images.append((ad, settings.IMAGELOCATION + imgname))

	# create index of ads that are in the same street
	print "[+] Found %s images"%(len(images))
	collection = images
	indexes = []
	for i in xrange(0, len(collection)):
		ad1 = collection[i][0]

		addr1 = removestreetnum(ad1)

		for j in xrange(i+1, len(collection)):
			ad2 = collection[j][0]

			if ad1 == ad2:
				continue
			if ad1.adid in ad2.copies or ad2.adid in ad1.copies:
				continue
			if ads.get(ad1.adid) != None and ads.get(ad2.adid) != None:
				# if both are old, that means they've been compared before
				continue

			addr2 = removestreetnum(ad2)

			if addr1 == addr2:
				indexes.append((i,j))

	# compare images to each other
	print "[+] Found %s indexes"%(len(indexes))
	random.shuffle(indexes)
	counter = 0
	matchedads = set()
	for i,j in indexes:
		ad1, ad2 = collection[i][0], collection[j][0]
		imgfilename1, imgfilename2 = collection[i][1], collection[j][1]
		match, correlation, size = deduplicator.compare_images(imgfilename1, imgfilename2)
		if match:
			ad1.copies.append(ad2.adid)
			ad2.copies.append(ad1.adid)
			print "[+] Duplicate detected:", settings.BASEURL + ad1.link, settings.BASEURL + ad2.link
		if counter % 1000 == 0:
			print "Progress: %.2f%%"%(float(counter)/len(indexes)*100)
		counter += 1

def main():
	ads = db.load()
	if ads == None:
		ads = {}

	oldadids = set(ads.keys())
	newads = crawler.fetch_new_ads(oldadids)
	print "[+] Found", len(newads), "new ads"

	# this fills ad.copies for all newads
	find_duplicates(newads, ads)

	for ad in newads.values():
		if ads.get(ad.adid) != None:
			# make sure we're not accidentally overwriting an old ad
			print "[-] AD %s is already in the DB!"%(ad.adid)
			continue

		ads[ad.adid] = ad
		if len(ad.copies) > 0:
			print "[+] Ad copy found!", ad.adid, settings.BASEURL + ad.link, ad.copies
		else:
			print "[+] NEW AD!", ad.adid, ad.link, ad.copies
			body = "%s %s\n"%(ad.adid, ad.link)
			send_mail([settings.EMAILADDRESS], "root@localhost", "New real-estate", body)
	print "Total ads in DB:", len(ads)

	db.save(ads)

if __name__ == "__main__":
	main()
