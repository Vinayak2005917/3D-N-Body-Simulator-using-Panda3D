from direct.showbase.ShowBase import ShowBase
from panda3d.core import WindowProperties
from panda3d.core import LineSegs, NodePath
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import TransparencyAttrib
from panda3d.core import CardMaker, TextureStage, Loader
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

        self.setupCamera()

        self.setupSkybox()

        # First earth
        self.earth = Object.Object3D(
            self, "models/earth.glb",
            position=(0, 0, 0),
            scale=1,
            rotation=(0, 180, 0)
        )

        # Second earth (will move)
        self.earth2 = Object.Object3D(
            self, "models/moon.glb",
            position=(250, 0, 0),
            scale=30,
            rotation=(0, 180, 0),
            velocity=(0, 0, 500),
            mass=0.125
        )
        grid = self.make_grid(size=100000, step=100, z=0)
        grid.reparentTo(self.render)
        grid.setHpr(0, 90, 0)

        # Add update task
        self.taskMgr.add(self.apply_gravity_on, "updateTask", extraArgs=[self.earth2], appendTask=True)
    
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
    
    def setupCamera(self):
        self.disableMouse()
        self.camera.setPos(0, -400, -800)
        self.camera.lookAt(0, 0, 0)
        crosshair = OnscreenImage(image='crosshairs.png', pos=(0, 0, 0), scale=0.04)
        crosshair.setTransparency(TransparencyAttrib.MAlpha)

    def setupSkybox(self):
        loader = self.loader
        size = 5000

        # Six faces of the skybox
        faces = {
            'up': 'kurt/space_up.png',
            'down': 'kurt/space_dn.png',
            'left': 'kurt/space_lf.png',
            'right': 'kurt/space_rt.png',
            'front': 'kurt/space_ft.png',
            'back': 'kurt/space_bk.png'
        }

        # Positions and rotations for each face
        transforms = {
            'up': ((0, 0, size), (0, 180, 0)),
            'down': ((0, 0, -size), (0, 0, 0)),
            'left': ((-size, 0, 0), (0, 90, 0)),
            'right': ((size, 0, 0), (0, -90, 0)),
            'front': ((0, size, 0), (90, 0, 0)),
            'back': ((0, -size, 0), (-90, 0, 0))
        }

        for face, tex_path in faces.items():
            cm = CardMaker(face)
            cm.setFrame(-1, 1, -1, 1)
            card = self.render.attachNewNode(cm.generate())
            card.setPos(*transforms[face][0])
            card.setHpr(*transforms[face][1])
            tex = loader.loadTexture(tex_path)
            card.setTexture(tex)
            card.setScale(size)
            card.setBin('background', 1)
            card.setDepthWrite(False)
            card.setTwoSided(True)

main = Main()
main.run()
