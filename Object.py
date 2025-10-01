import numpy as np

class Object3D:
    # Gravitational constant
    G = 6674384.0  # Adjusted for simulation scale
    
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

    # --- Physics methods ---
    def calculate_acceleration_from(self, other_object):
        """Calculate the gravitational acceleration this object experiences from another object."""
        pos_self = np.array(self.get_position())
        pos_other = np.array(other_object.get_position())
        
        r_vec = pos_other - pos_self
        r2 = np.dot(r_vec, r_vec)
        
        if r2 == 0:
            return np.array([0.0, 0.0, 0.0])
        
        # a = G * M / r^2, in direction of r_vec
        return self.G * other_object.mass * r_vec / (r2 * np.sqrt(r2))

    def rk4_step(self, dt, acc_func):
        """Perform RK4 integration step for position and velocity."""
        pos = np.array(self.get_position())
        vel = np.array(self.velocity)
        
        # k1
        a1 = acc_func(pos)
        v1 = vel
        p1 = pos

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

    def apply_gravity_from(self, other_object, dt):
        """Apply gravitational force from another object using RK4 integration."""
        # Create acceleration function for this specific interaction
        def acc_func(p):
            pos_other = np.array(other_object.get_position())
            r_vec = pos_other - p
            r2 = np.dot(r_vec, r_vec)
            if r2 == 0:
                return np.array([0.0, 0.0, 0.0])
            return self.G * other_object.mass * r_vec / (r2 * np.sqrt(r2))
        
        # Update position and velocity using RK4
        pos_new, vel_new = self.rk4_step(dt, acc_func)
        self.set_position(pos_new)
        self.set_velocity(vel_new)
    


#--------------------------Documentation----------------------------------