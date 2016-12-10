import copy
from collections import deque

#A helper function based on make2dList that makes 3d lists
def make3dList(height, rows, cols):
    new2dList, new3dList = [], []
    for row in range (rows): new2dList.append([0] *cols)
    for h in range (height): new3dList.append(copy.deepcopy(new2dList))

    return new3dList

#Our next location recieves a 1 while our current one in zeroed
#This applies to all of the move functions
def moveLeft(placementList, x, y, z):
	placementList[z][y][x] = 0
	placementList[z][y][x + 1] = 1

def moveRight(placementList, x, y, z):
	placementList[z][y][x] = 0
	placementList[z][y][x - 1] = 1

def moveUp(placementList, x, y, z):
	placementList[z][y][x] = 0
	placementList[z][y+1][x] = 1

def moveDown(placementList, x, y, z):
	placementList[z][y][x] = 0
	placementList[z][y-1][x] = 1

class Character():
	def __init__(self, x, y, z):
		self.x, self.y, self.z = x, y, z

	def __repr__(self):
		return "Character at (%d,%d,%d)" % (x, y, z)

	def moveLeft():
		self.x += 1

	def moveRight():
		self.x -= 1

	def moveUp():
		self.y += 1

	def moveDown():
		self.y -= 1


class Andrew(Character):
	def __repr__(self):
		originalResult = super.__repr__(self)
		newResult = originalResult.replace("Character", "Andrew")
		return newResult

class Enemy(Character):
	def __repr__(self):
		originalResult = super.__repr__(self)
		newResult = originalResult.replace("Character", "Enemy")
		return newResult

#A simple helper function that sees if we are within 3D board bounds
def satisfies3DConstraints(board, height, row, col):
    heights, rows, cols = len(board), len(board[0]), len(board[0][0])
    if (height >= 0 and row >= 0 and col >= 0 
    	and height < heights and row < rows and col < cols):
        return True
    else:
    	#print("Doesn't satisfy", "height:", height)
        return False

#Uses recursive backtracking to find a path to the player
#from a provided start point
def findPath(placementList, startPoint, existentPaths):
	heights, rows, cols = len(placementList), len(placementList[0]), len(placementList[0][0])
	#The start point is in x, y, z notation
	startCol, startRow, startHeight  = startPoint[0], startPoint[1], startPoint[2]
	path = []
	visited = []

	def isLegal(height, row, col, dheight, drow, dcol):
		newHeight, newRow, newCol = height + dheight, row + drow, col + dcol
		#We don't want to take the path another enemy has already taken
		#print("height:", height, "row:", row, "col:", col)
		
		for existentPath in existentPaths:
			if containsPath(existentPath, path):
				return False
		
		#We are legal if we are within bounds and not hitting a wall. 
		#Hitting the player is ok (and wanted)
		if (satisfies3DConstraints(placementList, newHeight, newRow, newCol) 
			and placementList[newHeight][newRow][newCol] != -1):
			return True
		#print("not legal!")
		return False

	def solve(height = startHeight, row = startRow, col = startCol):
		#print(path)
		directions = [(0, 1, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)]
		#If we find the player
		if ((height, row, col) in path): return False
		path.append((height, row, col))
		#print(path)
		if (satisfies3DConstraints(placementList, height, row, col) 
						and placementList[height][row][col] == 1):
			return True

		for dheight, drow, dcol in directions:
			if (isLegal(height, row, col, dheight, drow, dcol)):
				#If we can make the next move, try to solve it
				newHeight, newRow, newCol = height + dheight, row + drow, col + dcol

				solution = solve(newHeight, newRow, newCol)
				if (solution):
					return solution
		#Move didn't work so remove it from path list
		path.remove((height, row, col))
		return False

	return path if solve() else None

def playGame():
	#Dimensions
	length, width, height = 5, 5, 2
	andrewSpawnLocation = (0, 0, 0)
	enemy1SpawnLocation = (1, 4, 2)
	enemy2SpawnLocation = (1, 1, 3)

	#Define andrew and the two enemies
	andrew = Andrew(andrewSpawnLocation[0], andrewSpawnLocation[1], andrewSpawnLocation[2])
	enemy1 = Enemy(enemy1SpawnLocation[0], enemy1SpawnLocation[1], andrewSpawnLocation[2])
	enemy2 = Enemy(enemy2SpawnLocation[0], enemy2SpawnLocation[1], enemy2SpawnLocation[2])

	placement = make3dList(length, width, height)

