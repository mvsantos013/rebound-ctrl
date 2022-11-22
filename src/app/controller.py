from flask import Blueprint, jsonify, request as req
from src.app.models import SimulationModel, SimulationResultsModel
from src.app import service
from src.app.constants import HOSTS

blueprint = Blueprint('rebound-ctrl', __name__)

@blueprint.route('/hosts', methods=['GET'])
def fetch_hosts():
    return jsonify(data=HOSTS)

@blueprint.route('/simulations', methods=['GET'])
def fetch_simulations():
    simulations = [s.to_dict() for s in SimulationModel.scan().limit(10000)]
    return jsonify(data=simulations)

@blueprint.route('/simulations/<id>', methods=['GET'])
def fetch_simulation_results(id):
    result = SimulationResultsModel.get(id=id)
    if(result is None):
        return {}
    return result.to_dict()

@blueprint.route('/simulations', methods=['POST'])
def create_simulation():
    print('oi')
    return {}

def delete_simulation():
    pass