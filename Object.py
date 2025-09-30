class Object3D:
    def __init__(self, parent, model_path, scale=1, position=(0,0,0), velocity=(0,0,0), acceleration=(0,0,0), 
                 rotation=(0,0,0), angular_velocity=(0,0,0), angular_acceleration=(0,0,0), mass=1):
        self.model = parent.loader.loadModel(model_path)
        self.model.reparentTo(parent.render)

        self.model.setPos(*position)
        self.model.setScale(scale)
        self.model.setHpr(*rotation)

        self.velocity = velocity
        self.angular_velocity = angular_velocity
        self.acceleration = acceleration
        self.angular_acceleration = angular_acceleration
        self.mass = mass

    # --- Position methods ---
    def get_position(self):
        return self.model.getPos()

    def set_position(self, pos):
        self.model.setPos(*pos)
    
    def update_position(self, dt):
        x, y, z = self.get_position()
        vx, vy, vz = self.get_velocity()
        new_pos = (x + vx * dt, y + vy * dt, z + vz * dt)
        self.set_position(new_pos)

    # --- Velocity methods ---
    def get_velocity(self):
        return self.velocity

    def set_velocity(self, vel):
        self.velocity = vel

    # --- Rotation methods ---
    def get_rotation(self):
        return self.model.getHpr()

    def set_rotation(self, rot):
        self.model.setHpr(*rot)
