#Name: Daniel Barychev
#Andrew Id: dbaryche
#Section: D

#The panda and andrew models have been sourced from the Panda3D samples
#and the basic movement code has been taken from the Roaming Ralph Demo
#(https://www.panda3d.org/manual/index.php/Sample_Programs:_Roaming_Ralph)
#That sample program was the starting point for this project
#and the way that I handle collisions and camera code. The crystal and decoy
#models come from the Panda3D art package and specifically, BVW at CMU

from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionNode, CollisionHandlerPusher
from panda3d.core import CollisionHandlerQueue, CollisionRay, CollisionSphere, CollisionTube
from panda3d.core import Filename, AmbientLight, DirectionalLight
from panda3d.core import PandaNode, NodePath, Camera, TextNode
from panda3d.core import CollideMask
from panda3d.core import CollisionNode
from panda3d.core import CollisionTraverser
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import Sequence
from panda3d.core import Point3
from collections import deque
from direct.task import Task
import random
import sys
import os
import math
import copy

#The onscreen display methods
def addScore(msg):
    return OnscreenText(text= msg, style=1, fg=(1, 1, 1, 1), scale=.05,
                        shadow=(0, 0, 0, 1), parent=base.a2dTopLeft,
                        pos=(0.08, -0.1), align=TextNode.ALeft)

def addTitleScreen():
    return OnscreenImage(image = 'models/title_screen.jpg', pos = (0, 0, 0), scale = (1.9, 0, 1))

def addGameOverScreen():
    return OnscreenImage(image = 'models/game_over_screen.jpg', pos = (0, 0, 0), scale = (1.9, 0, 1))


