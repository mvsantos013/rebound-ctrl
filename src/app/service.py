import json
import time
import traceback
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
from src.lib.adapters.ssh_adapter import SSHClient
from src.app.models import SimulationModel, SimulationResultsModel
from src.constants import HOSTS, SSH_KEYS

def fetch_host_status(ssh, host):
    ''' Check if host is busy. Currently the approach is to check if
        there are more than 7 processes running, but this could be improved.
    '''
    try:
        if(host not in SSH_KEYS):
            raise Exception(f'Credentials not found for host {host}.')
        response, error = ssh.cmd('cat /proc/loadavg')
        procs, total_procs = response.split()[3].split('/')
        status = 'free' if int(procs) < 7 else 'busy'
        return status
    except:
        raise Exception('Error while fetching host status.')

def process_exists(ssh, process_id):
    response, error = ssh.cmd(f'ps -p {process_id}')
    return str(process_id) in response

def create_simulation(simulation):
    ssh = None
    try:
        simulation['id'] = str(uuid4())
        simulation['created_at'] = datetime.now(timezone.utc).isoformat()
        
        # Validate inputs
        SimulationModel.Schema().load(simulation)
        
        host = simulation['host']
        ssh = SSHClient(host, **SSH_KEYS[host]).connect()
        
        # Check if host is free
        print('Checking host status...')
        if(fetch_host_status(ssh, host) == 'busy'):
            raise Exception(f'Host {host} is busy.')
        
        print('Host is free.')
        print('Setting up simulation...')
        
        # Create simulation folder
        folder = f'rebound-ctrl/simulations/{simulation["id"]}'
        ssh.cmd(f'mkdir -p {folder}')
        
        # Upload meta.json file 
        meta_content = json.dumps(simulation, indent=4).replace('"', '\\"')
        ssh.upload(f'src/assets/problem.py', f'{folder}/problem.py')
        
        # Commands to setup simulation folder and start execution
        print('Starting simulation...')
        ssh.cmd(f'cd {folder} && echo "{meta_content}" > meta.json')
        ssh.cmd(f'cd {folder} && echo "python -u problem.py" > run.sh')
        ssh.cmd(f'cd {folder} && chmod +x run.sh')
        ssh.cmd(f'cd {folder} && nohup ./run.sh > logs.txt 2> errors.txt & echo $! > {folder}/pid.txt', wait_response=False)
        
        print('Checking simulation status...')
        time.sleep(1)
        try:
            process_id = int(ssh.cmd(f'cd {folder} && cat pid.txt')[0])
            if(process_exists(ssh, process_id)):
                print('Simulation started successfully. PID:', process_id)
        except Exception as e:
            raise(f'Process ID could not be identified. ({e}) ')
        
        simulation['process_id'] = str(process_id)
        simulation['status'] = 'running'
        
        obj = json.loads(json.dumps(simulation), parse_float=Decimal)
        SimulationModel(**obj).save()    
        
        return simulation
    except Exception as e:
        if(ssh is not None):
            ssh.disconnect()
        raise Exception(f'Error while creating simulation: {e}')
    
def fetch_simulation_logs(id, host):
    ssh = None
    try:
        ssh = SSHClient(host, **SSH_KEYS[host]).connect()
        response, error = ssh.cmd(f'cat rebound-ctrl/simulations/{id}/logs.txt')
        return response       
    except Exception as e:
        if(ssh is not None):
            ssh.disconnect()
        raise Exception(f'Error while fetching simulation logs: {e}')

def check_simulations_status(simulations):
    response = []
    for simulation in simulations:
        ssh = None
        try:
            host = simulation['host']
            ssh = SSHClient(host, **SSH_KEYS[host]).connect()
            sim_path = f'rebound-ctrl/simulations/{simulation["id"]}'
            
            # Check if there is a simulation folder
            has_simulation, error = ssh.cmd(f'[ -d "{sim_path}" ] && echo true')
            if(not has_simulation):
                simulation['status'] = 'unkwown'
            
            # Check if there are errors
            errors_content, error = ssh.cmd(f'[ -f "{sim_path}/errors.txt" ] && cat {sim_path}/errors.txt')
            if(errors_content):
                simulation['status'] = 'failed'
            
            # Check if simulation has results
            results, error = ssh.cmd(f'[ -f "{sim_path}/results.json" ] && cat {sim_path}/results.json')
            if(results):
                results = json.loads(results)
                if(results['status'] == 'failed'):
                    simulation['status'] = 'failed'
                else:
                    simulation['status'] = 'finished'
            
            # Simulation is not running anymore, save results in database.
            if(simulation['status'] != 'running'):
                obj = { 
                    'id': simulation['id'],
                    'results': results if results else {}
                }
                
                # Save results
                obj = json.loads(json.dumps(obj), parse_float=Decimal)
                SimulationResultsModel(**obj).save()
                
                # Update simulation status
                sim = {'id': simulation['id'], 'status': simulation['status']}
                SimulationModel(**sim).update(**sim)
                
            response.append(simulation)
            ssh.disconnect()
        except Exception as e:
            print(traceback.format_exc())
            if(ssh is not None):
                ssh.disconnect()
            simulation['error'] = f'Error while updating simulations status: {e}'
            response.append(simulation)
    return response