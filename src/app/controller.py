from flask import Blueprint, jsonify, request as req
from src.app.models import SimulationModel, SimulationResultsModel
from src.app import service
from src.constants import HOSTS

blueprint = Blueprint('rebound-ctrl', __name__)

@blueprint.route('/hosts', methods=['GET'])
def fetch_hosts():
    return jsonify(data=HOSTS)

@blueprint.route('/simulations', methods=['GET'])
def fetch_simulations():
    simulations = [s.to_dict() for s in SimulationModel.scan().limit(10000)]
    return jsonify(data=simulations)

@blueprint.route('/simulations/<id>/logs', methods=['GET'])
def fetch_simulation_logs(id):
    host = req.args.get('host')
    return service.fetch_simulation_logs(id, host)

@blueprint.route('/simulations/<id>', methods=['GET'])
def fetch_simulation_results(id):
    result = SimulationResultsModel.get(id=id)
    if(result is None):
        return {}
    return result.to_dict()

@blueprint.route('/simulations', methods=['POST'])
def create_simulation():
    simulation = req.get_json()
    return service.create_simulation(simulation)

@blueprint.route('/simulations/check-status', methods=['POST'])
def check_simulations_status():
    simulations = req.get_json()
    return service.check_simulations_status(simulations)

def delete_simulation():
    pass