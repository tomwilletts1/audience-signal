from flask import Blueprint, request, jsonify

def create_client_data_blueprint(client_data_service):
    bp = Blueprint('client_data', __name__, url_prefix='/api/client_data')

    @bp.route('/upload', methods=['POST'])
    def upload():
        data = request.get_json()
        file_path = data.get('file_path')
        owner_id = data.get('owner_id')
        audience_name = data.get('audience_name', 'Client Audience')
        result = client_data_service.process_uploaded_file(file_path, owner_id, audience_name)
        return jsonify(result)

    @bp.route('/map_columns', methods=['POST'])
    def map_columns():
        data = request.get_json()
        data_id = data.get('data_id')
        column_mapping = data.get('column_mapping', {})
        result = client_data_service.map_columns(data_id, column_mapping)
        return jsonify(result)

    return bp 