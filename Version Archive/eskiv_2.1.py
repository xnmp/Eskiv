#initialize
for i in range(1):
	import sys
	#sys.path.append('/usr/lib/python2.7/dist-packages/')
	sys.path.append('/home/chong/anaconda2/lib/python2.7/site-packages')

	import gtk.gdk
	import time
	import pyautogui as gui
	import subprocess
	import os
	import time
	import numpy as np

	#corners are (1186,213) , (1186,848) , (1887,213) , (1887,848)
	top_bound = 213
	bottom_bound = 848
	left_bound = 1186
	right_bound = 1887
	x_size = right_bound - left_bound
	y_size = bottom_bound - top_bound

	dt = 0.1
	ball_id = 0
	state = State(newballs = 1)
	timeout = time.time() + 20
	velodict = {(-1,0):'left', (1,0):'right', (0,-1):'up', (0,1):'down', (0,0):'none'}
	allvelos = [(x, y) for x in (-1,0,1) for y in (-1,0,1)]

def VeloMove(velo):
	movex = velodict[(velo[0], 0)]
	movey = velodict[(0, velo[1])]
	if movex != 'none':
		gui.keyDown(movex)
	if movey != 'none':
		gui.keyDown(movey)
	time.sleep(dt/2)
	gui.keyUp(movex)
	gui.keyDown(movey)

def pixel_at(x, y):
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, 1, 1)
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap(), x, y, 0, 0, 1, 1)
	return tuple(pixbuf.pixel_array[0, 0])

def flatten(l, ltypes=(list)):
	#found at http://rightfootin.blogspot.com.au/2006/09/more-on-python-flatten.html
	ltype = type(l)
	l = list(l)
	i = 0
	while i < len(l):
		while isinstance(l[i], ltypes):
			if not l[i]:
				l.pop(i)
				i -= 1
				break
			else:
				l[i:i + 1] = l[i]
		i += 1
	return ltype(l)

def move_eskiv_window():
	#start eskiv in the TOP RIGHT CORNER and then run this. 
	#os.system("gnash ~/Downloads/Eskiv.swf")
	#pid = subprocess.Popen(['gnash', "../Downloads/Eskiv.swf"]) 
	#resize window
	gui.moveTo(280,197)
	gui.dragRel(670,810)
	#move window
	gui.moveTo(40,10)
	gui.dragRel(960,0)
	#print gui.position()

#move_eskiv_window()

def mouseloc():
	#print gui.position()
	print pixel_at(1186,213)
	
#mouseloc()

class Eskiv(object):
	def __init__(self, pos = None, pos_er = 0)
		self.pos = pos
		self.pos_er = pos_er

class FuzzyBall(Eskiv):
	speed = 0.1
	radius = 10
	# a fuzzyball has a set of positions instead of one position
	def __init__(self, poset = set(), velo = None):
		self.poset = poset
		self.velo = velo
		#this is the range of the ball. Of the form (min, max)
		self.limits = [[0, x_size], [0, y_size]]

	def Update(self, pixels):
		for pos in self.poset:
			color = pixels[*pos]
			if color[2] != 0 and color[0] == 0:
				#if the pos is blank, remove it from the fuzzy set
				self.poset.remove(pos)

	def Diam(self):
		#diameter of the fuzzyball, helper function to convert fuzzyballs to balls
		for i in range(2):
			self.limit[i][0] = min(self.poset, key = lambda x: x[i][0])
			self.limit[i][1] = max(self.poset, key = lambda x: x[i][1])
		self.diam = max(self.limit[0][1] - self.limit[0][0], self.limit[1][1] - self.limit[1][0])

class Ball(FuzzyBall):
	#the pos is known in this case
	def __init__(self, pos = None, velo = None):
		self.pos = pos
		self.velo = velo

class Circle(Eskiv):
	speed = 0.12
	radius = 15
	def __init__(self, pos = None, pos_er = 0):
		self.pos = pos
		self.pos_er = pos_er

class Square(Eskiv):
	radius = 15
	def __init__(self, pos = None, pos_er = 0):
		self.pos = pos
		self.pos_er = pos_er

#STATE class: EXPLANATION
	# a STATE is a list of balls number to a list of tuples where the ball could be.
	# the list could be a single tuple, if we're sure of where the ball is
	# or it could be nothing, if we have no idea where the ball is
	# also dont forget the velocity.
	# still a little fuzzy about how to deal with multiple balls appearing at once. 

	'''
	HOW IT WORKS:
	1. We know how many balls there are.
	2. All balls except the newest few (up to 3) we already know the position and velocity of. 
	3. Project forward based on the known balls
	4. The filled-in pixels that aren't expected to be filled-in: 
		we first assign to the positions of the balls
		the velocity can be any of the 4
	5. Next frame: we 'hypothesize' that 4 points will be filled-in
		if a pixel that we hypothesized to be filled isn't filled, 
		then can delete the position and velocity tied to that pixel
	'''

