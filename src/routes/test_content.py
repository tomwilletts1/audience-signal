from flask import Blueprint, request, jsonify

def create_test_content_blueprint(content_test_service):
    bp = Blueprint('test_content', __name__, url_prefix='/api/test_content')

    @bp.route('/run', methods=['POST'])
    def run_content_test():
        data = request.get_json()
        audience_id = data.get('audience_id')
        content = data.get('content')
        sample_size = int(data.get('sample_size', 15))
        result = content_test_service.test_content(audience_id, content, sample_size)
        return jsonify(result)

    return bp 