"""
AI Form Generator - Web Application

A Flask-based web application that provides:
- Natural language form input
- Live form preview
- Dynamic field editing
- Export to HTML/JSON
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response
from form_generator import (
    AIFormParser,
    FormGenerator,
    FormConfig,
    FormField,
    FormEditorConfig,
    create_form_from_text
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# In-memory storage for form sessions (use database in production)
form_sessions = {}


@app.route('/')
def index():
    """Main page with the form generator interface."""
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate_form():
    """
    Generate a form from natural language input.

    Request body:
        {
            "text": "Natural language description of the form"
        }

    Returns:
        {
            "session_id": "unique-session-id",
            "config": {...form configuration...},
            "html": "generated HTML"
        }
    """
    data = request.get_json()
    text = data.get('text', '')

    if not text.strip():
        return jsonify({"error": "No input text provided"}), 400

    try:
        # Parse the input
        parser = AIFormParser()
        config = parser.parse(text)

        # Generate HTML
        generator = FormGenerator()
        html = generator.generate(config)

        # Create session
        session_id = str(uuid.uuid4())
        form_sessions[session_id] = {
            "config": config.to_dict(),
            "html": html,
            "created_at": datetime.now().isoformat(),
            "original_text": text
        }

        return jsonify({
            "session_id": session_id,
            "config": config.to_dict(),
            "html": html,
            "field_types": FormEditorConfig.get_field_types()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/form/<session_id>', methods=['GET'])
def get_form(session_id):
    """Get form configuration by session ID."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    session = form_sessions[session_id]
    return jsonify({
        "session_id": session_id,
        "config": session["config"],
        "html": session["html"]
    })


