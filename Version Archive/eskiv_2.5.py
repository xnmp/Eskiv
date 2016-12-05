# 2.5 got rid of Contains function and Eskiv class
# 2.4: got rid of miniballs, navigate function and intersect function, convrawpixels, collectsquare
# modified poslistout
# 2.3: added separate velocities for every fuzzyball

#initialize
import sys
#sys.path.append('/usr/lib/python2.7/dist-packages/')
sys.path.append('/home/chong/anaconda2/lib/python2.7/site-packages')

import gtk.gdk
import time
import subprocess
import os
import pyautogui as gui
import numpy as np

#corners are (1196,227) , (1197,830) , (1867,228) , (1867,830)
top_bound = 227
bottom_bound = 830
left_bound = 1196
right_bound = 1867
s_size = (right_bound - left_bound, bottom_bound - top_bound)

dt = 0.1
timeout = time.time() + 5
velodict = {(-1,0):'left', (1,0):'right', (0,-1):'up', (0,1):'down', (0,0):'none'}
allvelos = [(x, y) for x in (-1,0,1) for y in (-1,0,1)]

def pixel_at(x, y):
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 1, 1)
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap(), x, y, 0, 0, 1, 1)
	return tuple(pixbuf.pixel_array[0, 0])

class MyException(Exception):
    pass

def Poset(pos, radius, p = 2):
	#print pos
	range0 = range(int(pos[0] - radius), int(pos[0] + radius))
	range1 = range(int(pos[1] - radius), int(pos[1] + radius))
	return {poss for poss in zip(range0, range1) if Dist(poss, pos, p) < radius}

def EvolveCone(poslist, tau = dt, speed = 0.1):
	dist = speed * tau
	#print poslist
	poslistout = set()
	for pos in poslist:
		poslistout |= Poset(pos, dist, 1)
	#circps = [(p[0] + v[0] * , p[1] + v[1] * speed * dt) for p in poslist for v in allvelos]
	return poslistout

def EvolvePos(pos, velo):
	#helper function to Evolve
	#this is ok because tuples are immutable
	pos2 = list(pos)
	velo2 = list(velo)
	for i in range(2):
		pos2[i] = pos[i] + self.speed * self.velo[i]
		if pos2[i] <= 0:
			pos2[i] *= -1
			velo2[i] *= -1
		elif pos2[i] >= s_size[i]:
			pos2[i] = 2 * s_size[i] - pos2[i]
			velo2[i] *= -1
	return tuple(pos2), tuple(velo2)

class FuzzyBall(object):
	#TODO: a fuzzyball is four balls, one for each corner. 
	# instead of balls disappearing, the balls move
	speed = 0.1
	radius = 10
	tolerance = 2
	# a fuzzyball has a set of positions instead of one position
	# the set of the possible centers, not of the unpassable pixels
	def __init__(self, pos = None, poset = set(), balls = set(), velo = None, color = None):
		self.color = color
		# set the poset
		if pos != None and color != None:
			pos_er = self.radius * (1 - self.color / 255)
			self.poset = Poset(pos, pos_er)
		else:
			self.poset = poset

		#set the balls
		if balls != set():
			self.balls = balls
		else:
			if velo == None:
				self.balls = {Ball(pos, v) for pos in self.poset for v in [(-1,0),(1,0),(0,-1),(0,1)]}
			else:
				self.balls = {Ball(pos, velo) for pos in self.poset}
			
	def Update(self, pixels):
		for pos in self.poset:
			color = pixels[pos[0]][pos[1]]
			if color[2] != 0 and color[0] == 0:
				#if the pos is blank, remove it from the fuzzy set
				self.poset.remove(pos)
		if self.diam() <= self.radius:
			#upgrade the fball to a ball
			global state
			state.balls.add(Ball(pos = self.center(), velo = self.balls[0].velo))
			state.fballs.remove(self)

	def Evolved(self, tau = dt):
		# TODO: the poset actually gets smaller temporarily when it bounces
		self.balls = {ball.Evolved() for ball in self.balls}

	def Poset(self):
		#this might end up being too slow
		#TODO: make this more efficient
		poset = set()
		for ball in self.balls:
			poset |= ball.Poset()
		return poset

	def Reverse(self):
		#reverse for the getpath
		return FuzzyBall({ball.Reverse() for ball in self.balls})

	def diam(self):
		#diameter of the fuzzyball, helper function to convert fuzzyballs to balls
		#print self.Poset()
		try:
			xlow = min([pos[0] for pos in self.Poset()])
		except ValueError:
			print self.Poset(), 'ERROR'
		xhigh = max([pos[0] for pos in self.Poset()])
		ylow = min([pos[1] for pos in self.Poset()])
		yhigh = max([pos[1] for pos in self.Poset()])
		#print xhigh, xlow
		return max([xhigh - xlow, yhigh - ylow])

	def center(self):
		#center of the fuzzyball
		xlow = min([pos[0] for pos in self.Poset()])
		xhigh = max([pos[0] for pos in self.Poset()])
		ylow = min([pos[1] for pos in self.Poset()])
		yhigh = max([pos[1] for pos in self.Poset()])
		return ((xlow + xhigh) / 2, (ylow + yhigh) / 2)