class AnimatedAndrew(ShowBase):
    def __init__(self):
        # Set up the window, camera, etc.
        ShowBase.__init__(self)

        # Set the background color to black
        self.win.setClearColor((0, 0, 0, 1))

        # This is used to store which keys are currently pressed.
        self.keyMap = {
            "left": 0, "right": 0, "forward": 0, "cam-left": 0, "cam-right": 0, "use-decoy": 0,
            "come-towards": 0, "destroy-title": 0, "super-score": 0}

        self.score = 0

        # Title screen
        self.titleScreen = addTitleScreen()
        self.scoreTitle = addScore("Score: %d" %(self.score))

        #select the models to use as the sky and environment

        self.sky = loader.loadModel("models/sky")
        self.sky.reparentTo(render)
        
        self.environ = loader.loadModel("models/basic_terrain_floor2")
        self.environ.reparentTo(render)

        #We are always 5 larger than the edge
        length, width, height = 140, 140, 3

        self.xshift = 30
        self.yshift = 30

        #A placement list to track my characters
        self.map = make3dList(height, length, width)
        self.initMap()

        self.map[0][36][12] = 1

        self.andrew = Actor("models/ralph",
                           {"run": "models/ralph-run",
                            "walk": "models/ralph-walk"})
        self.andrew.reparentTo(render)
        self.andrew.setScale(.2)
        self.startPos = ((18, 6, 0))
        self.andrew.setPos((self.startPos))

        self.andrewPositions = [self.andrew.getPos()]
        self.andrewMovePositions = []

        # Load and transform the panda actor.
        self.pandas = []
        self.pandaMoveElements = dict()
        self.pandaRecalculation = dict()
        self.pandaPaths = dict()
        self.pandaStop = dict()
        self.pandaSpeed = 1
        self.existentPaths = []
        self.existentBasicPaths = []
        self.pandaActor = Actor("models/panda-model",
                                {"walk": "models/panda-walk4"})
        self.pandaActor.loop("walk")

        self.numPandas = 2

        for i in range(self.numPandas):
            n = render.attachNewNode("Panda")
            self.pandaActor.instanceTo(n)

            n.setScale(0.0025, 0.0025, 0.0025)

            n.reparentTo(render)
            if i % 2 == 0:
                n.setPos((-18, -18, 0))
                n.setH(90)
            else:
                n.setPos((-18, 69, 2))
                n.setH(90)
            
            self.pandaMoveElements[n] = 0
            self.pandaRecalculation[n] = True
            self.pandaStop[n] = False
            self.pandas.append(n)

        self.crystal = loader.loadModel("models/crystal/greencrystal")
        self.crystal.reparentTo(render)
        self.crystal.setPos((-18, 6, 0))
        self.crystal.setScale(0.015)
        """
        self.possibleCrystalPositions = [(-57, 54, 2), (-81, 57, 2), (-93, 75, 2), (-69, 75, 2),
                                        (6, 57, 2), (-6, 72, 2), (6, 87, 2),
                                        (-18, 6, 0), (18, 18, 0)]
        """
        #Only include half of the second floor for now since
        #it makes demoing much faster and easier
        self.possibleCrystalPositions = [(6, 57, 2), (-6, 72, 2), (6, 87, 2),
                                        (-18, 6, 0), (18, 18, 0)]                            

        self.walls = []
        self.wall = loader.loadModel("models/brick_wall")

        #In the format: [(x, y, z), H]
        #[(18, 24, 0), 90] is purposely omitted from the 0th floor left
        #[(18, 51, 2), 90], [(-24, 93, 2), 0] are purposely omitted from the right second floor
        #[(-51, 93, 2), 0] is purposely omitted from the left second floor
        self.wallPositions = [[(-18, -24, 0), 90], [(-6, -24, 0), 90], [(6, -24, 0), 90], [(18, -24, 0), 90], 
                                [(24, -18, 0), 0], [(24, -6, 0), 0], [(24, 6, 0), 0], [(24, 18, 0), 0],
                                [(-18, 24, 0), 90], [(-6, 24, 0), 90], [(6, 24, 0), 90],
                                [(-24, -18, 0), 0], [(-24, -6, 0), 0], [(-24, 6, 0), 0], [(-24, 18, 0), 0],

                                #1st floor inner maze
                                [(-18, -12, 0), 90], [(-6, -12, 0), 90], [(6, -12, 0), 90], 
                                [(-18, 0, 0), 90], [(-6, 0, 0), 90], [(6, 0, 0), 90],
                                [(-18, 12, 0), 90], [(-6, 12, 0), 90], [(6, 12, 0), 90], 
                                [(12, -6, 0), 0], [(12, 18, 0), 0],

                                #2nd floor right boundary
                                [(-18, 51, 2), 90], [(-6, 51, 2), 90], [(6, 51, 2), 90], 
                                [(24, 57, 2), 0], [(24, 69, 2), 0], [(24, 81, 2), 0], [(24, 93, 2), 0],
                                [(-18, 99, 2), 90], [(-6, 99, 2), 90], [(6, 99, 2), 90], [(18, 99, 2), 90],
                                [(-24, 57, 2), 0], [(-24, 69, 2), 0], [(-24, 81, 2), 0], 

                                #2nd floor right inner maze
                                [(12, 57, 2), 0], [(6, 63, 2), 90], [(-6, 63, 2), 90], 
                                [(-12, 69, 2), 0], [(-12, 81, 2), 0],
                                [(6, 81, 2), 90], [(-6, 81, 2), 90],

                                #2nd floor left boundary
                                [(-93, 51, 2), 90], [(-81, 51, 2), 90], [(-69, 51, 2), 90], [(-57, 51, 2), 90],
                                [(-51, 57, 2), 0], [(-51, 69, 2), 0], [(-51, 81, 2), 0], 
                                [(-93, 99, 2), 90], [(-81, 99, 2), 90], [(-69, 99, 2), 90], [(-57, 99, 2), 90],
                                [(-99, 57, 2), 0], [(-99, 69, 2), 0], [(-99, 81, 2), 0], [(-99, 93, 2), 0],

                                #2nd floor left inner maze
                                [(-57, 57, 2), 90], [(-81, 57, 2), 90], [(-57, 87, 2), 90], [(-81, 87, 2), 90],
                                [(-63, 69, 2), 0], [(-63, 81, 2), 0], [(-75, 69, 2), 0], [(-75, 81, 2), 0],
                                [(-87, 69, 2), 0], [(-87, 81, 2), 0]]

        for i in range(len(self.wallPositions)):
            wallPosition = self.wallPositions[i][0]
            wallH = self.wallPositions[i][1]

            w = render.attachNewNode("Wall")
            self.wall.instanceTo(w)

            w.reparentTo(render)
            w.setPos(wallPosition[0], wallPosition[1], wallPosition[2])
            w.setH(wallH)

            self.walls.append(w)

        self.addWallsToMap()
        

        self.plane = loader.loadModel("models/plane_wide")
        self.planePositions = [[(18, 30, 0), 270]]

        for i in range(len(self.planePositions)):
            planePosition = self.planePositions[i][0]
            planeH = self.planePositions[i][1]

            p = render.attachNewNode("Plane")
            self.plane.instanceTo(p)

            p.reparentTo(render)
            p.setPos(planePosition[0], planePosition[1], planePosition[2])
            p.setH(planeH)

        
        self.straightPlane = loader.loadModel("models/plane_straight_wide")
        self.straightPlanePositions = [[(-30, 93, 2), 0]]

        for i in range(len(self.straightPlanePositions)):
            straightPlanePosition = self.straightPlanePositions[i][0]
            straightPlaneH = self.straightPlanePositions[i][1]

            sp = render.attachNewNode("Straight Plane")
            self.straightPlane.instanceTo(sp)

            sp.reparentTo(render)
            sp.setPos(straightPlanePosition[0], straightPlanePosition[1], straightPlanePosition[2])
            sp.setH(straightPlaneH)
        

        self.extraFloor = loader.loadModel("models/basic_terrain_floor2")
        self.extraFloorPositions = [[(0, 75, 2), 0], [(-75, 75, 2), 0]]
        self.extraFloors = []

        for i in range(len(self.extraFloorPositions)):
            extraFloorPosition = self.extraFloorPositions[i][0]
            extraFloorH = self.extraFloorPositions[i][1]

            ef = render.attachNewNode("Extra Floor")
            self.extraFloor.instanceTo(ef)

            ef.reparentTo(render)
            ef.setPos(extraFloorPosition[0], extraFloorPosition[1], extraFloorPosition[2])
            ef.setH(extraFloorH)

            self.extraFloors.append(ef)

        self.decoy = loader.loadModel("models/decoy/littlebrother")
        self.decoy.reparentTo(render)
        #We put the decoy way under the map so it can't be seen
        self.decoy.setPos((18, -6, -10))
        self.decoy.setScale(0.7)
        self.decoy.setH(180)
        #Initialize the decoy location to nothing
        self.decoyLocation = []

        # Create a floater object, which floats 2 units above andrew.  We
        # use this as a target for the camera to look at.

        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(self.andrew)
        self.floater.setZ(2.0)

        # Accept the control keys for movement and rotation

        self.accept("escape", sys.exit)
        self.accept("arrow_left", self.setKey, ["left", True])
        self.accept("arrow_right", self.setKey, ["right", True])
        self.accept("arrow_up", self.setKey, ["forward", True])
        self.accept("a", self.setKey, ["cam-left", True])
        self.accept("s", self.setKey, ["cam-right", True])
        self.accept("arrow_left-up", self.setKey, ["left", False])
        self.accept("arrow_right-up", self.setKey, ["right", False])
        self.accept("arrow_up-up", self.setKey, ["forward", False])
        self.accept("a-up", self.setKey, ["cam-left", False])
        self.accept("s-up", self.setKey, ["cam-right", False])
        self.accept("p", self.setKey, ["destroy-title", True])
        self.accept("h", self.setKey, ["display-help", True])
        self.accept("g", self.setKey, ["destroy-help", True])
        self.accept("d", self.setKey, ["use-decoy", True])
        #Hidden feature to demo the bfs algorithm versus the backtracking algorithm
        self.accept("x", self.setKey, ["super-score", True])

        taskMgr.add(self.move, "moveTask")
        taskMgr.add(self.movePanda, "movePandaTask")
        taskMgr.add(self.updateMap, "updateMap")
        taskMgr.add(self.destroyTitleScreen, "destroyTitleScreen")
        taskMgr.add(self.useDecoy, "useDecoy")

        #Game state variables
        self.isMoving = False

        #Set up the camera
        self.disableMouse()
        self.camera.setPos(self.andrew.getX(), self.andrew.getY() + 10, 2)

        #Original Collision Logic

        self.setupCollision()

        #lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor((.3, .3, .3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection((-5, -5, -5))
        directionalLight.setColor((1, 1, 1, 1))
        directionalLight.setSpecularColor((1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))

    #Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value

    #Functions to control the display 
    #of the title and help screens
    def destroyTitleScreen(self, task):
        if self.keyMap["destroy-title"]:
            self.titleScreen.destroy()
        return task.cont

    def useDecoy(self, task):
        #We can use the decoy when our score is above five
        if self.keyMap["use-decoy"]:
            decoyPos = self.getSecondClosestZeroPoint(self.andrew)
            decoyX = -1 * (decoyPos[0] - self.xshift)
            decoyY = decoyPos[1] - self.yshift
            decoyZ = decoyPos[2]
            self.decoy.setX(decoyX)
            self.decoy.setY(decoyY)
            self.decoy.setZ(decoyZ)
            self.decoyLocation = [decoyPos]
            self.map[decoyPos[2]][decoyPos[1]][decoyPos[0]] = 1
            self.keyMap["use-decoy"] = False

        return task.cont


    def movePanda(self, task):
        dt = globalClock.getDt()

        #We don't want the panda to move if we are displaying another screen
        if self.keyMap["destroy-title"]:
            for panda in self.pandas:

                if self.pandaStop[panda]:
                    break

                pandaZ = int(panda.getZ())
                pandaY = int(panda.getY() + self.yshift)
                pandaX = abs(int(panda.getX()) - self.xshift)
                
                pandaLocation = (pandaX, pandaY, pandaZ)
                andrewLocation = self.findOneInMap()

                andrewX = andrewLocation[0]
                andrewY = andrewLocation[1]
                andrewZ = andrewLocation[2]


                
                #Recalculate the panda path, but only if andrew is not moving floors
                if self.pandaRecalculation[panda] and not self.andrewMovingZ():
                    #We optomize the directions depending on where andrew
                    #is in relation to the panda
                    self.directions = [(0, 1, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)]

                    
                    if (panda.getH() == 0):
                        #In the z, y, x format
                        self.directions = [(0, 1, 0), (0, -1, 0), (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)]

                    elif(panda.getH() == 90):
                        self.directions = [(0, 0, -1), (0, 0, 1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)]

                    elif(panda.getH() == 180):
                        self.directions = [(0, -1, 0), (0, 1, 0), (0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0)]

                    elif(panda.getH() == 270):
                        self.directions = [(0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0)]

                    if (int(panda.getZ()) == int(self.andrew.getZ())):
                        self.directions = self.directions[:-2]
                    
                    #If we have a score less than 3, use backtracking. Use breadth first search otherwise.
                    #Thus, the pandas get smarter as the score goes up
                    if self.score < 3:
                        self.pandaPaths[panda] = self.adjustBasicPath(calculateBasicPath(self.findPath(pandaLocation)))
                    else:
                        bfsRaw = breadthFirstSearch(pandaLocation, self.map)
                        bfsRaw.reverse()
                        bfsOption = calculateBasicPath(bfsRaw)
                        self.pandaPaths[panda] = bfsOption
                    
                    #Uncomment these lines to see the path the panda
                    #takes in where andrew is in relation

                    #print(self.pandaPaths[panda])
                    #print(andrewX, andrewY, andrewZ)
                    
                    self.pandaRecalculation[panda] = False

                path = self.pandaPaths[panda]
                
                if path == None or path in self.existentBasicPaths:
                    self.pandaStop[panda] = True
                    self.pandaRecalculation[panda] = True

                    #We set the panda to the closest zero spot 
                    #since that may put it back on track
                    closestZero = self.getClosestZeroPoint(panda)
                    #a reverse coordinate conversion is needed
                    panda.setX(-1 * (closestZero[0] - self.xshift))
                    panda.setY(closestZero[1] - self.yshift)
                    panda.setZ(closestZero[2])

                    break

                moveNumber = self.pandaMoveElements[panda]
                pathElement = path[moveNumber]
                direction = pathElement[0]
                magnitude = pathElement[1]
                destination = pathElement[2]

                moveFactor = 10

                if direction == "Y":   
                    #We check for the sign of our magnitude to
                    #see how we should orient ourselves          
                    if magnitude >= 0:
                        panda.setH(180)
                       
                    elif magnitude < 0:
                        panda.setH(0)

                    #2 is the epsilon
                    if ((pandaY < destination and magnitude > 0) or (pandaY > destination and magnitude < 0)):
                        panda.setY(panda, -250 * dt * moveFactor * self.pandaSpeed)
                
                    else:
                        if self.pandaMoveElements[panda] < len(path) - 1:
                            self.pandaMoveElements[panda] += 1
                        else:
                            #When we reach the end of our path

                            #update the necessary dictionaries
                            self.pandaMoveElements[panda] = 0
                            self.pandaRecalculation[panda] = True
                            self.existentBasicPaths.append(path)
                            

                elif direction == "X":
                    if magnitude > 0:
                        panda.setH(270)
                        
                    elif magnitude < 0:
                        panda.setH(90)

                    if ((pandaX < destination and magnitude > 0) or (pandaX > destination and magnitude < 0)):
                        #We use a setY() because we have changed our H value
                        panda.setY(panda, -250 * dt * moveFactor * self.pandaSpeed)
                        
                    else:
                        if self.pandaMoveElements[panda] < len(path) - 1:
                            self.pandaMoveElements[panda] += 1
                        else:
                            self.pandaMoveElements[panda] = 0
                            self.pandaRecalculation[panda] = True
                            self.existentBasicPaths.append(path)
                            

                elif direction == "Z":
                    if ((pandaZ < destination and magnitude > 0) or (pandaZ > destination and magnitude < 0)):
                        panda.setZ(panda, 1000 * dt * magnitude * self.pandaSpeed)
                        
                    else:
                        if self.pandaMoveElements[panda] < len(path) - 1:
                            self.pandaMoveElements[panda] += 1
                        
                        else:
                            self.pandaMoveElements[panda] = 0
                            self.pandaRecalculation[panda] = True
                            self.existentBasicPaths.append(path)
                       
        return task.cont

    # Accepts arrow keys to move either the player or the menu cursor,
    # Also deals with grid checking and collision detection
    def move(self, task):
        #The game is over when andrew hits a panda
        for panda in self.pandas:
            if (abs(panda.getY() - self.andrew.getY()) < 1 and abs(panda.getX() - self.andrew.getX()) < 1 
                                                                and abs(panda.getZ() - self.andrew.getZ()) < 1):
                self.pandaStop[panda] = True
                self.gameOverTitle = addGameOverScreen()



        # save andrew's positions so that we can restore him,
        # in case he falls off the map or runs into something.
        self.andrewPositions.append(self.andrew.getPos())

        if len(self.andrewPositions) > 2:
            #We want the second to last position
            lastpos = self.andrewPositions[-2]
        else:
            lastpos = self.andrewPositions[-1]

        andrewZ = self.andrew.getZ()
        andrewY = self.andrew.getY()
        andrewX = self.andrew.getX()    

        lastZ = lastpos.getZ()
        lastY = lastpos.getY()
        lastX = lastpos.getX()

        # Get the time that elapsed since last frame.  We multiply this with
        # the desired speed in order to find out with which distance to move
        # in order to achieve that desired speed.
        dt = globalClock.getDt()

        # If the camera-left key is pressed, move camera left.
        # If the camera-right key is pressed, move camera right.

        if self.keyMap["cam-left"]:
            self.camera.setX(self.camera, -20 * dt)
        if self.keyMap["cam-right"]:
            self.camera.setX(self.camera, +20 * dt)

        # If a move-key is pressed, move andrew in the specified direction.

        if self.keyMap["left"]:
            self.andrew.setH(self.andrew.getH() + 300 * dt)
        if self.keyMap["right"]:
            self.andrew.setH(self.andrew.getH() - 300 * dt)
        if self.keyMap["forward"]:
            #I increased the speed to 40 from 25
            self.andrew.setY(self.andrew, -40 * dt)

            self.andrewMovePositions.append(self.andrew.getPos())

            #If andrew moves forward, recalculate the panda paths
            #once 100 new position shifts are made given
            #that andrew is not moving up or down
            if len(self.andrewMovePositions) % 100 == 0:
                for panda in self.pandas:
                    if (not self.andrewMovingZ()):
                        self.pandaStop[panda] = False
            #Get rid of the decoy after a certain number of moves
            if len(self.andrewMovePositions) % 300 == 0:
                self.decoy.setPos((18, -6, -10))
                self.decoyLocation = []

        # If andrew is moving, loop the run animation.
        # If he is standing still, stop the animation.

        if self.keyMap["forward"] or self.keyMap["left"] or self.keyMap["right"]:
            if self.isMoving is False:
                self.andrew.loop("run")
                self.isMoving = True
        else:
            if self.isMoving:
                self.andrew.stop()
                self.andrew.pose("walk", 5)
                self.isMoving = False

        # If the camera is too far from andrew, move it closer.
        # If the camera is too close to andrew, move it farther.

        camvec = self.andrew.getPos() - self.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if camdist > 10.0:
            self.camera.setPos(self.camera.getPos() + camvec * (camdist - 10))
            camdist = 10.0
        if camdist < 5.0:
            self.camera.setPos(self.camera.getPos() - camvec * (5 - camdist))
            camdist = 5.0

        # Normally, we would have to call traverse() to check for collisions.
        # However, the class ShowBase that we inherit from has a task to do
        # this for us, if we assign a CollisionTraverser to self.cTrav.
        #self.cTrav.traverse(render)

        # Adjust andrew's Z coordinate.  If andrew's ray hit terrain,
        # update his Z. If it hit anything else, or didn't hit anything, put
        # him back where he was last frame.

        entries = list(self.andrewGroundHandler.getEntries())
        entries.sort(key=lambda x: x.getSurfacePoint(render).getZ())

        if len(entries) > 0 and entries[0].getIntoNode().getName() == "terrain":
            self.andrew.setZ(entries[0].getSurfacePoint(render).getZ())
        
        else:
            self.andrew.setPos(lastpos)
        

        # Keep the camera at one foot above the terrain,
        # or two feet above andrew, whichever is greater.

        entries = list(self.camGroundHandler.getEntries())
        entries.sort(key=lambda x: x.getSurfacePoint(render).getZ())

        if len(entries) > 0 and entries[0].getIntoNode().getName() == "terrain":
            self.camera.setZ(entries[0].getSurfacePoint(render).getZ() + 1.0)
        if self.camera.getZ() < self.andrew.getZ() + 2.0:
            self.camera.setZ(self.andrew.getZ() + 2.0)


        # The camera should look in andrew's direction,
        # but it should also try to stay horizontal, so look at
        # a floater which hovers above andrew's head.
        self.camera.lookAt(self.floater)

        if (abs(self.crystal.getX() - self.andrew.getX()) < 0.6 and 
            abs(self.crystal.getY() - self.andrew.getY()) < 0.6 and abs(self.crystal.getZ() - self.andrew.getZ()) < 0.6):

            self.scoreTitle.destroy()

            #If we have superscoring turned on, we increase
            #our score significantly. This shows off
            #panda speed as well as the bfs algorithm
            if self.keyMap["super-score"]:
                self.score = (self.score + 1) * 5
            else:
                self.score += 1

            self.scoreTitle = addScore("Score: %d" %(self.score))
            self.andrew.setPos(self.startPos)
            self.pandaSpeed *= 1.5
            self.resetCrystal()

        return task.cont

    #Returns whether andrew is moving on the z axis 
    def andrewMovingZ(self):
        if len(self.andrewPositions) > 4:
            lastZ = self.andrewPositions[-4].getZ()
        else:
            lastZ = self.andrewPositions[-1].getZ()

        currZ = self.andrew.getZ()

        #andrew is moving on the Z axis if his currZ
        #and lastZ are different
        return not int(lastZ) == int(currZ)

    def setupCollision(self):

        cs = CollisionSphere(0, 0, 0, 1)
        cnodePath = self.andrew.attachNewNode(CollisionNode('cnode'))
        cnodePath.node().addSolid(cs)

        for wall in self.walls:
            ct = CollisionTube(0,-6,0, 0,6,0, 1.2)
            cn = wall.attachNewNode(CollisionNode('ocnode'))
            cn.node().addSolid(ct)

        self.cTrav = CollisionTraverser()
        self.andrewGroundRay = CollisionRay()
        self.andrewGroundRay.setOrigin(0, 0, 10)
        self.andrewGroundRay.setDirection(0, 0, -1)
        self.andrewGroundCol = CollisionNode('andrewRay')
        self.andrewGroundCol.addSolid(self.andrewGroundRay)
        self.andrewGroundCol.setFromCollideMask(CollideMask.bit(0))
        self.andrewGroundCol.setIntoCollideMask(CollideMask.allOff())
        self.andrewGroundColNp = self.andrew.attachNewNode(self.andrewGroundCol)
        self.andrewGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.andrewGroundColNp, self.andrewGroundHandler)

        #Uncomment THESE LINES to collide with the enemies
        
        pusher = CollisionHandlerPusher()
        pusher.addCollider(cnodePath, self.andrew)

        #self.cTrav = CollisionTraverser()
        self.cTrav.addCollider(cnodePath, pusher)
        #self.cTrav.showCollisions(render)
        
        self.camGroundRay = CollisionRay()
        self.camGroundRay.setOrigin(0, 0, 20)
        self.camGroundRay.setDirection(0, 0, -1)
        self.camGroundCol = CollisionNode('camRay')
        self.camGroundCol.addSolid(self.camGroundRay)
        self.camGroundCol.setFromCollideMask(CollideMask.bit(0))
        self.camGroundCol.setIntoCollideMask(CollideMask.allOff())
        self.camGroundColNp = self.camera.attachNewNode(self.camGroundCol)
        self.camGroundHandler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.camGroundColNp, self.camGroundHandler)

        # Uncomment this line to see the collision rays
        #self.andrewGroundColNp.show()
        #self.camGroundColNp.show()

        # Uncomment this line to show a visual representation of the
        # collisions occuring
        #self.cTrav.showCollisions(render)

    def resetCrystal(self):
        crystalPositions = self.possibleCrystalPositions
        crystalIndex = int(random.random() * (len(crystalPositions) - 1))
        crystalPosition = crystalPositions[crystalIndex]
        self.crystal.setPos(crystalPosition)

    def initMap(self):
        #Every story is a sheet of -1s which will later be overwritten
        #We want a grid of 0 lines on even floors so the panda can easily
        #backtrack through them
        for k in range(len(self.map)):
            self.map[k] = make2dList(len(self.map[0]), len(self.map[0][0]))
            for j in range(len(self.map[0])):
                for i in range(len(self.map[0][0])):
                    if((k % 2 == 0) and ((j % 12 == 0) or (i % 12 == 0))):
                        self.map[k][j][i] = 0
                        #perimeter of floor 0
                        
                        if (k == 0 and (j > 54 or j < 6 or i > 54 or i < 6)):
                            self.map[k][j][i] = -1
                        

                    elif((k % 2 == 1) and ((j % 12 == 0) and (i % 12 == 0))):
                        self.map[k][j][i] = 0

    def addWallsToMap(self):
        map = self.map

        for wall in self.walls:
            #The way we map the wall depends on its orientation
            if wall.getH() == 90:
                wallLength = 2 
                wallWidth = 12

            else:
                wallLength = 12
                wallWidth = 2

            wallRow = int(wall.getY() + self.yshift)
            wallCol = abs(int(wall.getX()) - self.xshift)
            wallHeight = int(wall.getZ())

            #Set the appropriate area around the wall's location to -1
            for length in range(wallRow - wallLength//2, wallRow + wallLength//2):
                for width in range(wallCol - wallWidth//2, wallCol + wallWidth//2):
                    map[wallHeight][length][width] = -1

    def updateMap(self, task):
        map = self.map

        if len(self.andrewPositions) > 4:
            #We want the fourth to last position
            lastpos = self.andrewPositions[-4]
        else:
            lastpos = self.andrewPositions[-1]

        andrewZ = self.andrew.getZ()
        andrewY = self.andrew.getY()
        andrewX = self.andrew.getX()    

        lastZ = lastpos.getZ()
        lastY = lastpos.getY()
        lastX = lastpos.getX()

        currHeight = int(andrewZ)
        currRow = int(andrewY + self.yshift)
        currCol = abs(int(andrewX)  - self.xshift)

        lastHeight = int(lastZ)
        lastRow = int(lastY + self.yshift)
        lastCol = abs(int(lastX) - self.xshift)

        closestZero = self.getClosestZeroPoint(self.andrew)
        zeroCol = closestZero[0]
        zeroRow = closestZero[1]
        zeroHeight = closestZero[2]
        
        #Put andrew at the closest zero point to him. This guarantees
        #that he will be in an easily locatable position
        if zeroHeight % 2 == 0 and (currRow != lastRow or currCol != lastCol or currHeight != lastHeight):
            map[zeroHeight][zeroRow][zeroCol] = 1

            #We have to make sure that we get rid of extraneous
            #ones that may slip through
            self.clearMapOfOnes((zeroCol, zeroRow, zeroHeight))    

        return task.cont

    #Returns the closest open space on the map so that
    #placement of andrew is easier
    def getClosestZeroPoint(self, actor):
        zeros = self.findZerosInMap()
        minDist = 10000000000
        minIndex = 100000
        currHeight = int(actor.getZ())
        currRow = int(actor.getY() + self.yshift)
        currCol = abs(int(actor.getX())  - self.xshift)

        for i in range(len(zeros)):
            zeroPos = zeros[i]
            zeroCol = zeroPos[0]
            zeroRow = zeroPos[1]
            zeroHeight = zeroPos[2]

            distance = math.sqrt((zeroRow - currRow)**2 + (zeroCol - currCol)**2)
            if distance < minDist and zeroHeight == currHeight:
                minDist = distance
                minIndex = i

        return zeros[minIndex]

    #Similar to getClosestZeroPoint(), except that it
    #returns the second closest zero. This is used for decoy placement
    def getSecondClosestZeroPoint(self, actor):
        zeros = self.findZerosInMap()
        minDist = 10000000000
        minIndices = []
        currHeight = int(actor.getZ())
        currRow = int(actor.getY() + self.yshift)
        currCol = abs(int(actor.getX())  - self.xshift)

        for i in range(len(zeros)):
            zeroPos = zeros[i]
            zeroCol = zeroPos[0]
            zeroRow = zeroPos[1]
            zeroHeight = zeroPos[2]

            distance = math.sqrt((zeroRow - currRow)**2 + (zeroCol - currCol)**2)
            if distance < minDist and zeroHeight == currHeight:
                minDist = distance
                minIndices.append(i)
        #The second to last index will give us the second closest zero
        return zeros[minIndices[-2]]

    #Returns the index of the 1 in the 3D map
    def findOneInMap(self):
        map = self.map
        oneIndex = "Not found"
        for k in range (len(map)):
            for j in range (len(map[0])):
                for i in range (len(map[0][0])):
                    if map[k][j][i] == 1:
                        oneIndex = (i, j, k)
        return oneIndex

    #Returns the indices of the zeroes in the map
    def findZerosInMap(self):
        map = self.map
        zeroIndices = []
        for k in range (len(map)):
            for j in range (len(map[0])):
                for i in range (len(map[0][0])):
                    if map[k][j][i] == 0:
                        zeroIndices.append((i, j, k))
        return zeroIndices

    #Clears the map of ones except for the current index
    #to insure that our tracking is clean
    def clearMapOfOnes(self, currentOneIndex):
        currOneX, currOneY, currOneZ = currentOneIndex

        #We must make sure that we do not
        #erase our decoy position
        if len(self.decoyLocation) > 0:
            decoyLocation = self.decoyLocation[0]
        else:
            decoyLocation = None

        map = self.map
        for k in range (len(map)):
            for j in range (len(map[0])):
                for i in range (len(map[0][0])):
                    if map[k][j][i] == 1 and (i, j, k) != currentOneIndex and (i, j, k) != decoyLocation:
                        map[k][j][i] = 0

        return True
        
    #In case the path contains any wierd zero moves,
    #we fix those here. I believe those occur because
    #of the cap on max depth in my backtracking
    def adjustBasicPath(self, basicPath):
        if basicPath == None:
            return None

        zeroMoveIndices = []
        zDestinationMet = False

        for element in basicPath:
            direction = element[0]
            magnitude = element[1]
            destination = element[2]

            #Get rid of any zero moves
            if magnitude == 0:
                basicPath.remove(element)

            elif direction == "Z":
                if zDestinationMet:
                    basicPath.remove(element)

                if destination == int(self.andrew.getZ()):
                    zDestinationMet = True
                

        return basicPath       

    #Uses recursive backtracking to find a path to the player
    #from a provided start point. The inspiration for
    #this implementation came from the maze solving example
    #in the 15-112 course notes
    def findPath(self, startPoint):
        placementList = self.map
        heights, rows, cols = len(placementList), len(placementList[0]), len(placementList[0][0])
        #The start point is in x, y, z notation
        startCol, startRow, startHeight  = startPoint[0], startPoint[1], startPoint[2]
        path = []
        visited = []

        def isLegal(height, row, col, dheight, drow, dcol):
            newHeight, newRow, newCol = height + dheight, row + drow, col + dcol

            #We don't want to take the path another enemy has already taken
            for existentPath in self.existentPaths:
                if containsPath(existentPath, path):
                    return False
            
            #We are legal if we are within bounds and not hitting a wall. 
            #Hitting the player is ok (and wanted)
            if (satisfies3DConstraints(placementList, newHeight, newRow, newCol) 
                and placementList[newHeight][newRow][newCol] != -1):
                return True
            return False

        def solve(height = startHeight, row = startRow, col = startCol, depth = 0):
            directions = self.directions
            #If we find the player
            if ((height, row, col) in path): return False

            path.append((height, row, col))

            #Don't think too hard
            if depth > 100:
                return False

            if (satisfies3DConstraints(placementList, height, row, col) 
                            and placementList[height][row][col] == 1):
                return True

            for dheight, drow, dcol in directions:
                if (isLegal(height, row, col, dheight, drow, dcol)):
                    #If we can make the next move, try to solve it
                    newHeight, newRow, newCol = height + dheight, row + drow, col + dcol

                    solution = solve(newHeight, newRow, newCol, depth + 1)
                    if (solution):
                        return solution
            #Move didn't work so remove it from path list
            path.remove((height, row, col))
            return False

        if solve():
            self.existentPaths.append(path)
            return path
        else:
            None

#Returns the multiple of 12 n is closest to
def nearest12(n):
    prelim = (n//12 * 12)
    diff = n - prelim

    if (diff >= 6):
        return n + (12 - diff)
    else:
        return n - diff

def make2dList(rows, cols): #Adapted from 15-112 course notes
    a=[]
    #We use -1's instead of 0's
    for row in range(rows): a += [[-1]*cols]
    return a

#A helper function based on make2dList that makes 3d lists
def make3dList(height, rows, cols):
    new2dList, new3dList = [], []
    for row in range (rows): new2dList.append([0] *cols)
    for h in range (height): new3dList.append(copy.deepcopy(new2dList))

    return new3dList

#Adapted from http://compsci.ca/v3/viewtopic.php?t=32571
def breadthFirstSearch(startPoint, placementList):
    x = startPoint[2]
    y = startPoint[1]
    z = startPoint[0]
    Map = copy.deepcopy(placementList)
    queue = deque( [(x,y,z,None)]) 
    while len(queue)>0:
        node = queue.popleft() 
        x = node[0] 
        y = node[1] 
        z = node[2]
        if  ((x < 0 or y < 0 or z < 0) or (x >= len(Map) 
            or y >= len(Map[0]) or z >= len(Map[0][0])) or Map[x][y][z] == -1): #restrictions
            continue
        if Map[x][y][z] == 1: 
            return GetPathFromNodes(node) 
        Map[x][y][z] = -1 
        for i in [[x-1,y, z],[x+1,y, z],[x,y-1, z],[x,y+1, z], [x, y, z-1], [x, y, z+1]]: 
            queue.append((i[0],i[1],i[2],node))
    return [] 

#Also adapted from http://compsci.ca/v3/viewtopic.php?t=32571
def GetPathFromNodes(node): 
    path = [] 
    while(node != None): 
        path.append((node[0],node[1], node[2])) 
        node = node[3] 
    return path

def containsPath(superPath, subPath):

    #We can't tell much from a small subPath
    if (len(subPath) < 10):
        return False
    if (subPath[0] in superPath):
        superStartIndex = superPath.index(subPath[0])
    else:
        return False

    #We loop through the subPath and see if we can trace
    #all of it inside of the superPath
    for i in range(len(subPath)):    
        if (superStartIndex + i >= len(superPath) or superPath[superStartIndex + i] != subPath[i]):
            return False
    return True

#A helper to calculate a simple representation of the path
def calculateBasicPath(path):
    #We get a none path if there is no way to
    #reach the 1 and an a size 1 path if we are already there
    if path == None or len(path)==1 or path == []:
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

#A simple helper function that sees if we are within 3D board bounds
def satisfies3DConstraints(board, height, row, col):
    heights, rows, cols = len(board), len(board[0]), len(board[0][0])
    if (height >= 0 and row >= 0 and col >= 0 
        and height < heights and row < rows and col < cols):
        return True
    else:
        return False

def playGame():
    demo = AnimatedAndrew()
    demo.run()


playGame()
