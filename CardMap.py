from direct.showbase import DirectObject
from direct.showbase.DirectObject import DirectObject
from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import *
from direct.task import Task
from TimCam import TimCam
from pandac.PandaModules import TransparencyAttrib
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.interval.IntervalGlobal import *

import xml.etree.ElementTree as xml
from xml.dom import minidom
import Image

import sys
import math
import string

#import direct.directbase.DirectStart
from pandac.PandaModules import GeomVertexFormat, GeomVertexData, GeomVertexWriter, GeomTriangles, Geom, GeomNode, NodePath, GeomPoints

class StrategyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        base.disableMouse()

        self.map_scale = 1
        wp = WindowProperties()
        wp.setFullscreen(True)

        self.win_width = 1920
        self.win_height = 1080
        wp.setSize(self.win_width, self.win_height)
        base.win.requestProperties(wp)

        self.msg = []
        self.msg_path = []
        self.msg_y = []
        self.msg_alpha = []
        self.msg_delay = 3.0
        self.msg_fadetime = 5.0
        self.pickingEnabledObject = None
        self.prov_selected = -1

        self.scenario = "scenarios/wellington/wellington_wars.xml"
        loading_screen = "textures/loading.jpg"
        self.load_image = OnscreenImage(image = loading_screen, scale = (1920.0/1080.0,1,1))
        self.load_text = OnscreenText(text="Initialising...", pos = (0,-0.45,0))
        self.load_state = "Initialisation..."
        #self.load_state = "Done!"

        taskMgr.add(self.task_loading,"LoadingTask")
        taskMgr.doMethodLater(1.0,self.xml_scen_load,"xmlload")

        self.cam = TimCam()

        self.mess_count = 0
        self.accept("space", self.messaging)


        #self.message_create("Howdy")
        taskMgr.add(self.task_messages,"MessagesTask")

    def init_collisions(self):
        base.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerEvent()

        pickerNode = CollisionNode("mouseRayNode")
        pickerNPos = base.camera.attachNewNode(pickerNode)
        self.pickerRay = CollisionRay()
        pickerNode.addSolid(self.pickerRay)

        pickerNode.setTag("rays","ray1")
        base.cTrav.addCollider(pickerNPos, self.cHandler)

        self.cHandler.addInPattern("%(rays)ft-into-%(prov)it")
        self.cHandler.addOutPattern("%(rays)ft-out-%(prov)it")

        self.cHandler.addAgainPattern("ray_again_all%(""rays"")fh%(""prov"")ih")

        self.DO=DirectObject()

        self.DO.accept('ray1-into-city', self.collideInBuilding)
        self.DO.accept('ray1-out-city', self.collideOutBuilding)

        self.DO.accept('ray_again_all', self.collideAgainstBuilds)

        self.pickingEnabledOject=None

        self.DO.accept('mouse1', self.mouseClick, ["down"])
        self.DO.accept('mouse1-up', self.mouseClick, ["up"])

        taskMgr.add(self.rayUpdate, "updatePicker")

    def collideInBuilding(self,entry):
        np_into=entry.getIntoNodePath()
        np_into.getParent().setColor(.6,.5,1.0,1)

    def collideOutBuilding(self,entry):

        np_into=entry.getIntoNodePath()
        np_into.getParent().setColor(1.0,1.0,1.0,1)

        self.pickingEnabledObject = None

    def collideAgainstBuilds(self,entry):
        if entry.getIntoNodePath().getParent() <> self.pickingEnabledOject:
            np_from=entry.getFromNodePath()
            np_into=entry.getIntoNodePath()

            self.pickingEnabledObject = np_into.getParent()

    def mouseClick(self,status):
        if self.pickingEnabledObject:
            if status == "down":
                self.pickingEnabledObject.setScale(0.95*2)
                self.prov_selected = int(self.pickingEnabledObject.getTag("id"))
                self.message_create("You clicked on "+self.provinces[int(self.pickingEnabledObject.getTag("id"))][0])
                self.interface_update()

            if status == "up":
                self.pickingEnabledObject.setScale(1.0*2)
        elif self.pickingEnabledObject == None:
            self.prov_selected = -1
            self.interface_update()

    def rayUpdate(self,task):
        if base.mouseWatcherNode.hasMouse():
            mpos = base.mouseWatcherNode.getMouse()

            self.pickerRay.setFromLens(base.camNode, mpos.getX(),mpos.getY())
        return task.cont

    def interface_update(self):
        if self.prov_selected != -1:
            texture = loader.loadTexture("textures/interface_prov.png")
            self.interface_card.setTexture(texture)
            self.lbl_prov_name.setText(self.provinces[self.prov_selected][0])
            if self.provinces[self.prov_selected][4] != None:
                self.inter_img.setTexture(self.provinces[self.prov_selected][4])
            else:
                texture = loader.loadTexture("textures/planet.jpg")
                self.inter_img.setTexture(texture)
            self.inter_img.show()
        else:
            texture = loader.loadTexture("textures/interface_background.png")
            self.interface_card.setTexture(texture)
            self.lbl_prov_name.setText("")
            texture = loader.loadTexture("textures/planet.jpg")
            self.inter_img.setTexture(texture)
            self.inter_img.hide()



    def interface_draw(self):
        interface_scale = 2
        self.interface_card = self.draw_card_pixel("textures/interface_background.png",
                                                   (self.win_width)/2-(250*interface_scale),self.win_height-(128*interface_scale),
                                                   500*interface_scale,128*interface_scale)
        self.lbl_prov_name = self.label_create("",(1,1,1,1),
                                               (self.win_width)/2-((250-20)*interface_scale),
                                               self.win_height-((128-24)*interface_scale),10*interface_scale)
        self.inter_img = self.draw_card_pixel("textures/planet.jpg",(self.win_width)/2-((250-20)*interface_scale),
                                              self.win_height-((128-37)*interface_scale),
                                              76*interface_scale,76*interface_scale)
        self.inter_img.hide()

    def label_create(self,text,colour,x,y,scale):
        text_node = TextNode("MessageNode")
        text_node.setText(text)
        text_node_path = pixel2d.attachNewNode(text_node)
        text_node_path.setPos(x,0,-y)
        text_node_path.setScale(scale)
        text_node.setTextColor(colour)
        text_node.setAlign(TextNode.ALeft)
        return text_node

    def messaging(self):
        if self.mess_count < len(self.message_list):
            self.message_create(self.message_list[self.mess_count])
            self.mess_count += 1
        else:
            self.message_create(self.message_list[len(self.message_list)-1])
            self.mess_count = 0

    def task_loading(self,task):
        self.load_text.setText(self.load_state)
        if self.load_state == "Done!":
            self.interface_draw()
            self.message_list = []
            for p in range(len(self.provinces)):
                self.message_list.append(self.provinces[p+1][0]+" has been invaded by the enemy!")
            for m in range(len(self.message_list)):
                self.message_create(self.message_list[m])
            self.load_image.destroy()
            self.load_text.destroy()
            return task.done
        else:
            return task.cont

    def task_messages(self,task):
        task.delayTime = 1.0
        for m in range(len(self.msg_path)):
            if self.msg_path[m].getColorScale() == VBase4(1,1,1,0):
                # FIND A WAY TO KILL self.msg[m]
                # FIND A WAY TO KILL self.msg_path[m]
                self.msg_path.remove(self.msg_path[m])
                self.msg.remove(self.msg[m])
                self.msg_y.remove(self.msg_y[m])
                return task.cont
        return task.again



    def draw_card(self,renderer,pLL,pLR,pUR,pUL):
        cm = CardMaker("CardMaker")
        cm.setFrame(pLL,pLR,pUR,pUL)
        card = renderer.attachNewNode(cm.generate())
        card.clearColor()
        return (card)

    def draw_card_pixel(self,tex,x,y,width,height):
        cm = CardMaker("CardMaker")
        cm.setFrame(0,width,-height,0)
        card = pixel2d.attachNewNode(cm.generate())
        card.setTransparency(TransparencyAttrib.MAlpha)
        card.clearColor()
        texture = loader.loadTexture(tex)
        card.setTexture(texture)
        card.setPos(x,0,-y)
        return (card)

    def map_create(self,task):
        im = Image.open(self.map_region)
        pix = im.load()
        print im.getcolors()
        width,height = im.size
        aspect = width/height
        print width,height,aspect
        width *= self.map_scale
        height *= self.map_scale

        map = self.draw_card(render,(width/2,height/2,0),(-width/2,height/2,0),(-width/2,-height/2,0),(width/2,-height/2,0))
        map.setHpr(180,0,0)
        map.setTransparency(TransparencyAttrib.MAlpha)

        tex = loader.loadTexture(self.map_texture)
        map.setTexture(tex)

        z=1
        reg = self.draw_card(render,(width/2,height/2,z),(-width/2,height/2,z),(-width/2,-height/2,z),(width/2,-height/2,z))
        reg.setHpr(180,0,0)
        reg.setTransparency(TransparencyAttrib.MAlpha)

        size = width,height
        self.nat_map = Image.new("RGBA",size,(255,255,255,0))
        self.nat_map_pix = self.nat_map.load()
        #for x in range(width):
        #    for y in range(height):
        #        if pix[x,y][3] != 0 and pix[x,y] != (0,0,0,255):
        #            prov_from_col = self.get_prov_from_col(pix[x,y])
        #            self.nat_map_pix[x,y] = self.get_col_from_rgb(self.nations[self.provinces[prov_from_col][7]][1])
        self.nat_map.save("nat_map.png","PNG")

        tex_reg = loader.loadTexture("nat_map.png")
        reg.setTexture(tex_reg)
        reg.setAlphaScale(0.3)

        self.map_width = width
        self.map_height = height

        self.load_state = "Populating World..."
        taskMgr.doMethodLater(1.0,self.map_populate,"mappop")

        return task.done

    def get_col_from_rgb(self,rgb):
        col = string.split(rgb)
        return (int(col[0]),int(col[1]),int(col[2]),255)

    def get_prov_from_col(self,colour):
        found = False
        for p in range(len(self.provinces)):
            if self.get_col_from_rgb(self.provinces[p+1][1]) == colour:
                found = True
                return p+1
        if found == False:
            print "##ERROR FINDING PROV FROM COL "+str(colour)+"##"

    def map_populate(self,task):
        self.init_collisions()
        for p in range(len(self.provinces)):
            city = loader.loadModel("models/house2.x")
            city.reparentTo(render)
            city.setName(self.provinces[p+1][0])
            city.setScale(2, 2, 2)
            x = float(self.provinces[p+1][2]*self.map_scale)-(self.map_width/2)
            y = self.map_height-float(self.provinces[p+1][3]*self.map_scale)-(self.map_height/2)
            city.setPos(x, y, 1.0)
            city_col = city.attachNewNode(CollisionNode("CityCNode%d"%p))
            city_col.setScale((3,3,3))
            city_col.node().addSolid(CollisionSphere(0,0,0,1))
            city_col.setTag("prov","city")
            city.setTag("id",str(p+1))
        for p in range(len(self.paths)):
            path_split = string.replace(self.paths[p],"-"," ")
            path_split = string.split(path_split)
            prov_a = int(path_split[0])
            prov_b = int(path_split[1])
            line = LineSegs()
            line.setColor(1, 0, 0, 1)
            line.setThickness(5)
            line.moveTo(self.provinces[prov_a][2]-600, -(self.provinces[prov_a][3])+350, 2)
            line.drawTo(self.provinces[prov_b][2]-600, -(self.provinces[prov_b][3])+350, 2)

            node = line.create()
            node_path = NodePath(node)
            node_path.reparentTo(render)
            print "line drawn",self.provinces[prov_a][2],self.provinces[prov_a][3]
        for a in range(len(self.armies)):
            self.army_create(a+1,self.armies[a+1][2])

        self.load_state = "Done!"
        task.done

    def army_create(self,army_id,location):
        #self.provinces[location][8].append(army_id)
        x = float(self.provinces[location][2]*self.map_scale)-(self.map_width/2)
        y = self.map_height-float(self.provinces[location][3]*self.map_scale)-(self.map_height/2)
        army = loader.loadModel("models/man.x")
        army.reparentTo(render)
        army.setName(self.armies[army_id][0])
        army.setPos(x, y, 1.0)

    def message_create(self,text):
        msg_height = 17

        text_node = TextNode("MessageNode")
        text_node.setText(text)
        text_node_path = pixel2d.attachNewNode(text_node)
        text_node_path.setPos(0,0,-msg_height)
        text_node_path.setScale(15)
        text_node.setTextColor(0.8, 0.1, 0.1, 1)
        text_node.setAlign(TextNode.ALeft)

        for m in range(len(self.msg)):
                self.msg_y[m] -= msg_height
                self.msg_path[m].setPos(0,0,self.msg_y[m])
        self.msg.insert(0,text_node)
        self.msg_path.insert(0,text_node_path)
        self.msg_y.insert(0,-msg_height)

        fadeOut = LerpColorScaleInterval(text_node_path, self.msg_fadetime, VBase4(1,1,1,0), VBase4(1,1,1,1))
        para = Sequence(Wait(self.msg_delay), fadeOut)
        para.start()

    def xml_scen_load(self,task):
        tree = xml.parse(self.scenario)
        root = tree.getroot()

        self.map_region = root.attrib["region_map"]
        self.map_texture = root.attrib["texture_map"]

        self.day = (int(root.find("date/day").text))
        self.month = (int(root.find("date/month").text))
        self.year = (int(root.find("date/year").text))

        self.provinces = {}
        self.nations = {}
        self.armies = {}
        self.paths = []
        for p in root.findall("province"):
            if (p.find("image") != None):
                self.provinces[int(p.attrib["id"])] = [p.find("name").text,p.find("rgb").text,int(p.find("x").text),int(p.find("y").text),
                                                       loader.loadTexture(p.find("image").text),float(p.find("coin").text),float(p.find("men").text),int(p.attrib["owner"]),[]]
            else:
                self.provinces[int(p.attrib["id"])] = [p.find("name").text,p.find("rgb").text,int(p.find("x").text),int(p.find("y").text),
                                                       None,float(p.find("coin").text),float(p.find("men").text),int(p.attrib["owner"]),[]]
        print self.provinces

        for n in root.findall("nation"):
            if (n.find("flag") != None):
                self.nations[int(n.attrib["id"])] = [n.find("name").text,n.find("rgb").text,int(n.find("capital").text),int(n.find("coin").text),int(n.find("men").text),[],
                                                       loader.loadTexture(n.find("flag").text)]
            else:
                self.nations[int(n.attrib["id"])] = [n.find("name").text,n.find("rgb").text,int(n.find("capital").text),int(n.find("coin").text),int(n.find("men").text),[],
                                                       None]
        print self.nations

        for a in root.findall("army"):            #0:Name 1:Home 2:Location 3:Inf 4:Arch 5:Cav 6:x 7:y
            self.armies[int(a.attrib["id"])] = [a.find("name").text,int(a.find("home").text),int(a.find("location").text),
                                                int(a.find("infantry").text),int(a.find("archers").text),int(a.find("cavalry").text),"node"]
        print self.armies

        for pth in root.findall("paths/path"):
            self.paths.append(pth.attrib["name"])
        print self.paths

        im = Image.open(self.map_region)
        self.region_pix = im.load()
        self.region_width,self.region_height = im.size

        self.load_state = "Creating World..."
        #self.load_state = "Done!"
        taskMgr.doMethodLater(1.0,self.map_create,"mapcreate")
        task.done

app = StrategyGame()
app.setFrameRateMeter(True)
app.run()