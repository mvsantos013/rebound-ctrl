import os
import json
from rebound.interruptible_pool import InterruptiblePool
import traceback
from problem import DefaultSimulation, GridSimulation
from problem import utils


if __name__ == '__main__':
    try:
        utils.log('Reading inputs...')
        with open('meta.json') as f:
            inputs = json.load(f)

        utils.log('Starting simulation...')
        if(inputs.get('simulation_type') == 'default'):
            sim = DefaultSimulation(inputs)
            results = sim.run(inputs['particles'])
        elif(inputs.get('simulation_type') == 'grid'):
            sim = GridSimulation(inputs)
            params = sim.prepare_params()
            pool = InterruptiblePool(sim.cores)
            results = pool.map(sim.run, params)
        else:
            raise Exception(f'Simulation type not implemented:, {inputs.get("simulation_type")}')
        
        utils.log('Simulation finished, exporting results...')
        # Create results folder
        if(not os.path.exists('results')):
            os.makedirs('results')
        sim.export_results(results)
        utils.log('Results exported successfully.')
        
    except Exception as e:
        utils.log(traceback.format_exc())
        utils.log(f'PROGRAM_ERROR: {e}')
        with open('results/results.json', 'w') as f:
            json.dump({'error': str(e), 'status': 'failed'}, f, indent=4)