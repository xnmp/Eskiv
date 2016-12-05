# where to from here:
# posets are all gone, except for THE CONE
# the cone is an associative array where the keys are the pixels and the values are the circle centers
# more precisely, a path of circle centers, since each each pixel in the cone
# remembers its parent (just one possible parent is enough)
# evolving this array is easy, and we evolve it before the balls

# in getpath mode, each time we evolve a ball we check for collision against the cone
# if collision, we remove the value (ie the path)
# then just choose the path that contains the square at the end 

# 3.2 - resized eskiv window to be exactly 4x the natural size
# 3.1 went back to finding the top left pixel instead of the center
# 3.0 redoing this whole thing. first changing update for fsets
# - got rid of evolvepos
# - changed fuzzyballs to just be more balls instead of sets of balls
# - got rid of diam and center

#initialize
import sys
#sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/home/chong/anaconda2/lib/python2.7/site-packages')

import gtk.gdk
import time
import pyautogui as gui
import numpy as np
import numbers
import math
from itertools import product, izip

# bounces 16 from the top
top_bound, bottom_bound, left_bound, right_bound = 96 - 10, 615 + 10, 1160 - 10, 1737 + 10
s_size = (right_bound - left_bound, bottom_bound - top_bound)
gui.PAUSE = 0
# print 's_size', s_size

dt = 0.05
velodict = {(-1,0):'left', (1,0):'right', (0,-1):'up', (0,1):'down', (0,0):'none'}
allvelos = [(x, y) for x in (-1,0,1) for y in (-1,0,1)]

def pause():
	gui.click(1140, 36)
	gui.click(1140, 76)
	gui.click(300, 300)

def play():
	gui.click(1140, 36)
	gui.click(1140, 56)
	gui.click(300, 300)

def guimove(pos, offset = (20,0)):
	gui.moveTo(pos[0] + left_bound + offset[0], pos[1] + top_bound + offset[1])

def tr(msg):
	global loopnum
	print '~LOOP', loopnum, msg, '@:  ', (time.time() - looptime) / dt

def pixel_at(x, y):
	#the player circle is 51,51,51
	#the square is 102,102,102
	#empty space is x,x,x for 102 < x <= 153
	#the balls are 0,0,x for some x
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 1, 1)
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap(), x, y, 0, 0, 1, 1)
	return tuple(pixbuf.pixel_array[0, 0])

class MyException(Exception):
	#misc
    pass

def tadd(a,b):
	# add tuples elementwise
	return tuple(x+y for x,y in izip(a,b))

def tsub(a,b):
	# add tuples elementwise
	return tuple(x-y for x,y in izip(a,b))

def tmul(a,b):
	# add tuples elementwise
	return tuple(x*y for x,y in izip(a,b))

def smul(a,b):
	# add tuples elementwise
	return tuple(x*a for x in b)

def Dist(pos1, pos2, p = 1):
	#print pos1, pos2
	if p ==1:
		#Manhattan distance
		res = max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
	else:
		#Euclidean distance
		res = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
	#print res
	return res

def Poset(pos, radius, p = 2):
	#print pos
	range0 = range(int(pos[0] - radius), int(pos[0] + radius))
	range1 = range(int(pos[1] - radius), int(pos[1] + radius))
	if p == 1:
		return {(x, y) for x, y in product(range0, range1)}
	return {poss for poss in product(range0, range1) if Dist(poss, pos, p) < radius}

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

def findSprite(pixels, color = (51,51,51), tolerance = 20):
	# gives the leftmost top pixel of the circle or square
	#may return a list
	t = time.time()
	for y in range(0, len(pixels), 10):
		for x in range(0, len(pixels[0]), 10):
			if pixels[y][x][0] == color[0]:
				return (x,y)
				#--TODO: find the center of the square, or possible centers
				#not just the topleft-most pixel of it
	#print "findSprite runtime: ", t - time.time()
	return None

def findBall(pixels, excl_poset = set(), gridsize = 10, tolerance = 20):
	# gives the leftmost top pixel of leftmost top new ball
	# TODO: look for a (0,0,244) first
	for y in range(0, len(pixels), gridsize):
		for x in range(0, len(pixels[0]), gridsize):
			if (x,y) in excl_poset:
				continue
			color = pixels[y][x]
			# found a pixel
			if color[0] == 0 and color[2] > 80:
				# print pixels[y+ Ball.radius/2][x]
				# if pixels[y+ Ball.radius][x][0] != 0:
				# 	raise MyException
				return (x,y)
	return None

