import json
import time
import traceback
from io import BytesIO
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timezone
from src.lib.adapters.ssh_adapter import SSHClient
from src.lib.adapters import s3_adapter
from src.app.models import SimulationModel
from src.constants import HOSTS, SSH_KEYS, STAGE

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
        ssh.cmd(f'mkdir -p {folder}/problem/types')
        
        # Commands to setup simulation folder and start execution
        files = [
            'problem/__init__.py', 'problem/types/default.py', 'problem/types/grid.py',
            'problem/utils.py', 'problem.py', 'charts.py', 'README.md'
        ]
        for filename in files:
            ssh.upload(f'src/boilerplate/{filename}', f'{folder}/{filename}')
        
        meta_content = json.dumps(simulation, indent=4).replace('"', '\\"')
        ssh.cmd(f'cd {folder} && echo "{meta_content}" > meta.json')
        ssh.cmd(f'cd {folder} && echo "python3 -u problem.py" > run.sh')
        ssh.cmd(f'cd {folder} && chmod +x run.sh')
        
        print('Starting simulation...')
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
    simulation = SimulationModel.get(id=id)
    
    # Retrieve from machine if it's still running
    if(simulation and simulation.status == 'running'):
        ssh = None
        try:
            ssh = SSHClient(host, **SSH_KEYS[host]).connect()
            logs, error = ssh.cmd(f'cat rebound-ctrl/simulations/{id}/logs.txt')
            return logs       
        except Exception as e:
            if(ssh is not None):
                ssh.disconnect()
            raise Exception(f'Error while fetching simulation logs: {e}')
    
    # Retrieve from S3 if it's finished
    logs = download_simulation_logs(id)
    return logs

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
            results, error = ssh.cmd(f'[ -f "{sim_path}/results/results.json" ] && cat {sim_path}/results/results.json')
            if(results):
                results = json.loads(results)
                if(results['status'] == 'failed'):
                    simulation['status'] = 'failed'
                else:
                    simulation['status'] = 'finished'
            
            # Simulation is not running anymore, save results in database and s3.
            if(simulation['status'] != 'running'):
                # Update simulation status
                sim = {'id': simulation['id'], 'status': simulation['status']}
                SimulationModel(**sim).update(**sim)
                
                # Save results in s3 if simulation folder is available
                if(simulation['status'] == 'finished'):
                    try:
                        folder = f'rebound-ctrl/simulations/{simulation["id"]}'
                        ssh.cmd(f'cd {folder} && rm results.tar.gz')
                        ssh.cmd(f'cd {folder} && tar -czvf results.tar.gz .')
                        file = ssh.download(f'{folder}/results.tar.gz')
                        logs, error = ssh.cmd(f'cat rebound-ctrl/simulations/{simulation["id"]}/logs.txt')
                        bucket = f'rebound-ctrl-{STAGE}-files'
                        s3_adapter.upload_file(
                            bucket=bucket, 
                            path=f'simulations/{simulation["id"]}/results.tar.gz', 
                            file=file, 
                            content_type='application/tar+gzip'
                        )
                        s3_adapter.save_to_s3(bucket, f'simulations/{simulation["id"]}/logs.txt', logs)
                        ssh.cmd(f'rm -r {folder}')
                    except:
                        raise Exception('Error while saving simulation results in AWS S3. The simulation files are still available in the server.')
                    
            response.append(simulation)
            ssh.disconnect()
        except Exception as e:
            print(traceback.format_exc())
            if(ssh is not None):
                ssh.disconnect()
            simulation['error'] = f'Error while updating simulations status: {e}'
            response.append(simulation)
    return response

def download_simulation_results(id):
    try:
        file = s3_adapter.download_file(f'rebound-ctrl-{STAGE}-files', f'simulations/{id}/results.tar.gz')
        return file
    except Exception as e:
        raise Exception(f'Error while fetching simulation results: {e}')

def download_simulation_logs(id):
    try:
        file = s3_adapter.download_file(f'rebound-ctrl-{STAGE}-files', f'simulations/{id}/logs.txt')
        return file
    except Exception as e:
        raise Exception(f'Error while fetching simulation logs: {e}')

def delete_simulation(id):
    simulation = SimulationModel.get(id=id)
    
    # Delete from machine if it's still running
    if(simulation and simulation.status == 'running'):
        ssh = None
        try:
            ssh = SSHClient(simulation.host, **SSH_KEYS[simulation.host]).connect()
            ssh.cmd(f'rm -r rebound-ctrl/simulations/{id}')
            # TODO: kill process
        except Exception as e:
            print(f'Error while deleting simulation folder: {e}')
            if(ssh is not None):
                ssh.disconnect()
    else: # Simulation has already finished, delete results from s3
        try:
            s3_adapter.delete_file(f'rebound-ctrl-{STAGE}-files', f'simulations/{id}/results.tar.gz')
            s3_adapter.delete_file(f'rebound-ctrl-{STAGE}-files', f'simulations/{id}/logs.txt')
        except Exception as e:
            print(f'Error while deleting simulation folder: {e}')
    
    simulation.delete()