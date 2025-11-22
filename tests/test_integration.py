"""
Integration Tests for Form Analytics System
Tests components working together and API endpoints
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import (
    init_databases, get_dynamic_session, get_static_session,
    DynamicForm, DynamicFormField, DynamicFormResponse, DynamicResponseValue,
    DatabaseSync
)
from analytics import NLPQueryEngine, QueryExecutor, ChartGenerator


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database operations"""

    @classmethod
    def setUpClass(cls):
        """Initialize databases once for all tests"""
        init_databases()

    def test_form_creation_and_retrieval(self):
        """Test creating and retrieving a form"""
        session = get_dynamic_session()

        try:
            # Create a form
            form = DynamicForm(
                session_id='test-integration-001',
                title='Integration Test Form',
                description='Test form for integration testing'
            )
            session.add(form)
            session.flush()

            # Add a field
            field = DynamicFormField(
                field_id='test_field',
                form_id=form.id,
                label='Test Field',
                field_type='text',
                name='test_field'
            )
            session.add(field)
            session.commit()

            # Retrieve the form
            retrieved = session.query(DynamicForm).filter_by(
                session_id='test-integration-001'
            ).first()

            self.assertIsNotNone(retrieved)
            self.assertEqual(retrieved.title, 'Integration Test Form')
            self.assertEqual(len(retrieved.fields), 1)

        finally:
            # Cleanup
            session.query(DynamicFormField).filter_by(
                form_id=form.id
            ).delete()
            session.query(DynamicForm).filter_by(
                session_id='test-integration-001'
            ).delete()
            session.commit()
            session.close()

    def test_response_submission(self):
        """Test submitting a response to a form"""
        session = get_dynamic_session()

        try:
            # Create form
            form = DynamicForm(
                session_id='test-response-001',
                title='Response Test Form'
            )
            session.add(form)
            session.flush()

            # Add field
            field = DynamicFormField(
                field_id='name',
                form_id=form.id,
                label='Name',
                field_type='text',
                name='name'
            )
            session.add(field)
            session.flush()

            # Create response
            response = DynamicFormResponse(
                form_id=form.id,
                ip_address='127.0.0.1'
            )
            session.add(response)
            session.flush()

            # Add response value
            value = DynamicResponseValue(
                response_id=response.id,
                field_name='name',
                value='Test User',
                field_type='text'
            )
            session.add(value)
            session.commit()

            # Verify
            retrieved_response = session.query(DynamicFormResponse).filter_by(
                form_id=form.id
            ).first()

            self.assertIsNotNone(retrieved_response)
            self.assertEqual(len(retrieved_response.values), 1)
            self.assertEqual(retrieved_response.values[0].value, 'Test User')

        finally:
            # Cleanup
            session.query(DynamicResponseValue).filter(
                DynamicResponseValue.response_id == response.id
            ).delete()
            session.query(DynamicFormResponse).filter_by(
                form_id=form.id
            ).delete()
            session.query(DynamicFormField).filter_by(
                form_id=form.id
            ).delete()
            session.query(DynamicForm).filter_by(
                session_id='test-response-001'
            ).delete()
            session.commit()
            session.close()

    def test_database_sync(self):
        """Test syncing from dynamic to static database"""
        dynamic_session = get_dynamic_session()
        static_session = get_static_session()
        sync = DatabaseSync(stability_threshold=1, time_threshold_minutes=0)

        try:
            # Create form in dynamic
            form = DynamicForm(
                session_id='test-sync-001',
                title='Sync Test Form',
                response_count=5  # Above threshold
            )
            dynamic_session.add(form)
            dynamic_session.commit()

            # Run sync
            result = sync.force_sync_form('test-sync-001')
            self.assertTrue(result)

            # Verify in static
            from database.models import StaticForm
            static_form = static_session.query(StaticForm).filter_by(
                session_id='test-sync-001'
            ).first()

            self.assertIsNotNone(static_form)
            self.assertEqual(static_form.title, 'Sync Test Form')

        finally:
            # Cleanup
            dynamic_session.query(DynamicForm).filter_by(
                session_id='test-sync-001'
            ).delete()
            dynamic_session.commit()
            dynamic_session.close()

            from database.models import StaticForm
            static_session.query(StaticForm).filter_by(
                session_id='test-sync-001'
            ).delete()
            static_session.commit()
            static_session.close()