class State(object):

	def __init__(self, balls = set(), fballs = set(), circle = Circle(), square = Square(), newballs = 0):
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
		
		#circles and squares are updated via Evolved, if necessary
		blueness = 0
		for x,y in zip(range(x_size), range(y_size)):
			color = pixels[x][y]
			
			# the pixel is either
			#	- passable and in the error radius of a fuzzyball -> update the fuzzyball
			#	- unpassable and outside all error radii -> assign a new ball

			# if the pixel is unpassable,
			if color[0] == 0 and color[2] > 0:
				expected = False
				for ball in self.balls:
					dist = Dist((x,y), ball.pos, p = 2)
					#check if the pixel lies within the domain of a known ball
					if dist < ball.pos_er + ball.radius:
						expected = True
				
				if expected == False:
					# if the pixel is outside all known balls
					for ball in self.bballs:
						#now check the bballs
						if ball.pos != None and dist < ball.pos_er + ball.radius and color[2] > ball.color:
							#reset the pos and pos_er according to the bluest pixel in the radius
							ball.color = color[2]
							ball.pos_er = ball.getError()
							ball.pos = (x,y)
							expected = True
					if expected = False:
						# if the pixel is also outside all bballs, initialize an unknown ball
						self.FirstUnknownBall() = Ball((x,y), color = color[2])

			#if the pixel is passable
			else:
				for ball in self.balls:
					dist = Dist((x,y), ball.pos, p = 2)
					#check if the pixel lies within the domain of a known ball
					if dist < ball.pos_er + ball.radius:
						#add the ball to the new pixels
						if color[2] > blueness:
							blueness = color[2]
							ball.pos_er = self.DistToCenter(blueness)
							ball.pos = (x,y)
		return

	def Evolved(self, tau = dt):
		#helper function for update and navigate
		#go into the future by tau
		#does not happen inplace
		#--TODO: do this for lists within lists
		ps = []
		for pos, velo in zip(self.pos, self.velo)
			if pos.
		ps = list(Move(self.pos, ))[]
		vs = []
		for i in range(len(self.pos)):
			for j in range(1):
				p = self.pos[i][j]
				v = self.velo[i][j]
				p += VELOCITY * v * tau / dt
				if p < 0:
					p = abs(p)
					ReverseVelo()
				elif j = 0 and p > x_size:
					p = 2 * x_size - p
				elif j = 1 and self.pos[i][j] > x_size:
					p = 2 * y_size - p
				if j = 0:
					p0 = p
				else:
					p1 = p
			ps.append((p0, p1))
		#new square and circle positions, only if necessary
		#self.cpos = CirclePos(pixels)
		#self.sqpos = SquarePos(pixels)
		return State(ps, self.velo)



	def EvolvedCircle(self, tau = dt):
		circps = [(p[0] + v[0], p[1] + v[1]) for p in self.cpos for v in allvelos]
		return circps

	def Navigate(self, cpos):
		#helper function to getpath
		#returns the positions that are navigable in the next time step
		#cpos is the position of the circle as a tuple, OR a list of such positions
		#basically we expand the cpos by a radius, then intersect this with state.Evolve
		newstate = self.Evolved()
		return Intersect(newstate.pos, self.EvolvedCircle())

	def Intersects(self, cpos, stop = True):
		#intersect for a state
		if Intersect(self.pos, cpos, stop = True) != []:
			return True
		return False

	def ReverseVelos(self):
		#reverse velocities
		veloutlist = []
		for velo in self.velo:
			if isinstance(velo, list):
				velout = map(velo, ReverseVelo)
			else:
				velout = ReverseVelo(velo)
			veloutlist.append(velout)
		return State(self.pos, veloutlist)

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
		cposf = [self.cpos]
		while i < period / dt:
			newstate = newstate.Evolved()
			cposf.append(newstate.Navigate(cposf[-1:]))
			# check if square in the cpos
			if newstate.Intersects([self.sqpos]):
				break

		#navigate backward in time until the circle
		newstate = newstate.ReverseVelos()
		cposb = [self.sqpos]
		while not newstate.Intersects([self.cpos]):
			newstate = newstate.Evolved()
			cposb.append(Intersect(newstate.pos, cposf.pop()))

		#now find the path
		path = []
		cpos = self.cpos
		#we prefer to move left, and stay still last
		for move in ['left','right','up','down','none']:
			newpos = Move(cpos, move)
			if Intersect(newpos, cposb.pop()) != []:
				cpos = newpos
				path.append(move)
				break

		return path

	def pos(self):
		return [ball.pos for ball in self.balls]