class Eskiv(object):

	def __init__(self):
		self.pos = None

	def Evolved(self, tau = dt):
		newpos, newvelo = list(self.pos), list(self.velo)
		posdiff = [0,0]
		if tau == None:
			tau = time.time() - self.last_time
		# print 'tau/dt = ', (time.time() - self.last_time)/dt
		for i in range(2):
			newpos[i] = self.pos[i] + int(self.speed * self.velo[i] * tau)
			if newpos[i] <= 0:
				newpos[i] *= -1
				newvelo[i] *= -1
			elif newpos[i] >= s_size[i]:
				newpos[i] = 2 * s_size[i] - newpos[i]
				newvelo[i] *= -1
			posdiff[i] = newpos[i] - self.pos[i]
		self.pos, self.velo = tuple(newpos), tuple(newvelo)
		# update the poset
		self.last_time = time.time()
		# guimove(self.pos)
		self.poset = {tadd(pos, posdiff) for pos in self.poset}
		# print 'evolved distance: ', posdiff[1]
		return self

class Circle(Eskiv):
	speed = 360 # moves exactly 12 pixels at a time
	radius = 16 # this is exact
	color = (51, 51, 51)
	def __init__(self, pos, pos_er = 0):
		self.pos = pos
		self.pos_er = pos_er
		self.poset = Poset(self.pos, self.radius)
		self.velo = (0,0)

class Square(Eskiv):
	radius = 15
	color = (102, 102, 102)
	pshape = 1
	def __init__(self, pos, pos_er = 0):
		self.pos = tadd(pos, (self.radius/2, self.radius/2))
		self.pos_er = pos_er
		self.poset = Poset(self.pos, self.radius, p = 1)

def roundup(x, gridsize = 10):
	return int(math.ceil(x / float(gridsize)) * gridsize)

def rounddown(x, gridsize = 10):
	return int(math.floor(x / float(gridsize)) * gridsize)

def isLegal(pos):
	return 0 <= pos[0] <= s_size[0] and 0 <= pos[1] <= s_size[1]

def LegalList(poslist):
	return [x for x in poslist if isLegal(x)]

def posGen(pos, velo, gridsize = 10):
	if velo[0] > 0:
		print 'case 0+1', 'rounddown from', pos[0], 'to', rounddown(pos[0])
		return [(rounddown(pos[0]) + i * gridsize, pos[1]) for i in [-1,0,1,2]]
	elif velo[0] < 0:
		print 'case 0-1', 'roundup from', pos[0], 'to', roundup(pos[0])
		return [(roundup(pos[0]) - i * gridsize, pos[1]) for i in [-1,0,1,2]]
	elif velo[1] > 0:
		print 'case 1+1', 'rounddown from', pos[1], 'to', rounddown(pos[1])
		return [(pos[0], rounddown(pos[1]) + i * gridsize) for i in [-1,0,1,2]]
	else:
		print 'case 1-1', b'roundup from', pos[1], 'to', roundup(pos[1])
		return [(pos[0], roundup(pos[1]) - i * gridsize) for i in [-1,0,1,2]]

class Ball(Eskiv):
	speed = 240 #in pixels per second
	# moves exactly either 0, 8 or 16 pixels every time
	radius = 11 # this is exact
	color = (0, 0, 237)
	tolerance = 2

	# the pos is the pos of the center in this case
	def __init__(self, pos = None, velo = None, last_time = 0):
		self.last_time = last_time
		self.pos = pos
		self.velo = velo
		self.poset = Poset(self.pos, self.radius)
		# print self.poset
	
	# the following is only for balls in fuzzysets
	# returns true if the ball needs to be deleted
	def Update(self, pixels):
		# remove fuzzy sets
		# print 'fuzzy poset:', self.poset
		# check if the ball has moved zero, 10, or 20 pixels
		tr('begin updating the fset')
		for pos in LegalList(posGen(self.pos, self.velo)):
			# print self.pos, pos
			# tr('posGen done')
			color = pixels[pos[1]][pos[0]][0]
			# tr('got color: ' + str(color))
			if color == 0:
				break
		else:
			pos2 = findBall(getPixels())
			print '~LOOP '+ str(loopnum) + ' removed ball with pos', self.pos, 'and velocity', self.velo
			print 'real pos:                    ', pos2
			return True
		return False

	def Reverse(self):
		return Ball(self.pos, (-self.velo[0], -self.velo[1]))

