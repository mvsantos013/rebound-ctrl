import rebound
from rebound.interruptible_pool import InterruptiblePool
from datetime import datetime, timezone
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing
import time
import json
import traceback

# Read simulation parameters.
with open("meta.json") as f:
    inputs = json.load(f)

SIMULATION_ID = inputs['id']
SIMULATION_TYPE = inputs['simulation_type']             # Simulation type (default or grid)
CORES = inputs['cores']                                 # Number of processor cores to use
INTEGRATOR = inputs['integrator']                       # Integrator to use
YEARS = inputs['years']                                 # 100 years
NUMBER_OF_LOGS = inputs['num_logs']                     # Number of logs
EJECTION_MAX_DISTANCE = inputs['ejection_max_distance'] # Max distance from center of mass
TIMESTEP = inputs['timestep']                           # Timestep of the simulation

if(SIMULATION_TYPE == 'grid'):
    N_GRID = inputs['grid']['N']                        # Grid size
    NUM_SIMULATIONS = N_GRID ** 2                       # Number of simulations
    D = max(int(NUM_SIMULATIONS / NUMBER_OF_LOGS), 1)   # Number of simulations per log line
    
# --------------------------------------------------------------------

start_time = time.time()                            # Simulation start time
sim_finished = multiprocessing.Value('i', 0)        # Number of simulations finished

def simulate(particles, params = {}):
    ''' Run simulation based on parameters. '''
    sim = rebound.Simulation()                      # Create simulation object
    sim.integrator = INTEGRATOR
    sim.dt = TIMESTEP

    for particle in particles:
        for attr in particle:
            particle[attr] = float(particle[attr])
        sim.add(**particle)                         # Add particle to the simulation

    sim.move_to_com()                               # Move objects to the center of momentum frame

    sim.init_megno(seed=0)                          # Setup Megno chaos indicator
    sim.exit_max_distance = EJECTION_MAX_DISTANCE   # Max distance from center of mass
    try:
        sim.integrate(YEARS * (2*np.pi))            # Run simulation
        megno = sim.calculate_megno()
    except rebound.Escape:
        megno = 10.                                 # Particle got ejected

    # Check if megno is undefined for some reason.
    if megno != megno:
        megno = 10.
        
    orbits = calculate_orbits(sim) 
    
    if(SIMULATION_TYPE == 'default'):
        return megno, orbits
    elif(SIMULATION_TYPE == 'grid'):
        global sim_finished
        # After every D simulations, log the progress
        with sim_finished.get_lock():
            sim_finished.value = sim_finished.value + 1
            should_log = sim_finished.value % D == 0
            if(should_log):
                progress = sim_finished.value / (NUM_SIMULATIONS) * 100
                time_elapsed = time.time() - start_time
                eta = 100 * time_elapsed / progress - time_elapsed if progress else 0
                print(f'{sim_finished.value}/{NUM_SIMULATIONS} ({progress:.2f}% | {time_elapsed/60:.2f} min | {eta/60:.2f} min ETA)')
        delta_as, delta_es = [], []
        for orbit, particle in zip(orbits, particles[1:]):
            delta_as.append(orbit['a'] - particle['a'])
            delta_es.append(orbit['e'] - particle['e'])
        return megno, delta_as, delta_es

def calculate_orbits(sim):
    ''' Return orbits as list of dicts instead of list of objects. '''
    orbits = []
    for orbit in sim.calculate_orbits():
        o = {}
        for attr in orbit._fields_:
            o[attr[0]] = getattr(orbit, attr[0])
        orbits.append(o)
    return orbits


if __name__ == "__main__":
    try:
        print(f'{datetime.now(timezone.utc).isoformat()} Running simulation...')
        if(SIMULATION_TYPE == 'default'):
            megno, orbits = simulate(inputs['particles'])
            end_time = time.time()
            result = {
                'id': SIMULATION_ID,
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat(),
                'duration_time': (end_time - start_time) / 60 / 60,
                'status': 'finished',
                'results': {
                    'megno': megno,
                    'orbits': orbits,
                }
            }
        elif(SIMULATION_TYPE == 'grid'):
            pool = InterruptiblePool(CORES)
            
            # Identify attributes ranges
            ranges = {}
            particle = inputs['grid']['particle']
            for attr in particle:
                if(type(particle[attr]) == list):
                    ranges[attr] = np.linspace(particle[attr][0], particle[attr][1], N_GRID)
            x_attr, y_attr = list(ranges.keys())
            
            # Create parameters for each simulation
            params = []
            for y in ranges[y_attr]:
                for x in ranges[x_attr]:
                    particles = inputs['particles'].copy()
                    particles.append({**particle, x_attr: x, y_attr: y})
                    params.append(particles)
            
            results = pool.map(simulate, params)
            end_time = time.time()
            megnos, delta_as, delta_es = [], [], []
            for r in results:
                megnos.append(r[0])
                delta_as.append(r[1])
                delta_es.append(r[2])

            result = {
                'id': SIMULATION_ID,
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat(),
                'duration_time': (end_time - start_time) / 60 / 60,
                'status': 'finished',
                'results': {
                    'megnos': megnos,
                    'delta_a': delta_as,
                    'delta_e': delta_es,
                },
            }
        else: 
            raise Exception(f'Simulation type not implemented: {SIMULATION_TYPE}')
        
        print(f'{datetime.now(timezone.utc).isoformat()} Simulation finished.')
        
        with open('results.json', 'w') as f:
            json.dump(result, f, indent=4)
            
    except Exception as e:
        print(traceback.format_exc())
        print(f'{datetime.now(timezone.utc).isoformat()} PROGRAM_ERROR: {e}')
        with open('results.json', 'w') as f:
            json.dump({'error': str(e), 'status': 'failed'}, f, indent=4)