Name: Daniel Barychev
Andrew Id: dbaryche
Section: D

MAIN CITATIONS:
I would like to cite the Roaming Ralph Demo from the Panda3D samples (https://www.panda3d.org/manual/index.php/Sample_Programs:_Roaming_Ralph). This is the main code that I have built my world overtop of.
I sourced the Ralph model from the demo above, the panda model from the general Panda3D models
with which the module is packaged. The crystal model and decoy model come from the Panda3D art package and specifically, BVW at CMU.

The Breadth First Search algorithm is adapted from here (http://compsci.ca/v3/viewtopic.php?t=32571)

I created the floor, wall, ramp, and sky models in Blender.

TO INSTALL AND RUN:
This project runs using the Panda3D module. To run it, one must install the Panda3D Runtime or SDK (https://www.panda3d.org/download.php)
and run the main.py file using ppython as such "ppython main.py"

GENERAL PROJECT DISCRIPTION:
Animated Andrew is a 3D game made using Panda3D in which you play as Andrew, a boy stuck in a maze that is trying to get as many crystals as possible before a panda gets him. He has the option to use decoys, but those time out and the pandas get smarter and faster as the score goes up. 

The project is an experiment in the 3D implementation of recursive backtracking and breadth first search. I wanted to be able to dynamically use these algorithms to locate the player in 3D space and have the enemies work together to get him/her. Specifically, when the score is below 3, the pandas use backtracking since this provides less of a direct path. Above 3, the pandas switch over to breadth first search, finding the player much more quickly.

NOTES ON STYLE:
My test functions were built and used in the tester.py file. It was impractical to try and make them in the main.py file since data changes so frequently there. Thus, when testing things outside of the tester.py file, I simply used print statements in the mileu of my existing functions. In addition, there are some methods which are quite large. These are necessary since all of the movement code is best kept together for clarity. The roaming ralph demo does it this way, and I mimicked it. Other functions that I wrote all comply with 112 length standards. 

