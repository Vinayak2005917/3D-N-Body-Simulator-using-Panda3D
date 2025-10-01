from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import LineSegs, NodePath
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
from panda3d.core import CardMaker, TextureStage, Loader
from panda3d.core import Vec3
import Object
import numpy as np

class Main(ShowBase):
    def __init__(self):
        super().__init__()

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

        self.setupCamera()


        # First earth
        self.earth = Object.Object3D(
            self, "models/earth.glb",
            position=(0, 0, 0),
            scale=1,
            rotation=(0, 90, 0)
        )

        # Second earth (will move)
        self.moon = Object.Object3D(
            self, "models/moon.glb",
            position=(250, 0, 0),
            scale=30,
            rotation=(0, 90, 0),
            velocity=(0, 500, 0),
            mass=0.125
        )
        grid = self.make_grid(size=100000, step=100, z=0)
        grid.reparentTo(self.render)
        grid.setHpr(0, 0, 0)

        # Add update task
        self.taskMgr.add(self.apply_gravity_on, "updateTask", extraArgs=[self.moon], appendTask=True)
        self.taskMgr.add(self.updateCamera, "updateCamera")
    

#--------------------------Physics----------------------------------

    def acceleration(self, pos_obj, pos_target, G, m_target):
        r_vec = np.array(pos_target) - np.array(pos_obj)
        r2 = np.dot(r_vec, r_vec)
        if r2 == 0:
            return np.array([0.0, 0.0, 0.0])
        return G * m_target * r_vec / (r2 * np.sqrt(r2))  # a = F/m, normalized r_vec

    def rk4_step(self, pos, vel, dt, acc_func):
        # k1
        a1 = acc_func(pos)
        v1 = np.array(vel)
        p1 = np.array(pos)

        # k2
        a2 = acc_func(p1 + 0.5*v1*dt)
        v2 = v1 + 0.5*a1*dt

        # k3
        a3 = acc_func(p1 + 0.5*v2*dt)
        v3 = v1 + 0.5*a2*dt

        # k4
        a4 = acc_func(p1 + v3*dt)
        v4 = v1 + a3*dt

        # Combine
        pos_new = pos + (v1 + 2*v2 + 2*v3 + v4) * dt / 6
        vel_new = vel + (a1 + 2*a2 + 2*a3 + a4) * dt / 6

        return pos_new, vel_new

    def apply_gravity_on(self, obj, task):
        dt = task.dt * 15
        G = 66743000
        pos_target = self.earth.get_position()
        m_target = self.earth.mass

        pos = np.array(obj.get_position())
        vel = np.array(obj.get_velocity())

        # RK4 step
        def acc_func(p):
            return self.acceleration(p, pos_target, G, m_target)

        pos_new, vel_new = self.rk4_step(pos, vel, dt, acc_func)

        # Update object
        obj.set_position(pos_new)
        obj.set_velocity(vel_new)

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
        self.camera.setPos(0, 0, 0)
        self.camera.lookAt(0, 0, 0)

    def updateCamera(self, task):
        dt = task.dt
        speed = 350000   # units per second

        # --- Movement vector ---
        move_vec = Vec3(0, 0, 0)

        # WASD relative to where the camera is facing
        if self.mouseWatcherNode.is_button_down('w'):
            move_vec += Vec3(0, 1, 0)   # forward
        if self.mouseWatcherNode.is_button_down('s'):
            move_vec += Vec3(0, -1, 0)  # backward
        if self.mouseWatcherNode.is_button_down('a'):
            move_vec += Vec3(-1, 0, 0)  # left
        if self.mouseWatcherNode.is_button_down('d'):
            move_vec += Vec3(1, 0, 0)   # right

        # Space/Shift = up/down in WORLD space (not camera space)
        if self.mouseWatcherNode.is_button_down('space'):
            self.camera.setZ(self.camera.getZ() + speed * dt)
        if self.mouseWatcherNode.is_button_down('shift'):
            self.camera.setZ(self.camera.getZ() - speed * dt)

        # --- Apply WASD in camera's local XY plane ---
        if move_vec.length() > 0:
            move_vec.normalize()
            self.camera.setPos(self.camera, move_vec * speed * dt)

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


main = Main()
main.run()
