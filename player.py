#======================================================================#
#
# Team:  Hunter Quant
#        Edward Pryor
#        Nick marasco
#        Shane Peterson
#        Brandon Williams
#        Jeremy Rose
#
# Last modification: 10/15/14
#
# Description: Player class
# Designed to hold all information about the player.
# Instantiates controls from here by calling to the camMov class.
# Once we have more interesting data about players, it will go here
#
#======================================================================#

from camMov import CameraMovement
from weapons import *

from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.gui.DirectGui import *
from panda3d.core import CollisionNode, CollisionSphere, CollisionRay, CollisionHandlerGravity, CardMaker
from panda3d.core import NodePath, BitMask32, TransparencyAttrib, Filename, TextNode
from direct.showbase.DirectObject import DirectObject
class Player(DirectObject):
    
    #using this to be our player
    #define tehings like health in here
    #have to tie the camera to this
    #game manager ->player ->camera as far as instantiating goes
    
    def __init__(self):
        self.red = 0
        self.green = 1
        self.blue = 1
        self.oRed = 0
        self.oGreen = 1
        self.oBlue = 1

        self.overHeat = 0
        self.overHeatCount = .1
        self.isOverHeated = False
        base.taskMgr.add(self.overHeatTask, "overHeatTask")
        
        self.down = True
        self.playerNode = NodePath('player')
        self.playerNode.reparentTo(render)
        self.playerNode.setPos(0,-30,30)
        
        self.playerNode.setScale(1.0)
        self.cameraModel = loader.loadModel("./resources/player")
        self.cameraModel.reparentTo(self.playerNode)
        #cameraModel.hide()
        self.cameraModel.setPos(0,0,2)
        self.rRifle = RecursionRifle(base.camera, len(base.projectileList))
        self.mhBlunder = MHB(base.camera, len(base.projectileList))
        self.kvDuals = KeyValue(base.camera, len(base.projectileList))
        #Weapons
        self.overheat = 0
        self.weaponMap = {1:self.rRifle, 2:self.mhBlunder, 3:self.kvDuals}
        self.weaponNameMap = {1:"./resources/rrName.png", 2:"./resources/mhbName.png", 3:"./resources/kvdName.png"}
        self.curWeapon = 1
        
        #Load all images in so it doesn't stutter on swap
        self.weaponName = OnscreenImage(self.weaponNameMap[3])
        self.weaponName.setTransparency(True)
        self.weaponName.setImage(self.weaponNameMap[2])
        self.weaponName.setTransparency(True)
        self.weaponName.setImage(self.weaponNameMap[1])
        self.weaponName.setTransparency(True)
        self.weaponName.reparentTo(render2d)
        
        self.mhBlunder.hide()
        self.kvDuals.hide()
        self.accept("mouse1", self.fireWeapon)
        self.accept("mouse3", self.swapWeapon)
        
        #HUD
        hud = OnscreenImage("resources/hud.png")
        hud.setTransparency(True)
        hud.reparentTo(render2d)
        base.taskMgr.add(self.updateUsage, "usagePaint", taskChain='Gametasks')
        base.taskMgr.add(self.hFlicker, "hflicker", taskChain='GameTasks')
        base.taskMgr.add(self.updateCount, "Ecount", taskChain='GameTasks')
        base.taskMgr.add(CameraMovement(self.cameraModel).cameraControl, "cameraControl", taskChain='GameTasks')
        self.createColision()
        
        # define player health here
        # try not to re-create the player object, will alter reset these values
        # alernatively, dump player stats off in save file before recreating
        self.maxEnergy = 100
        self.curEnergy = self.maxEnergy
        self.accept("cnode", self.hit)
        
        #set up on screen health bar
        font = loader.loadFont("./resources/ni7seg.ttf")
        self.healthLable = TextNode('health field name')
        self.healthLable.setFont(font)
        self.healthLable.setText("Abstraction")
        textNodePath = aspect2d.attachNewNode(self.healthLable)
        textNodePath.setScale(0.05)
        self.healthLable.setAlign(TextNode.ACenter)
        textNodePath.setPos(0, 0, .68)
        self.healthLable.setTextColor(self.red, self.green, self.blue, 1)

        self.enemiesLeft = TextNode('monsters to kill')
        self.enemiesLeft.setFont(font)
        self.enemiesLeft.setText(str(len(base.enemyList)))
        texnp = aspect2d.attachNewNode(self.enemiesLeft)
        texnp.setScale(.1)
        texnp.setPos(hud, 0, 0, 0)
        self.enemiesLeft.setTextColor(1, 1, 0, 1)
        

        # usage bar
        self.bar = DirectWaitBar(text = "", value = self.curEnergy, range = self.maxEnergy, pos = (0,.4,.95), barColor = (self.red, self.green, self.blue, 1))
        self.bar.setScale(0.5)
        self.usageBar = DirectWaitBar(text = "", value = self.overHeat, range = 100,  pos = (1.25, -.4, -.95), barColor =(1, 0, 0,1))
        self.usageBar.setScale(0.5)
        # weapon name 

	#Kill Floor task
	base.taskMgr.add(self.killFloor, "Kill Floor") 

    def hit(self, damage):
        self.curEnergy = self.curEnergy-damage
        self.bar['value'] = self.curEnergy
        print "Player Health:",self.curEnergy
        if self.curEnergy <=0:
            
            base.fsm.request('GameOver', 1)

    # set the player health to a specific value        
    def adjustHealth(self, value):
        self.curEnergy = value
        self.bar['value'] = self.curEnergy

    def updateCount(self, task):
        self.enemiesLeft.setText(str(len(base.enemyList)))
        return task.cont 
    def updateUsage(self, task):
        if self.curEnergy > 0:
            if self.overHeat < 50:
                self.usageBar['barColor'] = (.2, 1, .5, 1)
            elif self.overHeat >=50 and self.overHeat <70:
                self.usageBar['barColor'] = (1, 1, .2, 1)
            elif self.overHeat >= 70:
                self.usageBar['barColor'] = (1, 0, 0, 1)
            self.usageBar['value'] = self.overHeat
            if self.isOverHeated:
                self.usageBar['barColor'] = (1, 0, 0, 1)
            
        return task.cont

    def swapWeapon(self): 
        # ignore this print. using it to gather data about the size of the debug room
        print self.playerNode.getPos()
        self.weaponMap[self.curWeapon].resetWeapon
        if  self.curWeapon == 1:
            
            self.weaponName.setImage(self.weaponNameMap[2])
            self.weaponName.setTransparency(True)
            self.weaponMap[1].reticle.setScale(0)
            self.weaponMap[1].curScale = 0
            self.weaponMap[1].step = False
          
            self.rRifle.hide()
            self.mhBlunder.show()
            
            self.curWeapon = 2
            self.weaponMap[2].reticle.setScale(.075)
            self.weaponMap[2].curScale = .075
        elif self.curWeapon == 2:
            
            self.weaponName.setImage(self.weaponNameMap[3])
            self.weaponName.setTransparency(True)
            self.weaponMap[2].reticle.setScale(0)
            self.weaponMap[2].curScale = 0
            self.weaponMap[2].step = False
            
            self.mhBlunder.hide()
            self.kvDuals.show()
            
            self.curWeapon = 3
            self.weaponMap[3].reticle.setScale(.025)
            self.weaponMap[3].curScale = .025
        elif self.curWeapon == 3:

            self.weaponName.setImage(self.weaponNameMap[1])
            self.weaponName.setTransparency(True)
            self.weaponMap[3].reticle.setScale(0)
            self.weaponMap[3].curScale = 0
            self.weaponMap[3].step = False
            
            self.kvDuals.hide()
            self.rRifle.show()
           
            self.curWeapon = 1
            self.weaponMap[1].reticle.setScale(.025)
            self.weaponMap[1].curScale = .025
         
        base.taskMgr.remove("weaponDelay")
    
    def fireWeapon(self):

        if base.taskMgr.hasTaskNamed("weaponDelay") == False:

            if not self.isOverHeated:

                base.taskMgr.add(self.weaponMap[self.curWeapon].fire, "fire")

        elif self.weaponMap[self.curWeapon].canShoot() == True:

            if not self.isOverHeated:
                
                base.taskMgr.remove("weaponDelay")
                base.taskMgr.add(self.weaponMap[self.curWeapon].fire, "fire")
        else:

            print "Can't Shoot"

    def overHeatTask(self, task):
        
        self.overHeat -= self.overHeatCount
        if self.overHeat >= 100:
            
            self.overHeatCount = .5
            self.isOverHeated = True
        elif self.overHeat < 0:
            
            self.overHeatCount = .1
            self.overHeat = 0
            self.isOverHeated = False

        return task.cont


    def createColision(self):
        
        # Set up floor collision handler
        base.floor = CollisionHandlerGravity()
        base.floor.setGravity(9.8)

        # Create player collision node and add to traverser
        playerCollNodePath = self.initCollisionSphere(self.playerNode.getChild(0))
        base.cTrav.addCollider(playerCollNodePath, base.pusher)
        base.pusher.addCollider(playerCollNodePath, self.playerNode)
        
        # Create Floor Ray - for gravity / floor
        floorCollRayPath = self.initCollisionRay(1,-1) 
        base.floor.addCollider(floorCollRayPath, self.playerNode)
        base.cTrav.addCollider(floorCollRayPath, base.floor)
        floorCollRayPath.reparentTo(self.cameraModel)

    def initCollisionSphere(self, obj):
        
        # Create sphere and attach to player
        cNode = CollisionNode('player')

        cs = CollisionSphere(0, 0, 4, 2)
        cNodePath = obj.attachNewNode(CollisionNode('cnode'))
        cNodePath.node().addSolid(cs)
        cNodePath.show()
        
        return cNodePath

    def initCollisionRay(self, originZ, dirZ):
        ray = CollisionRay(0,0,originZ,0,0,dirZ)
        collNode = CollisionNode('playerRay')
        collNode.addSolid(ray)
        collNode.setFromCollideMask(BitMask32.bit(1))
        collNode.setIntoCollideMask(BitMask32.allOff())
        collRayNP = self.playerNode.attachNewNode(collNode)
        collRayNP.show()
        return collRayNP

    # call this method when collide with a health upgrade
    def energyUpgrade(self):
        self.maxEnergy +=100
        self.curEnergy = self.maxEnergy

    def killFloor(self, task):

	    z = int(self.playerNode.getPos()[2])

	    if(z < -7):
		    self.playerNode.setPos(0, 0, 6) #resets height
		    self.cameraModel.setPos(base.xPos, base.yPos, base.zPos) #resets position
		    self.hit(10)
	    return task.cont

    def hFlicker(self, task):
        if self.curEnergy <=30:
            if self.down:
                self.red = self.red+0.1
                self.blue = self.blue-.01
                self.green = self.green-.01
            else:
                self.red = self.red-0.1
                self.blue = self.green+0.1
                self.green = self.green+0.1
        else:
            self.red = self.oRed
            self.blue = self.oBlue
            self.green = self.oGreen
        if self.red >=1:
            self.down = False
        if self.red <=0:
            self.down = True
        self.healthLable.setTextColor(self.red, self.green, self.blue, 1)
        self.bar['barColor']=(self.red, self.green, self.blue, 1)
        return task.cont
        
    def resetEnergy(self):
        self.curEnergy = self.maxEnergy
        self.adjustHealth(self.curEnergy)
        

                
