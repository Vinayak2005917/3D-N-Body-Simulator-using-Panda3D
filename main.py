from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import LineSegs, NodePath
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from panda3d.core import TransparencyAttrib
from panda3d.core import CardMaker, TextureStage, Loader
from panda3d.core import Vec3
import Object
import numpy as np

class Main(ShowBase):
    def __init__(self):
        super().__init__()
        self.font = self.loader.loadFont("Roboto-VariableFont_wdth,wght.ttf")

        # Set window properties
        props = WindowProperties()
        props.setSize(1280, 720)   # width x height
        props.setTitle("3D N Body Sim")
        self.win.requestProperties(props)
        self.is_dragging = False
        self.last_mouse_pos = None

        # Listen for mouse button events
        self.accept("mouse1", self.startDrag)   # left mouse down
        self.accept("mouse1-up", self.endDrag)  # left mouse up
        self.taskMgr.add(self.dragCamera, "dragCamera")
        self.accept("wheel_up", self.zoomIn)
        self.accept("wheel_down", self.zoomOut)
        self.setupCamera()

        #Objects
        self.objects = []

        # Earth
        self.earth = Object.Object3D(
            self, "models/earth.glb",
            position=(0, 0, 0),
            scale=1,
            rotation=(0, 90, 0),
            mass=25
        )
        self.objects.append(self.earth)

        # Moon (only this will move)
        self.moon = Object.Object3D(
            self, "models/moon.glb",
            position=(1500, 0, 0),
            scale=30,
            rotation=(0, 90, 0),
            velocity=(0, 1000, 0),
            mass=0.125
        )
        self.objects.append(self.moon)

        
        # Grid
        grid = self.make_grid(size=100000, step=100, z=0)
        grid.reparentTo(self.render)
        grid.setHpr(0, 0, 0)

        cam_pos = self.camera.getPos()
        self.posText = OnscreenText(
            text="",
            pos=(-1.7, -0.9),        # top-left corner
            scale=0.06,
            fg=(1, 1, 1, 1),        # white text
            align=TextNode.ALeft,
            font=self.font,  
            mayChange=True
        )

        # Add update task
        self.taskMgr.add(self.update_physics, "physicsTask")
        self.taskMgr.add(self.updateCamera, "updateCamera")
        self.taskMgr.add(self.updateUI, "updateUI")
    
#--------------------------Physics----------------------------------

    def update_physics(self, task):
        """Update physics for all objects applying gravity on each other."""
        dt = task.dt * 15

        for i in self.objects:
            for j in self.objects:
                if i != j:
                    i.apply_gravity_from(j, dt)
        
        return task.cont

#--------------------------Grid----------------------------------
        
    def make_grid(self, size=1000, step=100, z=0):
        ls = LineSegs()

        # --- Grid lines ---
        ls.setColor(0.5, 0.5, 0.5, 1)  # gray
        for x in range(-size, size + 1, step):
            ls.moveTo(x, -size, z)
            ls.drawTo(x, size, z)

        for y in range(-size, size + 1, step):
            ls.moveTo(-size, y, z)
            ls.drawTo(size, y, z)

        node = ls.create()
        return NodePath(node)
    
#--------------------------Camera----------------------------------

    def setupCamera(self):
        self.disableMouse()
        self.camera.setPos(0, -2500, 1000)
        self.camera.lookAt(0, 0, 0)

    def updateCamera(self, task):
        dt = task.dt
        speed = 350000

        # get camera forward/right vectors
        cam_forward = self.camera.getQuat(self.render).getForward()
        cam_forward.setZ(0)  # flatten to horizontal plane
        cam_forward.normalize()

        cam_right = self.camera.getQuat(self.render).getRight()
        cam_right.setZ(0)
        cam_right.normalize()

        move_vec = Vec3(0, 0, 0)

        if self.mouseWatcherNode.is_button_down('w'):
            move_vec += cam_forward
        if self.mouseWatcherNode.is_button_down('s'):
            move_vec -= cam_forward
        if self.mouseWatcherNode.is_button_down('a'):
            move_vec -= cam_right
        if self.mouseWatcherNode.is_button_down('d'):
            move_vec += cam_right

        if move_vec.length() > 0:
            move_vec.normalize()
            self.camera.setPos(self.camera.getPos() + move_vec * speed * dt)

        # Space/Shift = vertical
        if self.mouseWatcherNode.is_button_down('space'):
            self.camera.setZ(self.camera.getZ() + speed * dt)
        if self.mouseWatcherNode.is_button_down('shift'):
            self.camera.setZ(self.camera.getZ() - speed * dt)

        return task.cont

    def startDrag(self):
        self.is_dragging = True
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.last_mouse_pos = (mpos.getX(), mpos.getY())

    def endDrag(self):
        self.is_dragging = False
        self.last_mouse_pos = None

    def dragCamera(self, task):
        if self.is_dragging and self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            x, y = mpos.getX(), mpos.getY()

            if self.last_mouse_pos:
                dx = x - self.last_mouse_pos[0]
                dy = y - self.last_mouse_pos[1]

                # Adjust sensitivity
                sensitivity = 100

                # Rotate camera
                self.camera.setH(self.camera.getH() - dx * sensitivity)
                self.camera.setP(self.camera.getP() + dy * sensitivity)

            self.last_mouse_pos = (x, y)

        return task.cont

    def zoomIn(self):
        # move camera forward along its look direction
        self.camera.setPos(self.camera, Vec3(0, 100, 0))  

    def zoomOut(self):
        # move camera backward along its look direction
        self.camera.setPos(self.camera, Vec3(0, -100, 0))

    def updateUI(self, task):
        pos = self.camera.getPos()
        self.posText.setText(f" X= {pos.x:.2f}, Y= {pos.y:.2f}, Z= {pos.z:.2f}")
        return task.cont
    

main = Main()
main.run()