class TestAnalyticsIntegration(unittest.TestCase):
    """Integration tests for analytics components"""

    @classmethod
    def setUpClass(cls):
        """Set up test data"""
        init_databases()

        # Create test form with responses
        session = get_dynamic_session()
        try:
            form = DynamicForm(
                session_id='analytics-test-001',
                title='Analytics Test Form',
                response_count=10
            )
            session.add(form)
            session.flush()

            field = DynamicFormField(
                field_id='rating',
                form_id=form.id,
                label='Rating',
                field_type='select',
                name='rating'
            )
            session.add(field)
            session.flush()

            # Add responses
            for i in range(10):
                response = DynamicFormResponse(
                    form_id=form.id,
                    ip_address=f'192.168.1.{i}'
                )
                session.add(response)
                session.flush()

                value = DynamicResponseValue(
                    response_id=response.id,
                    field_name='rating',
                    value=str((i % 5) + 1),
                    field_type='select'
                )
                session.add(value)

            session.commit()
            cls.test_form_id = form.session_id

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

        # Sync to static for querying
        sync = DatabaseSync(stability_threshold=1, time_threshold_minutes=0)
        sync.force_sync_form('analytics-test-001')

    @classmethod
    def tearDownClass(cls):
        """Clean up test data"""
        dynamic_session = get_dynamic_session()
        static_session = get_static_session()

        try:
            # Clean dynamic
            form = dynamic_session.query(DynamicForm).filter_by(
                session_id='analytics-test-001'
            ).first()
            if form:
                dynamic_session.query(DynamicResponseValue).filter(
                    DynamicResponseValue.response_id.in_(
                        dynamic_session.query(DynamicFormResponse.id).filter_by(form_id=form.id)
                    )
                ).delete(synchronize_session=False)
                dynamic_session.query(DynamicFormResponse).filter_by(form_id=form.id).delete()
                dynamic_session.query(DynamicFormField).filter_by(form_id=form.id).delete()
                dynamic_session.delete(form)
            dynamic_session.commit()

            # Clean static
            from database.models import StaticForm, StaticFormField, StaticFormResponse, StaticResponseValue
            static_form = static_session.query(StaticForm).filter_by(
                session_id='analytics-test-001'
            ).first()
            if static_form:
                static_session.query(StaticResponseValue).filter(
                    StaticResponseValue.response_id.in_(
                        static_session.query(StaticFormResponse.id).filter_by(form_id=static_form.id)
                    )
                ).delete(synchronize_session=False)
                static_session.query(StaticFormResponse).filter_by(form_id=static_form.id).delete()
                static_session.query(StaticFormField).filter_by(form_id=static_form.id).delete()
                static_session.delete(static_form)
            static_session.commit()

        finally:
            dynamic_session.close()
            static_session.close()

    def test_nlp_to_sql_to_results(self):
        """Test full NLP query to results pipeline"""
        executor = QueryExecutor(use_static=True)

        result = executor.execute_natural_query(
            "How many forms do we have?",
            save_history=False
        )

        self.assertTrue(result['success'])
        self.assertIn('results', result)
        self.assertIn('sql_query', result)

    def test_query_with_chart_generation(self):
        """Test query results to chart generation"""
        executor = QueryExecutor(use_static=True)
        chart_gen = ChartGenerator()

        # Execute query
        result = executor.execute_natural_query(
            "List all forms",
            save_history=False
        )

        self.assertTrue(result['success'])

        # Generate chart
        if result['results']['rows']:
            chart_config = chart_gen.generate(
                result['results'],
                'bar',
                'Forms Overview'
            )

            self.assertIn('type', chart_config)
            self.assertIn('data', chart_config)

    def test_forms_summary(self):
        """Test getting forms summary"""
        executor = QueryExecutor(use_static=True)
        summary = executor.get_forms_summary()

        self.assertIn('total_forms', summary)
        self.assertIn('forms', summary)
        self.assertGreaterEqual(summary['total_forms'], 0)

    def test_query_history_tracking(self):
        """Test that queries are saved to history"""
        executor = QueryExecutor(use_static=True)

        # Execute a query
        executor.execute_natural_query(
            "Count all responses",
            save_history=True
        )

        # Check history
        history = executor.get_query_history(limit=5)
        self.assertIsInstance(history, list)


