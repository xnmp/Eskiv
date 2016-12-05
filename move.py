import os, subprocess, sys
#sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/home/chong/anaconda2/lib/python2.7/site-packages')
import pyautogui as gui
import gtk.gdk

top_bound, bottom_bound, left_bound, right_bound = 96, 615, 1160, 1737
s_size = (right_bound - left_bound, bottom_bound - top_bound)

def guimove(pos, offset = (0,0)):
	gui.moveTo(pos[0] + left_bound + offset[0], pos[1] + top_bound + offset[1])

def pixel_at(x, y):
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 1, 1)
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap(), x, y, 0, 0, 1, 1)
	return tuple(pixbuf.pixel_array[0, 0])

def move_eskiv_window():
	#start eskiv in the TOP RIGHT CORNER and then run this. 
	#os.system("gnash ~/Downloads/Eskiv.swf")
	#pid = subprocess.Popen(['gnash', "../Downloads/Eskiv.swf"]) 
	#resize window
	gui.moveTo(280,197)
	gui.dragRel(521,450)
	#move window
	gui.moveTo(40,10)
	gui.dragRel(963,0)
	#LEAVE IT NOW

def mouseloc():
	print gui.position()
	print pixel_at(*gui.position())

def findBall(pixels, tolerance = 20):
	# gives the leftmost top pixel of leftmost top new ball
	# TODO: look for a (0,0,255) first
	maxblue = 0
	maxx = 0
	minx = 10000
	for y in range(0, len(pixels)):
		for x in range(130, 150): #range(0, len(pixels[0]), 8):
			col = pixels[y][x]
			if pixels[y][x][0] == 0 and pixels[y][x][2] > 100:
				#print 'found ball with color ', pixels[y][x], 'at', (x,y)
				maxx = max(maxx, x)
				minx = min(minx, x)
				if col[2] > maxblue:
					maxblue = col[2]
					guimove((x, y))
	return maxblue, minx, maxx

def getPixels():
	# gets all pixel data from the game screen
	# the x and y coordinates are reversed in this array
	#t = time.time()
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, s_size[0], s_size[1])
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap()
										, left_bound, top_bound, 0, 0, s_size[0], s_size[1])
	#print "getPixels runtime: ", t - time.time()
	return pixbuf.pixel_array


move_eskiv_window()	
# mouseloc()
# gui.click(1100,300)
# print gui.position()[1] - top_bound, bottom_bound - top_bound
# gui.press('left')
# print findBall(getPixels())