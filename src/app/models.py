from dynamorm import DynaModel
from marshmallow import Schema, fields
from src.constants import SIMULATIONS_TABLE, SIMULATIONS_RESULTS_TABLE


class SimulationModel(DynaModel):
    class Table:
        name = SIMULATIONS_TABLE
        hash_key = 'id'
        
    class SimulationSchema(Schema):
        id = fields.Str()
        name = fields.Str()
        description = fields.Str()
        status = fields.Str()
        process_id = fields.Str()
        host = fields.Str()
        simulation_type = fields.Str()
        cores = fields.Int()
        integrator = fields.Str()
        timestep = fields.Decimal()
        years = fields.Decimal()
        num_logs = fields.Int()
        ejection_max_distance = fields.Decimal()
        particles = fields.List(fields.Dict())
        grid = fields.Dict()
        created_at = fields.Str()

    class Schema(SimulationSchema):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)