def Intersect(poslist1, poslist2, stop = False):
	#helper function to navigate
	#cpos is a list of positions (tuples)
	#returns the positions that are safe
	intersection = []
	for ballpos in poslist1:
		for checkpos in poslist2:
			if Dist(ballpos, checkpos) < 5:
				intersection.append(checkpos)
				if stop:
					break
	return intersection

def ReverseVelo(velo):
	#just reverses a velocity
	return (-velo[0], -velo[1])

def Move(poslist, velo, obj = "ball"):
	#this basically just evolves a poslist, one velo
	if obj = 'ball':
		objvelo = BALL_VELO
	else:
		obj = CIRC_VELO
	for pos in poslist:
		if isinstance(pos, list):
			yield list(Move(pos, velo))
		else:
			res0 = pos[0] + velo[0] * objvelo
			res1 = pos[1] + velo[1] * objvelo
			yield (res0, res1)

def Dist(pos1, pos2, p = 1):
	if p ==1:
		#Manhattan distance
		return max(abs(pos1[0] - pos2[0]), abs(pos1[1] - pos2[1]))
	else:
		#Euclidean distance
		return np.sqrt((pos1[0] - pos1[1]) ** 2 + (pos2[0] - pos2[1]) ** 2)

def getRawPixels():
	# gets all pixel data from the game screen
	# the x and y coordinates are reversed in this array
	rw = gtk.gdk.get_default_root_window()
	pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, False, 8, x_size, y_size)
	pixbuf = pixbuf.get_from_drawable(rw, rw.get_colormap()
										, left_bound, top_bound, 0, 0, x_size, y_size)
	print pixbuf.pixel_array.shape
	return pixbuf.pixel_array

def convRawPixels(rawpixels):
	#takes a raw pixel array and converts each position to either passable (True) or unpassable (False)
	pix = [[True] * x_size] * y_size
	for x, PixRow in enumerate(rawpixels):
		for y in PixRow: # note that we've swapped x and y compared to other funcs that loop over a pixel array
			if rawpixels[x][y] == ():
				pix[x,y] = True
			else:
				pix[x,y] = False
	return pix

def CirclePos(rawpixels, color = (51,51,51)):
	#given pixels, find the circle
	#may return a list
	for y, PixRow in enumerate(rawpixels):
		for x in PixRow:
			if pixels[x][y] == color
				return (x,y)
				#--TODO: find the center of the square, or possible centers
				#not just the topleft-most pixel of it

def SquarePos(rawpixels, color = (102,102,102)):
	#given pixels, find the square
	#may return a list
	for y, PixRow in enumerate(rawpixels):
		for x in PixRow:
			if pixels[x][y] == color
				return (x,y)
				#--TODO: find the center of the square, or possible centers
				#not just the topleft-most pixel of it

def collectSquare(cpos, sqpos, move):
	#returns True if the square will be collected in the next move
	if Dist(cpos + move * VELOCITY, sqpos) < 5: #threshold value is 5
		return True
	return False

def countBalls(cpos):
	#returns the number of balls that need to be search for
	timeout = time.time() + dt/2 #waits half a time step for balls to appear
	numballs = 0
	while time.time() < timeout: #or no more squares
		sqpos = SquarePos(getPixels())
		if sqpos == oldsqpos:
			oldsqpos = sqpos
			numballs += 1
			time.sleep(dt/5)
	return numballs

def checkDead():
	#just look for the 'GAME OVER' text
	return False


#===================
#==== MAIN LOOP ====
#===================

#main loop
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
	if path == []:
		path = state.getPath()
	move = path.pop()
	
	#reset the path if square is about to be collected
	if collectSquare(state, sqpos, move):
		path = []

	#make the move
	gui.press(move)

	#sleep
	time.sleep(dt)

#TO DO LIST: 
	'''
	1. hit the square at the optimal time and angle
	2. if there is no path due to too many unknown positions and velocities, 
	   then stall until positions and velocities can be known
	3. failing this, guess some positions and velocities in an optimal way
	4. full on Kalman filter for the state
	5. take the wildest path for maximum impression
	'''