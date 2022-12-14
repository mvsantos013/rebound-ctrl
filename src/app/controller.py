from flask import Blueprint, jsonify, request as req, Response
from src.app.models import SimulationModel
from src.app import service

blueprint = Blueprint('rebound-ctrl', __name__)

@blueprint.route('/hosts', methods=['GET'])
def fetch_hosts():
    return jsonify(data=service.fetch_hosts())

@blueprint.route('/simulations', methods=['GET'])
def fetch_simulations():
    simulations = [s.to_dict() for s in SimulationModel.scan().limit(10000)]
    return jsonify(data=simulations)

@blueprint.route('/simulations/<id>/logs', methods=['GET'])
def fetch_simulation_logs(id):
    host = req.args.get('host')
    return service.fetch_simulation_logs(id, host)

@blueprint.route('/simulations/<id>/results', methods=['GET'])
def download_simulation_results(id):
    file = service.download_simulation_results(id)
    response = Response(file, mimetype='application/tar+gzip')
    response.headers.add('Access-Control-Expose-Headers', f'Content-Disposition')
    response.headers.add('Content-Disposition', f'attachment; filename=results-{id}.tar.gz')
    return response

@blueprint.route('/simulations', methods=['POST'])
def create_simulation():
    simulation = req.get_json()
    return service.create_simulation(simulation)

@blueprint.route('/simulations/<id>', methods=['DELETE'])
def delete_simulation(id):
    service.delete_simulation(id)
    return jsonify(data={'success': True})

@blueprint.route('/simulations/check-status', methods=['POST'])
def check_simulations_status():
    simulations = req.get_json()
    return service.check_simulations_status(simulations)