class TestAPIIntegration(unittest.TestCase):
    """Integration tests for Flask API endpoints"""

    @classmethod
    def setUpClass(cls):
        """Set up Flask test client"""
        init_databases()

        from analytics_app import app
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_forms_endpoint(self):
        """Test GET /api/forms endpoint"""
        response = self.client.get('/api/forms')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('forms', data)
        self.assertIn('total_forms', data)

    def test_query_endpoint(self):
        """Test POST /api/query endpoint"""
        response = self.client.post(
            '/api/query',
            data=json.dumps({'query': 'How many forms?'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)

    def test_query_endpoint_missing_query(self):
        """Test query endpoint with missing query"""
        response = self.client.post(
            '/api/query',
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_sync_status_endpoint(self):
        """Test GET /api/sync/status endpoint"""
        response = self.client.get('/api/sync/status')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('dynamic_forms', data)
        self.assertIn('static_forms', data)

    def test_query_suggestions_endpoint(self):
        """Test GET /api/query/suggestions endpoint"""
        response = self.client.get('/api/query/suggestions')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('suggestions', data)
        self.assertIsInstance(data['suggestions'], list)

    def test_chart_endpoint(self):
        """Test POST /api/chart endpoint"""
        chart_data = {
            'data': {
                'columns': ['label', 'value'],
                'rows': [
                    {'label': 'A', 'value': 10},
                    {'label': 'B', 'value': 20}
                ]
            },
            'chart_type': 'bar',
            'title': 'Test Chart'
        }

        response = self.client.post(
            '/api/chart',
            data=json.dumps(chart_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('type', data)
        self.assertEqual(data['type'], 'bar')

    def test_query_history_endpoint(self):
        """Test GET /api/query/history endpoint"""
        response = self.client.get('/api/query/history?limit=10')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('history', data)

    def test_explain_endpoint(self):
        """Test POST /api/query/explain endpoint"""
        response = self.client.post(
            '/api/query/explain',
            data=json.dumps({'query': 'Count responses by form'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('generated_sql', data)
        self.assertIn('intent', data)


class TestEndToEndWorkflow(unittest.TestCase):
    """End-to-end workflow tests"""

    @classmethod
    def setUpClass(cls):
        init_databases()
        from analytics_app import app
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_complete_workflow(self):
        """Test complete workflow: import form -> submit -> query -> visualize"""

        # Step 1: Import a form
        form_config = {
            'config': {
                'session_id': 'e2e-test-001',
                'title': 'E2E Test Form',
                'description': 'End-to-end test form',
                'fields': [
                    {
                        'id': 'name',
                        'label': 'Name',
                        'field_type': 'text',
                        'name': 'name',
                        'required': True
                    },
                    {
                        'id': 'rating',
                        'label': 'Rating',
                        'field_type': 'select',
                        'name': 'rating',
                        'options': ['1', '2', '3', '4', '5']
                    }
                ]
            }
        }

        response = self.client.post(
            '/api/import/form',
            data=json.dumps(form_config),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        session_id = data['session_id']

        # Step 2: Submit responses
        for i in range(3):
            response = self.client.post(
                f'/api/submit/{session_id}',
                data=json.dumps({
                    'name': f'User {i}',
                    'rating': str((i % 5) + 1)
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)

        # Step 3: Force sync
        response = self.client.post(f'/api/sync/force/{session_id}')
        self.assertEqual(response.status_code, 200)

        # Step 4: Query the data
        response = self.client.post(
            '/api/query',
            data=json.dumps({'query': 'How many responses?'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Cleanup
        session = get_dynamic_session()
        try:
            form = session.query(DynamicForm).filter_by(
                session_id=session_id
            ).first()
            if form:
                session.query(DynamicResponseValue).filter(
                    DynamicResponseValue.response_id.in_(
                        session.query(DynamicFormResponse.id).filter_by(form_id=form.id)
                    )
                ).delete(synchronize_session=False)
                session.query(DynamicFormResponse).filter_by(form_id=form.id).delete()
                session.query(DynamicFormField).filter_by(form_id=form.id).delete()
                session.delete(form)
            session.commit()
        finally:
            session.close()


if __name__ == '__main__':
    unittest.main(verbosity=2)
