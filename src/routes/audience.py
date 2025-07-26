from flask import Blueprint, request, jsonify

def create_audience_blueprint(audience_service):
    bp = Blueprint('audience', __name__, url_prefix='/api/audience')

    @bp.route('/create', methods=['POST'])
    def create():
        data = request.get_json()
        result = audience_service.create_audience_from_filters(
            name=data.get('name'),
            audience_type=data.get('type'),
            criteria=data.get('criteria'),
            owner_id=data.get('owner_id')
        )
        return jsonify(result)

    @bp.route('/list', methods=['GET'])
    def list_():
        return jsonify(audience_service.list_all_audiences())

    @bp.route('/<audience_id>', methods=['GET'])
    def get_audience(audience_id):
        return jsonify(audience_service.get_audience_by_id(audience_id))

    @bp.route('/<audience_id>/sample', methods=['POST'])
    def sample_personas(audience_id):
        data = request.get_json() or {}
        count = int(data.get('count', 8))
        personas = audience_service.sample_personas_from_audience(audience_id, count=count)
        return jsonify({'personas': personas})

    return bp 