@app.route('/api/form/<session_id>/update', methods=['POST'])
def update_form(session_id):
    """
    Update form configuration.

    Request body:
        {
            "config": {...updated form configuration...}
        }
    """
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    new_config_dict = data.get('config')

    if not new_config_dict:
        return jsonify({"error": "No configuration provided"}), 400

    try:
        # Rebuild FormConfig from dict
        fields = []
        for field_dict in new_config_dict.get('fields', []):
            field = FormField(
                id=field_dict['id'],
                label=field_dict['label'],
                field_type=field_dict['field_type'],
                name=field_dict['name'],
                required=field_dict.get('required', False),
                placeholder=field_dict.get('placeholder', ''),
                description=field_dict.get('description', ''),
                options=field_dict.get('options', []),
                validation=field_dict.get('validation', {}),
                default_value=field_dict.get('default_value', '')
            )
            fields.append(field)

        config = FormConfig(
            title=new_config_dict.get('title', 'Form'),
            description=new_config_dict.get('description', ''),
            fields=fields,
            action=new_config_dict.get('action', '#'),
            method=new_config_dict.get('method', 'POST')
        )

        # Regenerate HTML
        generator = FormGenerator()
        html = generator.generate(config)

        # Update session
        form_sessions[session_id]["config"] = config.to_dict()
        form_sessions[session_id]["html"] = html

        return jsonify({
            "session_id": session_id,
            "config": config.to_dict(),
            "html": html
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/form/<session_id>/field', methods=['POST'])
def add_field(session_id):
    """Add a new field to the form."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    field_data = data.get('field')

    if not field_data:
        return jsonify({"error": "No field data provided"}), 400

    try:
        session = form_sessions[session_id]
        config_dict = session["config"]

        # Generate unique field ID
        field_id = f"field_{len(config_dict['fields']) + 1}_{uuid.uuid4().hex[:6]}"

        new_field = {
            "id": field_id,
            "label": field_data.get('label', 'New Field'),
            "field_type": field_data.get('field_type', 'text'),
            "name": field_data.get('name', field_id),
            "required": field_data.get('required', False),
            "placeholder": field_data.get('placeholder', ''),
            "description": field_data.get('description', ''),
            "options": field_data.get('options', []),
            "validation": field_data.get('validation', {}),
            "default_value": field_data.get('default_value', '')
        }

        config_dict['fields'].append(new_field)

        # Regenerate HTML
        fields = [FormField(**f) for f in config_dict['fields']]
        config = FormConfig(
            title=config_dict['title'],
            description=config_dict['description'],
            fields=fields
        )
        generator = FormGenerator()
        html = generator.generate(config)

        session["html"] = html

        return jsonify({
            "field": new_field,
            "html": html
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/form/<session_id>/field/<field_id>', methods=['PUT'])
def update_field(session_id, field_id):
    """Update a specific field."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    field_data = data.get('field')

    if not field_data:
        return jsonify({"error": "No field data provided"}), 400

    try:
        session = form_sessions[session_id]
        config_dict = session["config"]

        # Find and update the field
        field_found = False
        for i, field in enumerate(config_dict['fields']):
            if field['id'] == field_id:
                config_dict['fields'][i] = {
                    **field,
                    **field_data,
                    'id': field_id  # Preserve ID
                }
                field_found = True
                break

        if not field_found:
            return jsonify({"error": "Field not found"}), 404

        # Regenerate HTML
        fields = [FormField(**f) for f in config_dict['fields']]
        config = FormConfig(
            title=config_dict['title'],
            description=config_dict['description'],
            fields=fields
        )
        generator = FormGenerator()
        html = generator.generate(config)

        session["html"] = html

        return jsonify({
            "field": config_dict['fields'][i],
            "html": html
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/form/<session_id>/field/<field_id>', methods=['DELETE'])
def delete_field(session_id, field_id):
    """Delete a field from the form."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    try:
        session = form_sessions[session_id]
        config_dict = session["config"]

        # Remove the field
        original_length = len(config_dict['fields'])
        config_dict['fields'] = [f for f in config_dict['fields'] if f['id'] != field_id]

        if len(config_dict['fields']) == original_length:
            return jsonify({"error": "Field not found"}), 404

        # Regenerate HTML
        fields = [FormField(**f) for f in config_dict['fields']]
        config = FormConfig(
            title=config_dict['title'],
            description=config_dict['description'],
            fields=fields
        )
        generator = FormGenerator()
        html = generator.generate(config)

        session["html"] = html

        return jsonify({
            "success": True,
            "html": html
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/form/<session_id>/reorder', methods=['POST'])
def reorder_fields(session_id):
    """Reorder form fields."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    field_order = data.get('order', [])  # List of field IDs in new order

    try:
        session = form_sessions[session_id]
        config_dict = session["config"]

        # Reorder fields
        field_map = {f['id']: f for f in config_dict['fields']}
        reordered = []
        for field_id in field_order:
            if field_id in field_map:
                reordered.append(field_map[field_id])

        # Add any fields not in the order list (shouldn't happen, but safety)
        for field in config_dict['fields']:
            if field not in reordered:
                reordered.append(field)

        config_dict['fields'] = reordered

        # Regenerate HTML
        fields = [FormField(**f) for f in config_dict['fields']]
        config = FormConfig(
            title=config_dict['title'],
            description=config_dict['description'],
            fields=fields
        )
        generator = FormGenerator()
        html = generator.generate(config)

        session["html"] = html

        return jsonify({
            "success": True,
            "html": html
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/form/<session_id>/export/html', methods=['GET'])
def export_html(session_id):
    """Export form as HTML file."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    session = form_sessions[session_id]
    html = session["html"]

    return Response(
        html,
        mimetype='text/html',
        headers={
            'Content-Disposition': f'attachment; filename=form_{session_id[:8]}.html'
        }
    )


@app.route('/api/form/<session_id>/export/json', methods=['GET'])
def export_json(session_id):
    """Export form configuration as JSON."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    session = form_sessions[session_id]
    config = session["config"]

    return Response(
        json.dumps(config, indent=2),
        mimetype='application/json',
        headers={
            'Content-Disposition': f'attachment; filename=form_{session_id[:8]}.json'
        }
    )


@app.route('/api/form/<session_id>/save', methods=['POST'])
def save_form(session_id):
    """Save form to the generated_forms directory."""
    if session_id not in form_sessions:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json()
    filename = data.get('filename', f'form_{session_id[:8]}')

    # Sanitize filename
    filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-'))

    try:
        session = form_sessions[session_id]

        # Save HTML
        html_path = f'generated_forms/{filename}.html'
        os.makedirs('generated_forms', exist_ok=True)
        with open(html_path, 'w') as f:
            f.write(session["html"])

        # Save JSON config
        json_path = f'generated_forms/{filename}.json'
        with open(json_path, 'w') as f:
            json.dump(session["config"], f, indent=2)

        return jsonify({
            "success": True,
            "html_path": html_path,
            "json_path": json_path
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/preview/<session_id>')
def preview_form(session_id):
    """Preview the generated form in a standalone page."""
    if session_id not in form_sessions:
        return "Session not found", 404

    session = form_sessions[session_id]
    return session["html"]


if __name__ == '__main__':
    # Ensure generated_forms directory exists
    os.makedirs('generated_forms', exist_ok=True)

    # Run the development server
    app.run(debug=True, host='0.0.0.0', port=5000)
