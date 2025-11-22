"""
Unit Tests for Form Analytics System
Tests individual components in isolation
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from analytics.nlp_engine import NLPQueryEngine, QueryIntent
from analytics.chart_generator import ChartGenerator, ChartType
from database.config import get_database_url


class TestNLPEngine(unittest.TestCase):
    """Unit tests for NLP Query Engine"""

    def setUp(self):
        self.engine = NLPQueryEngine()

    def test_intent_detection_count(self):
        """Test count intent detection"""
        queries = [
            "How many responses do we have?",
            "Count all forms",
            "Total number of submissions"
        ]
        for query in queries:
            parsed = self.engine.parse(query)
            self.assertEqual(parsed.intent, QueryIntent.COUNT,
                           f"Failed for query: {query}")

    def test_intent_detection_list(self):
        """Test list intent detection"""
        queries = [
            "Show me all responses",
            "List the forms",
            "Find submissions from today"
        ]
        for query in queries:
            parsed = self.engine.parse(query)
            self.assertEqual(parsed.intent, QueryIntent.LIST,
                           f"Failed for query: {query}")

    def test_intent_detection_aggregate(self):
        """Test aggregate intent detection"""
        queries = [
            "What is the average rating?",
            "Sum of all values",
            "Maximum response count"
        ]
        for query in queries:
            parsed = self.engine.parse(query)
            self.assertEqual(parsed.intent, QueryIntent.AGGREGATE,
                           f"Failed for query: {query}")

    def test_limit_parsing(self):
        """Test limit extraction from queries"""
        test_cases = [
            ("Show top 10 responses", 10),
            ("First 5 forms", 5),
            ("Last 20 submissions", 20),
            ("Show 100 results", 100)
        ]
        for query, expected_limit in test_cases:
            parsed = self.engine.parse(query)
            self.assertEqual(parsed.limit, expected_limit,
                           f"Failed for query: {query}")

    def test_time_range_parsing(self):
        """Test time range extraction"""
        queries_with_time = [
            "Responses from today",
            "Submissions this week",
            "Forms from last month"
        ]
        for query in queries_with_time:
            parsed = self.engine.parse(query)
            self.assertIsNotNone(parsed.time_range,
                               f"Time range not detected for: {query}")

    def test_group_by_parsing(self):
        """Test GROUP BY extraction"""
        test_cases = [
            ("Count responses group by form", "form"),
            ("Responses per day", "day"),
            ("Submissions by category", "category")
        ]
        for query, expected_group in test_cases:
            parsed = self.engine.parse(query)
            self.assertEqual(parsed.group_by, expected_group,
                           f"Failed for query: {query}")

    def test_sql_generation_count(self):
        """Test SQL generation for count queries"""
        query = "How many responses do we have?"
        sql = self.engine.to_sql(query)
        self.assertIn("COUNT", sql.upper())
        self.assertIn("FROM", sql.upper())

    def test_sql_generation_with_limit(self):
        """Test SQL generation with LIMIT"""
        query = "Show top 5 forms"
        sql = self.engine.to_sql(query)
        self.assertIn("LIMIT 5", sql)

    def test_table_detection(self):
        """Test correct table detection"""
        test_cases = [
            ("Show all forms", "forms"),
            ("List responses", "form_responses"),
            ("Get all answers", "response_values")
        ]
        for query, expected_table in test_cases:
            parsed = self.engine.parse(query)
            self.assertEqual(parsed.target_table, expected_table,
                           f"Failed for query: {query}")

    def test_explain_output(self):
        """Test explain function returns all expected keys"""
        query = "Count responses from today"
        explanation = self.engine.explain(query)

        expected_keys = ['original_query', 'intent', 'target_table',
                        'generated_sql', 'conditions', 'time_range']
        for key in expected_keys:
            self.assertIn(key, explanation)


class TestChartGenerator(unittest.TestCase):
    """Unit tests for Chart Generator"""

    def setUp(self):
        self.generator = ChartGenerator()

    def test_bar_chart_generation(self):
        """Test bar chart configuration generation"""
        data = {
            'columns': ['category', 'count'],
            'rows': [
                {'category': 'A', 'count': 10},
                {'category': 'B', 'count': 20}
            ]
        }
        config = self.generator.generate(data, 'bar', 'Test Chart')

        self.assertEqual(config['type'], 'bar')
        self.assertIn('data', config)
        self.assertIn('options', config)
        self.assertEqual(len(config['data']['labels']), 2)

    def test_pie_chart_generation(self):
        """Test pie chart configuration generation"""
        data = {
            'columns': ['label', 'value'],
            'rows': [
                {'label': 'Yes', 'value': 60},
                {'label': 'No', 'value': 40}
            ]
        }
        config = self.generator.generate(data, 'pie', 'Distribution')

        self.assertEqual(config['type'], 'pie')
        self.assertEqual(len(config['data']['datasets'][0]['data']), 2)

    def test_line_chart_generation(self):
        """Test line chart configuration generation"""
        data = {
            'columns': ['date', 'count'],
            'rows': [
                {'date': '2024-01-01', 'count': 5},
                {'date': '2024-01-02', 'count': 8},
                {'date': '2024-01-03', 'count': 12}
            ]
        }
        config = self.generator.generate(data, 'line', 'Trend')

        self.assertEqual(config['type'], 'line')
        self.assertEqual(len(config['data']['labels']), 3)

    def test_empty_data_handling(self):
        """Test handling of empty data"""
        data = {'columns': [], 'rows': []}
        config = self.generator.generate(data, 'bar', 'Empty')

        self.assertIn('No Data', str(config))

    def test_auto_chart_selection(self):
        """Test automatic chart type selection"""
        # Categorical data (few items) -> pie
        categorical_data = {
            'columns': ['cat', 'val'],
            'rows': [{'cat': 'A', 'val': 1}] * 5
        }
        chart_type = self.generator.auto_select_chart_type(categorical_data, 'distribution')
        self.assertEqual(chart_type, 'pie')

        # Time series data -> line
        time_data = {
            'columns': ['date', 'count'],
            'rows': [{'date': '2024-01-01', 'count': 1}] * 10
        }
        chart_type = self.generator.auto_select_chart_type(time_data, 'trend')
        self.assertEqual(chart_type, 'line')

    def test_color_palette_generation(self):
        """Test color palette has enough colors"""
        # Generator should have at least 10 colors
        self.assertGreaterEqual(len(self.generator.default_colors), 10)

    def test_distribution_chart_generation(self):
        """Test chart from distribution data"""
        distribution = [
            {'value': 'Option A', 'count': 30},
            {'value': 'Option B', 'count': 50},
            {'value': 'Option C', 'count': 20}
        ]
        config = self.generator.generate_from_distribution(
            distribution, 'pie', 'Test Distribution'
        )

        self.assertEqual(config['type'], 'pie')
        self.assertEqual(len(config['data']['labels']), 3)


class TestDatabaseConfig(unittest.TestCase):
    """Unit tests for Database Configuration"""

    def test_sqlite_url_generation(self):
        """Test SQLite URL generation"""
        url = get_database_url('sqlite', '', '', 'test_db', '', '')
        self.assertIn('sqlite:///', url)
        self.assertIn('test_db.db', url)

    def test_postgresql_url_generation(self):
        """Test PostgreSQL URL generation"""
        url = get_database_url(
            'postgresql', 'localhost', '5432',
            'testdb', 'user', 'password'
        )
        self.assertIn('postgresql://', url)
        self.assertIn('localhost:5432', url)
        self.assertIn('testdb', url)

    def test_postgresql_ssl_url(self):
        """Test PostgreSQL URL with SSL"""
        url = get_database_url(
            'postgresql', 'host', '5432',
            'db', 'user', 'pass', ssl=True
        )
        self.assertIn('sslmode=require', url)

    def test_mysql_url_generation(self):
        """Test MySQL URL generation"""
        url = get_database_url(
            'mysql', 'localhost', '3306',
            'testdb', 'root', 'password'
        )
        self.assertIn('mysql+pymysql://', url)
        self.assertIn('localhost:3306', url)

    def test_invalid_db_type(self):
        """Test error on invalid database type"""
        with self.assertRaises(ValueError):
            get_database_url('invalid', '', '', '', '', '')


class TestFormGenerator(unittest.TestCase):
    """Unit tests for Form Generator logic"""

    def setUp(self):
        from form_generator import AIFormParser
        self.parser = AIFormParser()

    def test_field_type_detection_email(self):
        """Test email field type detection"""
        test_texts = [
            "Email address",
            "Your email",
            "E-mail"
        ]
        for text in test_texts:
            field_type = self.parser._infer_field_type(text)
            self.assertEqual(field_type, "email", f"Failed for: {text}")

    def test_field_type_detection_phone(self):
        """Test phone field type detection"""
        test_texts = [
            "Phone number",
            "Telephone",
            "Mobile number"
        ]
        for text in test_texts:
            field_type = self.parser._infer_field_type(text)
            self.assertEqual(field_type, "tel", f"Failed for: {text}")

    def test_field_type_detection_date(self):
        """Test date field type detection"""
        test_texts = [
            "Date of birth",
            "Birthday",
            "Start date"
        ]
        for text in test_texts:
            field_type = self.parser._infer_field_type(text)
            self.assertEqual(field_type, "date", f"Failed for: {text}")

    def test_required_field_detection(self):
        """Test required field marker detection"""
        required_texts = [
            "Name *",
            "Email (required)",
            "Phone required"
        ]
        for text in required_texts:
            is_required = '*' in text or 'required' in text.lower()
            self.assertTrue(is_required, f"Should be required: {text}")

    def test_options_extraction(self):
        """Test dropdown options extraction"""
        text = "Country: [USA, Canada, UK]"
        # Extract options using regex
        import re
        match = re.search(r'\[(.*?)\]', text)
        if match:
            options = [o.strip() for o in match.group(1).split(',')]
            self.assertEqual(len(options), 3)
            self.assertIn("USA", options)


if __name__ == '__main__':
    # Run tests with verbosity
    unittest.main(verbosity=2)
