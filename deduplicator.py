# -*- coding: utf-8 -*-

import scipy as sp
from scipy.misc import imread, imresize
from scipy.signal.signaltools import correlate2d as c2d

# I quite literally have no idea what the math behind this is, except that it involves matrices,
# got it from: https://stackoverflow.com/questions/1819124/image-comparison-algorithm

def get_resized_data(origdata, size):
	'''Resize image data'''
	tmp = imresize(origdata, (size, size), interp="bilinear", mode=None)
	# convert to grey-scale using W3C luminance calc
	lum = [299, 587, 114]
	tmp = sp.inner(tmp, lum) / 1000.0
	# normalize per http://en.wikipedia.org/wiki/Cross-correlation
	return ((tmp - tmp.mean()) / tmp.std())

def read_image(filename):
	'''Read image as Scipy array, RGB (3 layer)'''
	imgdata = imread(filename)
	try:
		len(imgdata[0][0])
	except TypeError as exc:
		# not a list of values
		print "[-] Skipping %s"%filename
		return None
	return imgdata

def compare_images(imgfile1, imgfile2):
	'''Compare the images as per https://stackoverflow.com/questions/1819124/image-comparison-algorithm
	This is really slow, so we start with a tiny size and gradually go larger if we find them to look alike.'''
	size = 5

	origimage1, origimage2 = read_image(imgfile1), read_image(imgfile2)
	if origimage1 == None or origimage2 == None:
		# bad image
		return False, 0, size

	while True:
		data1, data2 = get_resized_data(origimage1, size), get_resized_data(origimage2, size)
		correlation = c2d(data1, data2, mode="same").max()
		if correlation > size**2 * 0.75:
			if size >= 80:
				# seems like a good match
#				print "\tMATCH", size, imgfile1, imgfile2
				return True, correlation, size
			else:
				# refine
#				print "\tPossible correlation!", size, imgfile1, imgfile2
				size *= 2
		else:
			# not a match
			return False, correlation, size