class FuzzySet(object):
	radius = 10
	tolerance = 2

	# a fuzzy set is just a set of balls which may or may not exist
	def __init__(self, pos = None, balls = None, color = None, last_time = 0):
		tr('commenced fuzzy set creation')
		self.color = color
		self.last_time = last_time
		# set the balls
		# TODO: according to color too
		if balls == None:
			self.balls = {Ball(pos, v, last_time = last_time) for v in [(-1,0),(1,0),(0,-1),(0,1)]}
		else:
			self.balls = balls
		tr('fuzzy set created with pos' + str(pos))
	
	def Update(self, pixels):
		balls = self.balls.copy()
		# remove balls in the fset
		# deletes balls then returns true if the fset needs to be upgraded
		for ball in balls:
			#print ball
			if ball.Update(pixels):
				self.balls.remove(ball)
				if len(self.balls) == 1:
					return True
		return False

	def Evolved(self, tau = dt):
		self.balls = {ball.Evolved() for ball in self.balls}
		return self

	def Reverse(self):
		# reverse for the getpath
		return FuzzySet(balls = {ball.Reverse() for ball in self.balls})

# Classes: EXPLANATION
	# a Ball definitely exists, it has a position and a velocity
	# a FuzzyBall is a ball which may or may not be real
	# - most of the time there will only be one ball whose state is in question, if any
	# - this will be represented by a big set of fuzzyballs
	# a State contains a set of Balls, and a set of FuzzyBalls, 
	# 	together with a Circle and a Square

	'''
	HOW IT WORKS:
	1. All balls except the newest few (up to 3) we already know the position and velocity of. 
	2. Project forward all balls and fuzzy sets
	3. Make the fuzzy sets less fuzzy, perhaps upgrade them to balls
	4. Look for any new unpassable pixels and create more fuzzy sets
	'''

def EvolveCone(poslist, tau = dt, speed = Circle.speed):
	#helper function to getpath
	dist = speed * tau
	#print poslist
	poslistout = set()
	for pos in poslist:
		poslistout |= Poset(pos, dist, 1)
	#circps = [(p[0] + v[0] * , p[1] + v[1] * speed * dt) for p in poslist for v in allvelos]
	return poslistout

class State(object):

	def __init__(self, balls = set(), fsets = set(), circle = None, square = None, newballs = 0):
		self.balls = balls
		self.fsets = fsets
		self.circle = circle
		self.square = square
		self.newballs = newballs #number of balls that need allocating
		self.poset = self.Poset()

	def Update(self, pixels):

		# update the square. 
		if self.square == None:
			tr('looking for square')
			sqpos = findSprite(pixels, Square.color)
			self.square = Square(sqpos)
			tr('found square')

		# update the circle
		if self.circle == None:
			tr('looking for circle')
			cpos = findSprite(pixels, Circle.color)
			self.circle = Circle(cpos)
			tr('found circle')

		# update the fsets
		fsets = self.fsets.copy()
		for fset in fsets:
			if fset.Update(pixels):
				# upgrade to a ball
				for ball in fset.balls:
					self.fsets.remove(fset)
					self.balls.add(ball)
					tr('ball created')

		# now check for unpassable pixels and assign new balls
		# this is the slowest part of the whole thing
		if self.newballs >= 1:
			tr('looking for new pixels')
			newballpos = findBall(pixels, excl_poset = self.poset)
			if newballpos != None:
				tr('found new pixel')
				# TODO: add the color
				self.fsets.add(FuzzySet(pos = newballpos, last_time = time.time()))
				self.newballs -= 1

		return self

	def Evolved(self, tau = dt):
		# go into the future by tau
		# does not happen inplace
		# h = time.time()
		self.balls = {ball.Evolved() for ball in self.balls}
		self.fsets = {fset.Evolved() for fset in self.fsets}
		if self.circle.velo != (0,0):
			self.circle = self.circle.Evolved()
		self.poset = self.Poset()
		# tr('state evolved')
		return self

	def Poset(self):
		# could be slow
		res_poset = set()
		for ball in self.balls:
			res_poset |= ball.poset
		for fset in self.fsets:
			for ball in fset.balls:
				res_poset |= ball.poset
		return res_poset

	def Reverse(self):
		# reverse velocities
		# print 'lll', {fset.Reverse() for fset in self.fsets}
		return State(balls = {ball.Reverse() for ball in self.balls}, 
					fsets = {fset.Reverse() for fset in self.fsets},
					circle = self.circle)

	def getPath(self):
		#1. Navigate until the intersection contains the square
		#2. Navigate backwards in time from the square until the intersection contains the circle
		#	OR navigate one period, then another, 
		#	and keep going unless the two last navigated periods are the same
		#3. Take the intersection of the passable squares at each time step. 
		#	These are the 'safe' squares
		#4. For each time step just pick a move that takes you to a safe square
		
		period = 10
		tr('looking for path')
		#navigate forward in time until a square, saving all the positions in cpos
		newstate = self
		sqposet = self.square.poset
		cposet = self.circle.poset
		
		i = 0
		# navigate forward in time until square
		freeposet = cposet
		print 'SQPOSET:', sqposet
		cposets_f = [cposet]
		while i < period / dt and sqposet & freeposet == set(): 
			newstate = newstate.Evolved()
			freeposet = newstate.Poset() & EvolveCone(cposets_f[-1])
			cposets_f.append(freeposet)
			i += 1

		#navigate backward in time until the circle
		newstate = newstate.Reverse()
		freeposet = sqposet
		cposets_b = [sqposet]
		while cposet & freeposet == set():
			newstate = newstate.Evolved()
			freeposet = newstate.Poset() & EvolveCone(cposets_b[-1])
			cposets_b.append(freeposet & cposets_f.pop())

		#now find the path
		path = []
		#we prefer to move left, and stay still last
		navcircle = self.circle
		while cposets_b != []:
			freeposet = cposets_b.pop()
			for velo in allvelos:
				navcircle.velo = velo
				navcircle = navcircle.Evolved()
				cposet = navcircle.poset
				# here "<="" means subset of
				if cposet <= freeposet:
					path.append(velo)
					break
		tr('path found')
		return path

