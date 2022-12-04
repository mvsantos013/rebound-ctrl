import os
import rebound
import math
import time
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone

class DefaultSimulation():
    def __init__(self, inputs):
        self.inputs = inputs
        self.simulation_id = inputs['id']
        self.simulation_type = inputs['simulation_type']             # Simulation type (default or grid)
        self.cores = inputs['cores']                                 # Number of processor cores to use
        self.integrator = inputs['integrator']                       # Integrator to use
        self.years = inputs['years']                                 # 100 years
        self.number_of_logs = inputs['num_logs']                     # Number of logs
        self.ejection_max_distance = inputs['ejection_max_distance'] # Max distance from center of mass
        self.timestep = inputs['timestep']                           # Timestep of the simulation
        self.start_time = time.time()                              
        
    def run(self, particles):
        ''' Run simulation based on parameters. '''
        self.sim = rebound.Simulation()                             # Create simulation object
        self.sim.integrator = self.integrator                       # Set integrator
        self.sim.dt = self.timestep * (2*math.pi)                   # Set timestep

        for particle in particles:
            for attr in particle:
                particle[attr] = float(particle[attr])
            self.sim.add(**particle)                                # Add particle to the simulation

        self.sim.move_to_com()                                      # Move objects to the center of momentum frame

        self.sim.init_megno(seed=0)                                 # Setup Megno chaos indicator
        self.sim.exit_max_distance = self.ejection_max_distance     # Max distance from center of mass
        
        error = None
        try:
            self.sim.integrate(self.years * (2*math.pi))              # Run simulation
        except Exception as e:
            error = e
    
        result = self.calculate_result(error, particles)
        
        return result

    def calculate_result(self, error, particles):
        ''' Calculate result of the simulation. '''
       
        # Final orbit data by particle
        orbits = []
        for i, final_orbit in enumerate(self.sim.calculate_orbits()):
            inital_orbit = particles[i+1]
            orbit = {
                'a': final_orbit.a,
                'e': final_orbit.e,
                'inc': final_orbit.inc,
                'Omega': final_orbit.Omega,
                'omega': final_orbit.omega,
                'M': final_orbit.M,
                'delta_a': final_orbit.a - inital_orbit.get('a', 0),
                'delta_e': final_orbit.e - inital_orbit.get('e', 0)
            }
            orbits.append(orbit)
        
        # Check if there was an error 
        if(error):                                                  
            megno = 10.0
            return megno, orbits
        
        megno = self.sim.calculate_megno()
        return megno, orbits
    
    
    def export_results(self, results):
        megno, orbits = results
        end_time = time.time()
        
        # General result
        result = {
            'megno': megno,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'end_time': datetime.fromtimestamp(end_time).isoformat(),
            'duration_time': (end_time - self.start_time) / 60 / 60,
            'status': 'finished',
        }
        
        # Exports results.json file    
        with open('results/results.json', 'w') as f:
            json.dump(result, f, indent=4)
        
        # Exports orbits file for each particle
        i = 1
        for particle in orbits:
            df = pd.DataFrame([particle])
            df.to_csv(f'results/orbits_p{i:03d}.csv', index=False, header=True)
            i += 1