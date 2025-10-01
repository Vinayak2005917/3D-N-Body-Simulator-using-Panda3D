from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import LineSegs, NodePath
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TextNode
from panda3d.core import TransparencyAttrib
from panda3d.core import CardMaker, TextureStage, Loader
from direct.gui.DirectGui import DirectButton
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
        self.setBackgroundColor(0, 0, 0)

        #constants
        self.speed_factor = 1
        self.start_cords = (0, -10000, 4000)
        self.dt = 0.01
        self.grid_visible = True
        self.grid_node = None

        # Listen for mouse button events
        self.accept("mouse1", self.startDrag)   # left mouse down
        self.accept("mouse1-up", self.endDrag)  # left mouse up
        self.taskMgr.add(self.dragCamera, "dragCamera")
        self.accept("wheel_up", self.zoomIn)
        self.accept("wheel_down", self.zoomOut)
        self.setupCamera()

        #Objects
        self.objects = []
        '''
        # Sun
        self.sun = Object.Object3D(
            self, "models/sun.glb",
            position=(0,0,0),
            scale=25,
            rotation=(0, 90, 0),
            mass=1500
        )
        self.objects.append(self.sun)
        # Earth
        self.earth = Object.Object3D(
            self, "models/earth.glb",
            position=(4000, 0, 0),
            scale=1,
            rotation=(0, 90, 0),
            velocity=(0, 1500, 0),
            mass=10
        )
        self.objects.append(self.earth)
        '''
  
        # Grid
        if self.grid_visible:
            self.grid_node = self.make_grid(size=100000, step=100, z=0)
            self.grid_node.setName("grid")
            self.grid_node.reparentTo(self.render)
            self.grid_node.setHpr(0, 0, 0)

        # UI Text

        # Controls
        self.controlsText = OnscreenText(
            text="W,S,A,D = Move, Space/Shift = Up/Down, Mouse Drag = Rotate, Scroll = Zoom",
            pos=(-1.1, 0.9),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=self.font,
        )
        # stats
        self.statsText = OnscreenText(
            text=f"dt = {self.dt}\nSpeed = {self.speed_factor}X\nIntegrator = RK4",
            pos=(1.3, -0.8),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=self.font,  
            mayChange=True
        )
        # Camera Position
        self.CameraPosText = OnscreenText(
            text="",
            pos=(-1.7, -0.9),
            scale=0.06,
            fg=(1, 1, 1, 1),
            align=TextNode.ALeft,
            font=self.font,  
            mayChange=True
        )

        # Buttons
        self.Toggle_Grid_button = DirectButton(
            text=f"Grid: {'On' if self.grid_visible else 'Off'}",  
            scale=0.075,   # careful: scale is BIG, 1 means fullscreen
            pos=(-1.6, 0, 0.8),
            command=self.toggle_grid_function
        )
        self.Add_Object_button = DirectButton(
            text=f"Add",  
            scale=0.075,
            pos=(-1.6, 0, 0.9),
            command=self.add_object
        )

        # Add update task
        for _ in range(0, self.speed_factor):
            self.taskMgr.add(self.update_physics, "physicsTask")
        self.taskMgr.add(self.updateCamera, "updateCamera")
        self.taskMgr.add(self.updateUI, "updateUI")
    
#--------------------------Physics----------------------------------

    def update_physics(self, task):
        """Update physics for all objects applying gravity on each other."""
        dt = self.dt
        for i in self.objects:
            for j in self.objects:
                if i != j:
                    i.apply_gravity_from(j, dt)
        
        return task.cont

    def add_object(self):
        """Add a new object at a random position with random velocity."""
        import random
        pos = (0,0,0)
        vel = (0,0,0)
        scale = 100
        mass = 1
        new_object = Object.Object3D(
            self, "models/mars.glb",
            position=pos,
            scale=scale,
            rotation=(0, 0, 0),
            velocity=vel,
            mass=mass
        )
        self.objects.append(new_object)
        
#--------------------------UI----------------------------------
        
    def make_grid(self, size=1000, step=100, z=0):
        ls = LineSegs()

        # --- Grid lines ---
        ls.setColor(0.2,0.2,0.2,1)
        for x in range(-size, size + 1, step):
            ls.moveTo(x, -size, z)
            ls.drawTo(x, size, z)

        for y in range(-size, size + 1, step):
            ls.moveTo(-size, y, z)
            ls.drawTo(size, y, z)

        node = ls.create()
        return NodePath(node)

    def toggle_grid_function(self):
        if self.grid_visible:
            # Hide grid
            if self.grid_node:
                self.grid_node.hide()
            self.grid_visible = False
            self.Toggle_Grid_button['text'] = "Grid: Off"
        else:
            # Show grid
            if self.grid_node:
                self.grid_node.show()
            else:
                # Create grid if it doesn't exist
                self.grid_node = self.make_grid(size=100000, step=100, z=0)
                self.grid_node.setName("grid")
                self.grid_node.reparentTo(self.render)
                self.grid_node.setHpr(0, 0, 0)
            self.grid_visible = True
            self.Toggle_Grid_button['text'] = "Grid: On"

    def updateUI(self, task):
        pos = self.camera.getPos()
        self.CameraPosText.setText(f" X= {pos.x:.2f}, Y= {pos.y:.2f}, Z= {pos.z:.2f}")
        return task.cont
    
#--------------------------Camera----------------------------------

    def setupCamera(self):
        self.disableMouse()
        self.camera.setPos(self.start_cords)
        self.camera.lookAt(0, 0, 0)

    def updateCamera(self, task):
        dt = task.dt
        if (abs(self.camera.getX())+abs(self.camera.getY())+abs(self.camera.getZ())) > 3000:
            speed = 600000
        else:
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
        zoom_factor = 100
        if abs(self.camera.getZ()) > 2000:
            zoom_factor = 1000
        self.camera.setPos(self.camera, Vec3(0, zoom_factor, 0))  

    def zoomOut(self):
        # move camera forward along its look direction
        zoom_factor = 100
        if abs(self.camera.getZ()) > 2000:
            zoom_factor = 1000
        # move camera backward along its look direction
        self.camera.setPos(self.camera, Vec3(0, -zoom_factor, 0))
    

main = Main()
main.run()