def countBalls(cpos):
	#returns the number of balls that need to be search for
	timeout = time.time() + dt / 2 #waits half a time step for balls to appear
	numballs = 0
	while time.time() < timeout: #or no more squares
		sqpos = SquarePos(getPixels())
		if sqpos == oldsqpos:
			oldsqpos = sqpos
			numballs += 1
			time.sleep(dt/5)
	return numballs

def PressMove(velo, tau = dt):
	movex = velodict[(velo[0], 0)]
	movey = velodict[(0, velo[1])]
	if movex != 'none':
		gui.keyDown(movex)
	if movey != 'none':
		gui.keyDown(movey)
	time.sleep(tau/2)
	if movex != 'none':
		gui.keyUp(movex)
	if movey != 'none':
		gui.keyUp(movey)
	#update the state
	global state
	state.circle.velo = velo

def checkDead():
	#TODO: just look for the 'GAME OVER' text
	return False

#===================
#==== MAIN LOOP ====
#===================

#main loop
state = State(newballs = 1)
path = []
timeout = time.time() + 40
dt = 0.0333333

lastballpos = 0
loopnum = 1
totdist = 0

count = 0

# gui.click(1100, 300)

while True:

	looptime = time.time()

	# stop if dead
	if checkDead():
		break

	# for now, run for 20 seconds at most
	if time.time() > timeout:
		break

	# update state
	# if state.square == None or state.fsets != set():
	# 	pix = getPixels()
	# 	state = state.Update(pix)


	ballpos = findBall(getPixels(), gridsize = 8)

	# evolve state
	# state = state.Evolved()
	# for ball in state.balls:
	# 	ballpos = findBall(getPixels())
		# print 'expected ball pos: ', ball.pos, 'real ball pos: ', ballpos #ppp
		# print lastballpos - ballpos[1], ball.velo
		# lastballpos = ballpos[1]
		# guimove(ballpos)

	# measure the velocity
	# if loopnum >= 5 and time.time() - looptime < dt:
	# 	count += 1
	# 	totdist += np.absolute(lastballpos - ballpos[1])
	# 	print totdist / float(count), (lastballpos - ballpos[1]), ballpos


	print (lastballpos - ballpos[1]), ballpos
	lastballpos = ballpos[1]

	# get the next moves
	# if path == []:
	# 	#print state.square.pos
	# 	path = state.getPath()
	
	# # reset the path if square is about to be collected
	# elif len(path) == 1:
	# 	state.Square = None

	# # make the move
	# currentvelo = path.pop()
	# PressMove(currentvelo)

	# sleep
	if time.time() - looptime < dt:
		# print 'Sleeping for', dt - time.time() + looptime
		time.sleep(dt -  time.time() + looptime)
	# tr('---#' + str(loopnum) + ' end')

	loopnum += 1

	#break

#TO DO LIST: 
'''
1. hit the square at the optimal time and angle
2. if there is no path due to too many unknown positions and velocities, 
   then stall until positions and velocities can be known
3. failing this, guess some positions and velocities in an optimal way
4. full on Kalman filter for the state
5. take the wildest path for maximum impression
'''