class Ball(object):
	speed = 0.1
	radius = 10
	tolerance = 2
	#the pos is the pos of the center in this case
	def __init__(self, pos = None, velo = None):
		self.pos = pos
		self.velo = velo

	def Evolved(self, tau = dt):
		gui.moveTo(*self.pos)
		print 'llll'
		return Ball(*EvolvePos(self.pos, self.velo))

	def Reverse(self):
		return Ball(self.pos, (-self.velo[0], -self.velo[1]))

	def Poset(self):
		return Poset(self.pos, self.radius)

class Circle(object):
	speed = 0.12
	radius = 15
	color = (51, 51, 51)
	def __init__(self, pos, pos_er = 0):
		self.pos = pos
		self.pos_er = pos_er
	def Poset(self):
		#print self.pos
		return Poset(self.pos, self.radius)
	def Moved(self, velo, tau = dt):
		cpos = (self.pos[0] * velo[0] * self.speed * tau, 
					self.pos[1] * velo[1] * self.speed * tau)
		return Circle(cpos)

class Square(object):
	radius = 15
	color = (102, 102, 102)
	def __init__(self, pos, pos_er = 0):
		self.pos = pos
		self.pos_er = pos_er
	def Poset(self):
		return Poset(self.pos, self.radius, p = 1)

#Classes: EXPLANATION
	# a Ball is a position and a velocity
	# a FuzzyBall is a set of balls
	# a State contains a set of Balls, and a set of FuzzyBalls, together with a Circle and a Square

	'''
	HOW IT WORKS:
	1. We know how many balls there are.
	2. All balls except the newest few (up to 3) we already know the position and velocity of. 
	3. Project forward based on the known balls,
	4. The filled-in pixels that aren't expected to be filled-in: ,
		we first assign to the positions of the balls,
		the velocity can be any of the 4,
	5. Next frame: w,e 'hypothesize' that 4 points will be filled-in
		if a pixel that we hypothesized to be filled isn't filled, 
		then can delete the position and velocity tied to that pixel
	'''
	# second method is to have fballs and qballs, where qballs have four velocities
	# and they turn into fballs when we figure out their velocity

