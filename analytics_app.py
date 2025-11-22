"""
Analytics Application API
Provides endpoints for form response analytics, NLP queries, and visualizations
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory

from database import (
    init_databases, get_dynamic_session, get_static_session,
    DynamicForm, DynamicFormField, DynamicFormResponse, DynamicResponseValue,
    DatabaseSync
)
from analytics import NLPQueryEngine, QueryExecutor, ChartGenerator

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'analytics-secret-key')

# Initialize components
init_databases()
query_executor = QueryExecutor(use_static=True)
chart_generator = ChartGenerator()
db_sync = DatabaseSync()


# ============ PAGE ROUTES ============

@app.route('/')
def index():
    """Main analytics dashboard"""
    return render_template('analytics/dashboard.html')


@app.route('/app')
def mobile_app():
    """Mobile app version (PWA)"""
    return render_template('analytics/app.html')


# ============ API ROUTES ============

@app.route('/api/query', methods=['POST'])
def execute_query():
    """
    Execute a natural language query.

    Body:
        query: Natural language query string

    Returns:
        Query results with SQL and insights
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400

    query = data['query'].strip()
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400

    result = query_executor.execute_natural_query(query)
    return jsonify(result)


@app.route('/api/query/raw', methods=['POST'])
def execute_raw_sql():
    """
    Execute a raw SQL query.

    Body:
        sql: SQL query string

    Returns:
        Query results
    """
    data = request.get_json()
    if not data or 'sql' not in data:
        return jsonify({'error': 'SQL query is required'}), 400

    try:
        result = query_executor.execute_sql(data['sql'])
        return jsonify({'success': True, 'results': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/query/explain', methods=['POST'])
def explain_query():
    """
    Explain how a natural language query will be interpreted.

    Body:
        query: Natural language query string

    Returns:
        Query explanation and generated SQL
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400

    nlp_engine = NLPQueryEngine()
    explanation = nlp_engine.explain(data['query'])
    return jsonify(explanation)


@app.route('/api/query/history')
def get_query_history():
    """Get recent query history"""
    limit = request.args.get('limit', 50, type=int)
    history = query_executor.get_query_history(limit)
    return jsonify({'history': history})


@app.route('/api/query/suggestions')
def get_query_suggestions():
    """Get suggested queries"""
    session_id = request.args.get('session_id')
    suggestions = query_executor.suggest_queries(session_id)
    return jsonify({'suggestions': suggestions})


# ============ FORM DATA ROUTES ============

@app.route('/api/forms')
def list_forms():
    """Get list of all forms"""
    summary = query_executor.get_forms_summary()
    return jsonify(summary)


@app.route('/api/forms/<session_id>')
def get_form(session_id):
    """Get form details by session ID"""
    response_data = query_executor.get_response_data(session_id)
    if 'error' in response_data:
        return jsonify(response_data), 404
    return jsonify(response_data)


@app.route('/api/forms/<session_id>/fields')
def get_form_fields(session_id):
    """Get form fields"""
    fields = query_executor.get_form_fields(session_id)
    return jsonify({'fields': fields})


@app.route('/api/forms/<session_id>/responses')
def get_form_responses(session_id):
    """Get form responses"""
    limit = request.args.get('limit', 100, type=int)
    response_data = query_executor.get_response_data(session_id, limit)
    return jsonify(response_data)


@app.route('/api/forms/<session_id>/stats/<field_name>')
def get_field_stats(session_id, field_name):
    """Get statistics for a specific field"""
    stats = query_executor.get_field_statistics(session_id, field_name)
    return jsonify(stats)


# ============ SUBMISSION ROUTES ============

@app.route('/api/submit/<session_id>', methods=['POST'])
def submit_form_response(session_id):
    """
    Submit a form response to the dynamic database.

    Body:
        Form field values

    Returns:
        Submission confirmation
    """
    session = get_dynamic_session()

    try:
        # Find the form
        form = session.query(DynamicForm).filter_by(session_id=session_id).first()

        if not form:
            return jsonify({'error': 'Form not found'}), 404

        # Create response
        response = DynamicFormResponse(
            form_id=form.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        session.add(response)
        session.flush()

        # Add response values
        data = request.get_json() or request.form.to_dict()

        for field in form.fields:
            value = data.get(field.name, '')
            response_value = DynamicResponseValue(
                response_id=response.id,
                field_name=field.name,
                value=str(value) if value else '',
                field_type=field.field_type
            )
            session.add(response_value)

        # Update response count
        form.response_count += 1
        form.sync_status = 'modified'

        session.commit()

        return jsonify({
            'success': True,
            'response_id': response.id,
            'message': 'Response submitted successfully'
        })

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


# ============ CHART ROUTES ============

@app.route('/api/chart', methods=['POST'])
def generate_chart():
    """
    Generate a chart from query results.

    Body:
        data: Query result data
        chart_type: Type of chart (bar, line, pie, etc.)
        title: Chart title

    Returns:
        Chart.js configuration
    """
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({'error': 'Data is required'}), 400

    chart_type = data.get('chart_type', 'bar')
    title = data.get('title', '')
    options = data.get('options', {})

    chart_config = chart_generator.generate(
        data['data'],
        chart_type,
        title,
        options
    )

    return jsonify(chart_config)


@app.route('/api/chart/auto', methods=['POST'])
def auto_generate_chart():
    """
    Automatically generate a chart with optimal type.

    Body:
        data: Query result data
        intent: Query intent (optional)
        title: Chart title

    Returns:
        Chart.js configuration with auto-selected type
    """
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({'error': 'Data is required'}), 400

    intent = data.get('intent')
    title = data.get('title', '')

    # Auto-select chart type
    chart_type = chart_generator.auto_select_chart_type(data['data'], intent)

    chart_config = chart_generator.generate(
        data['data'],
        chart_type,
        title
    )

    return jsonify({
        'chart_type': chart_type,
        'config': chart_config
    })


@app.route('/api/chart/distribution/<session_id>/<field_name>')
def generate_distribution_chart(session_id, field_name):
    """Generate a distribution chart for a specific field"""
    stats = query_executor.get_field_statistics(session_id, field_name)

    if 'error' in stats:
        return jsonify(stats), 404

    chart_config = chart_generator.generate_from_distribution(
        stats.get('distribution', []),
        'pie',
        f"Distribution of {field_name}"
    )

    return jsonify(chart_config)


# ============ SYNC ROUTES ============

@app.route('/api/sync/status')
def get_sync_status():
    """Get database sync status"""
    status = db_sync.get_sync_status()
    return jsonify(status)


@app.route('/api/sync/run', methods=['POST'])
def run_sync():
    """Run database synchronization"""
    results = db_sync.sync_all_pending()
    return jsonify(results)


@app.route('/api/sync/force/<session_id>', methods=['POST'])
def force_sync(session_id):
    """Force sync a specific form"""
    success = db_sync.force_sync_form(session_id)
    return jsonify({'success': success})


# ============ IMPORT ROUTES ============

@app.route('/api/import/form', methods=['POST'])
def import_form():
    """
    Import a form configuration into the dynamic database.

    Body:
        config: Form configuration object

    Returns:
        Import confirmation with session ID
    """
    data = request.get_json()
    if not data or 'config' not in data:
        return jsonify({'error': 'Form configuration is required'}), 400

    config = data['config']
    session = get_dynamic_session()

    try:
        # Create form
        form = DynamicForm(
            session_id=config.get('session_id', str(uuid.uuid4())),
            title=config.get('title', 'Imported Form'),
            description=config.get('description', ''),
            action=config.get('action', '#'),
            method=config.get('method', 'POST')
        )
        session.add(form)
        session.flush()

        # Add fields
        for i, field_config in enumerate(config.get('fields', [])):
            field = DynamicFormField(
                field_id=field_config.get('id', f'field_{i}'),
                form_id=form.id,
                label=field_config.get('label', f'Field {i}'),
                field_type=field_config.get('field_type', 'text'),
                name=field_config.get('name', f'field_{i}'),
                required=field_config.get('required', False),
                placeholder=field_config.get('placeholder', ''),
                description=field_config.get('description', ''),
                options=field_config.get('options', []),
                validation=field_config.get('validation', {}),
                default_value=field_config.get('default_value', ''),
                field_order=i
            )
            session.add(field)

        session.commit()

        return jsonify({
            'success': True,
            'session_id': form.session_id,
            'form_id': form.id,
            'message': 'Form imported successfully'
        })

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


@app.route('/api/import/responses/<session_id>', methods=['POST'])
def import_responses(session_id):
    """
    Import responses for a form.

    Body:
        responses: Array of response objects

    Returns:
        Import confirmation
    """
    data = request.get_json()
    if not data or 'responses' not in data:
        return jsonify({'error': 'Responses array is required'}), 400

    session = get_dynamic_session()

    try:
        form = session.query(DynamicForm).filter_by(session_id=session_id).first()

        if not form:
            return jsonify({'error': 'Form not found'}), 404

        imported_count = 0

        for resp_data in data['responses']:
            response = DynamicFormResponse(
                form_id=form.id,
                submitted_at=datetime.fromisoformat(resp_data.get('submitted_at', datetime.utcnow().isoformat())),
                ip_address=resp_data.get('ip_address', ''),
                user_agent=resp_data.get('user_agent', '')
            )
            session.add(response)
            session.flush()

            values = resp_data.get('values', {})
            for field_name, value in values.items():
                response_value = DynamicResponseValue(
                    response_id=response.id,
                    field_name=field_name,
                    value=str(value) if value else ''
                )
                session.add(response_value)

            imported_count += 1

        form.response_count += imported_count
        form.sync_status = 'modified'

        session.commit()

        return jsonify({
            'success': True,
            'imported_count': imported_count,
            'message': f'Imported {imported_count} responses'
        })

    except Exception as e:
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        session.close()


# ============ PWA ROUTES ============

@app.route('/manifest.json')
def manifest():
    """Serve PWA manifest"""
    return jsonify({
        'name': 'Form Analytics',
        'short_name': 'FormAnalytics',
        'description': 'AI-powered form response analytics',
        'start_url': '/app',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#4a90d9',
        'icons': [
            {
                'src': '/static/icons/icon-192.png',
                'sizes': '192x192',
                'type': 'image/png'
            },
            {
                'src': '/static/icons/icon-512.png',
                'sizes': '512x512',
                'type': 'image/png'
            }
        ]
    })


@app.route('/sw.js')
def service_worker():
    """Serve service worker for PWA"""
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')


# ============ ERROR HANDLERS ============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