def containsPath(superPath, subPath):
	#We can't tell much from a subPath of size one
	if (len(subPath) == 1):
		return False
	#The super path must atleast have the start of the subPath
	if (subPath[0] in superPath):
		superStartIndex = superPath.index(subPath[0])
	else:
		return False
	#We loop through the subPath and see if we can trace
	#it inside of the superPath
	for i in range(len(subPath)):
		if (superPath[superStartIndex + i] != subPath[i]):
			return False
	return True

#A helper to calculate a simple representation of the path
def calculateBasicPath(path):
	if path == None:
		return None
	basicPath = []
	#Initialize our previous x and y
	prevZ = path[0][0]
	prevY = path[0][1]
	prevX = path[0][2]
	for point in path:
		currZ = point[0]
		currY = point[1]
		currX = point[2]

		if currZ != prevZ:
			#check if we are not already recording a Z change
			if len(basicPath) == 0 or basicPath[-1][0] != "Z":
				basicPath.append(["Z", 0, currZ])

			#we want to change the number of the last element in basicPath
			if (currZ > prevZ):
				basicPath[-1][1] += 1
			elif (currZ < prevZ):
				basicPath[-1][1] -= 1

			#record the latest destination
			basicPath[-1][2] = currZ

		elif currY != prevY:
			if len(basicPath) == 0 or basicPath[-1][0] != "Y":
				basicPath.append(["Y", 0, currY])
			if (currY > prevY):
				basicPath[-1][1] += 1
			elif (currY < prevY):
				basicPath[-1][1] -= 1

			basicPath[-1][2] = currY

		elif currX != prevX:
			if len(basicPath) == 0 or basicPath[-1][0] != "X":
				basicPath.append(["X", 0, currX])
			if (currX > prevX):
				basicPath[-1][1] += 1
			elif (currX < prevX):
				basicPath[-1][1] -= 1

			basicPath[-1][2] = currX

		prevZ = currZ
		prevY = currY
		prevX = currX
	return basicPath

def generate3DMap(heights, rows, cols):
	map = make3dList(heights, rows, cols)

	wallLength = 6
	wallWidth = 0

	wallPos = (0, 6, -6)

	z = wallPos[0]
	y = wallPos[1]
	x = wallPos[2]

	for width in range(x - wallWidth/2, x + wallWidth/2):
		map[0][0][width] = -1

	for length in range(y - wallLength/2, y + wallLength/2):
		map[0][length][0] = -1 

	return map

#Adapted from http://compsci.ca/v3/viewtopic.php?t=32571
def breadthFirstSearch(startPoint, placementList):
    x = startPoint[0]
    y = startPoint[1]
    z = startPoint[2]
    Map = copy.copy(placementList)
    queue = deque( [(x,y,z,None)]) #create queue 
    while len(queue)>0: #make sure there are nodes to check left 
        node = queue.popleft() #grab the first node 
        x = node[0] #get x and y 
        y = node[1] 
        z = node[2]
        if  ((x < 0 or y < 0 or z < 0) or (x >= len(Map) or y >= len(Map[0]) or z >= len(Map[0][0])) or Map[x][y][z] == -1): #if it's not a path, we can't try this spot 
            continue
        if Map[x][y][z] == 1: #check if it's an exit 
            return GetPathFromNodes(node) #if it is then return the path 
        Map[x][y][z] = -1 #make this spot explored so we don't try again 
        for i in [[x-1,y, z],[x+1,y, z],[x,y-1, z],[x,y+1, z], [x, y, z-1], [x, y, z+1]]: #new spots to try 
            queue.append((i[0],i[1],i[2],node))#create the new spot, with node as the parent 
    return [] 

def GetPathFromNodes(node): 
    path = [] 
    while(node != None): 
        path.append((node[0],node[1], node[2])) 
        node = node[3] 
    return path


def findPaths():
	existentPaths = []
	placementList = [[[0, 0, 0, 0, 0],
					 [0, 0, -1, 0, 0],
					 [0,-1, 0,-1, 0],
					 [0,-1, 0,-1, 0],
					 [0, 0, 0,-1, 0]],

					 [[1, 0, 0, 0, 0],
					 [0, -1, 0, 0, 0],
					 [0,-1, -1,-1, 0],
					 [0,-1, 0,-1, 0],
					 [0, 0, 0,-1, 0]]]

	placementList2 = make3dList(1, 20, 10)
	placementList2[0][10][9] = 1

	enemy1Start = (8, 12, 0)
	enemy2Start = (0, 4, 0)
	#existentPaths.append(findPath(placementList, enemy2Start, existentPaths))
	#existentPaths.append(findPath(placementList, enemy2Start, existentPaths))

	#print(calculateBasicPath(existentPaths[0]))
	bfsStart = (1, 4, 4)
	bfsResult = breadthFirstSearch(bfsStart, placementList)
	bfsResult.reverse()
	return bfsResult


print(findPaths())