class State(object):

	def __init__(self, balls = set(), fballs = set(), circle = None, square = None, newballs = 0):
		self.balls = balls
		self.fballs = fballs
		self.circle = circle
		self.square = square
		self.newballs = newballs #number of balls that need allocating

	def Update(self, pixels):
		#infer the velocities

		#the player circle is 51,51,51
		#the square is 102,102,102
		#empty space is x,x,x for 102 < x <= 153
		#the balls are 0,0,x for some x
		
		#TODO: update all fballs before checking for unpassable pixels
		# 1: update all fballs
		# self.fballs = {fball.Update(pixels) for fball in self.fballs}:
		# 2. look for unpassable pixels and assign new balls

		# update the square. Note: the circle is updated through PressMove
		if self.square == None:
			sqpos = findSprite(pixels, Square.color)
			print sqpos
			#sqpos = (500,500)
			self.square = Square(sqpos)
		if self.circle == None:
			cpos = findSprite(pixels, Circle.color)
			print cpos
			#cpos = (5,5)
			self.circle = Circle(cpos)

		for x, y in zip(range(s_size[0]), range(s_size[1])):
			color = pixels[y][x]
			
			# the pixel is either
			#	- passable and in the error radius of a fuzzyball -> update the fuzzyball
			#	- unpassable and outside all error radii -> assign a new ball

			# 1. if the pixel is unpassable, check if it's a new ball
			# TODO: don't need to bother if newballs == 0, but do it anyway for now
			if color[0] == 0 and color[2] > 0: 

				expected = False

				#check if the pixel lies within the domain of a ball
				for ball in self.balls:
					dist = Dist((x,y), ball.pos, p = 2)
					if dist < ball.radius:
						#go to the next pixel
						expected = True
						#TODO: update the known balls too base on color
						break
				
				if expected == False:
					# if the pixel is outside all known balls, check the fballs
					for fball in self.fballs:
						if (x,y) in fball.Poset():
							#update the poset based on the color
							#TODO: SOMETHING ABOUT COLOR HERE
							expected = True
							break

					# if the pixel is also outside all fballs, initialize an fball
					if expected == False:
						#here if newballs < 0 then something went wrong
						if self.newballs == 0:
							raise MyException('No new balls')
						#add fuzzy ball with four velocities
						self.fballs.add(FuzzyBall(pos = (x,y), color = color[2]))
						self.newballs -= 1

			# 2. if the pixel is passable, update fballs
			else:
				# check if the pixel lies within the domain of a known fball
				# usually there's at most 1 fball so relax
				fballs = self.fballs.copy()
				for fball in fballs:
					balls = fball.balls.copy()
					for ball in balls:
						if (x,y) in ball.Poset():
							fball.balls.remove(ball)
					
					# fball reaches ball status
					# this is really slow
					if fball.balls == set() or fball.diam() <= fball.radius + fball.tolerance:
						self.balls.add(Ball(pos = fball.center(), velo = fball.balls[0].velo))
						self.fballs.remove(fball)
						#TODO: remove the brothers too
				self.fballs = fballs
		return self

	def Evolved(self, tau = dt):
		#go into the future by tau
		#does not happen inplace
		self.balls = {ball.Evolved() for ball in self.balls}
		self.fballs = {fball.Evolved() for fball in self.fballs}
		return self

	def Poset(self):
		#could be slow
		poset = set()
		for ball in self.balls:
			poset |= ball.Poset()
		for fball in self.fballs:
			poset |= fball.Poset()
		return poset

	def Reverse(self):
		#reverse velocities
		return State(balls = {ball.Reverse() for ball in self.balls}, 
					fballs = {fballs.Reverse() for fball in self.fballs})

	def getPath(self):
		#1. Navigate until the intersection contains the square
		#2. Navigate backwards in time from the square until the intersection contains the circle
		#	OR navigate one period, then another, 
		#	and keep going unless the two last navigated periods are the same
		#3. Take the intersection of the free squares at each time step. 
		#	These are the 'safe' squares
		#4. For each time step just pick a move that takes you to a safe square
		#returns a move
		
		period = 10

		#navigate forward in time until a square, saving all the positions in cpos
		newstate = self
		#print self.square.pos
		cpos = self.circle.pos
		sqpos = self.square.pos
		cposetsf = [{cpos}]
		sqposet = self.circle.Poset()
		cposet = self.circle.Poset()
		
		i = 0
		# check if square in the cpos
		freeposet = cposet
		while i < period / dt and sqposet & freeposet == set(): #Contains(freeposet, sqpos):
			newstate = newstate.Evolved()
			freeposet = newstate.Poset() & EvolveCone(cposetsf[-1])
			cposetsf.append(freeposet)
			i += 1

		#navigate backward in time until the circle
		newstate = newstate.Reverse()
		cposetsb = [{sqpos}]
		#print freeposet, '    ', cposet
		while cposet & freeposet == set(): #Contains(freeposet, cpos):
			newstate = newstate.Evolved()
			print cposetsb
			freeposet = newstate.Poset() & EvolveCone(cposetsb[-1])
			cposetsb.append(freeposet & cposetsf.pop())

		#now find the path
		path = []
		#we prefer to move left, and stay still last
		while cposetsb != []:
			freeposet = cposetsb.pop()
			for velo in allvelos:
				cposet = self.circle.Moved(velo).Poset()
				if cposet <= freeposet:
					path.append(velo)
					break

		return path

def Dist(pos1, pos2, p = 1):
	if p ==1:
		#Manhattan distance
		return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
	else:
		#Euclidean distance
		return np.sqrt((pos1[0] - pos1[1]) ** 2 + (pos2[0] - pos2[1]) ** 2)

def getPixels():
	# gets all pixel data from the game screen
	# the x and y coordinates are reversed in this array
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, s_size[0], s_size[1])
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap()
										, left_bound, top_bound, 0, 0, s_size[0], s_size[1])
	return pixbuf.pixel_array

def findSprite(pixels, color = (51,51,51)):
	#given pixels, find the circle
	#may return a list
	for y in range(len(pixels)):
		for x in range(len(pixels[0])):
			if tuple(pixels[y][x]) == color:
				return (x,y)
				#--TODO: find the center of the square, or possible centers
				#not just the topleft-most pixel of it
	return None

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

def PressMove(velo):
	movex = velodict[(velo[0], 0)]
	movey = velodict[(0, velo[1])]
	if movex != 'none':
		gui.keyDown(movex)
	if movey != 'none':
		gui.keyDown(movey)
	time.sleep(dt/2)
	gui.keyUp(movex)
	gui.keyDown(movey)
	#update the state
	global state
	state.Circle = state.Circle.Moved(velo)

def checkDead():
	#TODO: just look for the 'GAME OVER' text
	return False

#===================
#==== MAIN LOOP ====
#===================

#main loop
state = State(newballs = 1)
path = []

while True:

	#stop if dead
	if checkDead():
		break

	#for now, run for 20 seconds at most
	if time.time() > timeout:
		break

	#update state
	pix = getPixels()
	state = state.Update(pix)
	
	#get the next moves
	# if path == []:
	# 	#print state.square.pos
	# 	path = state.getPath()
	
	# #reset the path if square is about to be collected
	# elif len(path) == 1:
	# 	state.Square = None

	# #make the move
	# currentvelo = path.pop()
	# PressMove(currentvelo)

	#sleep
	time.sleep(dt)

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