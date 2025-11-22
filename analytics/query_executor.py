"""
Query Executor for Form Response Analytics
Executes SQL queries and returns formatted results with caching and optimization
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database.models import (
    get_static_session, get_dynamic_session, QueryHistory,
    StaticForm, StaticFormField, StaticFormResponse, StaticResponseValue
)
from .nlp_engine import NLPQueryEngine

logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes queries against the form response database.
    Supports both natural language and raw SQL queries.
    """

    def __init__(self, use_static: bool = True):
        """
        Initialize the query executor.

        Args:
            use_static: If True, query from static database; otherwise use dynamic
        """
        self.use_static = use_static
        self.nlp_engine = NLPQueryEngine()
        self._query_cache = {}

    def execute_natural_query(self, query: str, save_history: bool = True) -> Dict[str, Any]:
        """
        Execute a natural language query.

        Args:
            query: Natural language query string
            save_history: Whether to save this query to history

        Returns:
            Dictionary containing results and metadata
        """
        start_time = time.time()

        try:
            # Convert to SQL
            sql = self.nlp_engine.to_sql(query)
            explanation = self.nlp_engine.explain(query)

            # Execute the SQL
            result = self.execute_sql(sql)

            execution_time = (time.time() - start_time) * 1000

            # Save to history
            if save_history:
                self._save_query_history(
                    natural_query=query,
                    sql_query=sql,
                    execution_time=execution_time,
                    result_count=len(result.get('rows', [])),
                    success=True
                )

            return {
                'success': True,
                'natural_query': query,
                'sql_query': sql,
                'explanation': explanation,
                'results': result,
                'execution_time_ms': round(execution_time, 2),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            error_message = str(e)

            if save_history:
                self._save_query_history(
                    natural_query=query,
                    sql_query=self.nlp_engine.to_sql(query) if query else '',
                    execution_time=execution_time,
                    result_count=0,
                    success=False,
                    error_message=error_message
                )

            logger.error(f"Query execution failed: {error_message}")

            return {
                'success': False,
                'natural_query': query,
                'error': error_message,
                'execution_time_ms': round(execution_time, 2),
                'timestamp': datetime.utcnow().isoformat()
            }

    def execute_sql(self, sql: str) -> Dict[str, Any]:
        """
        Execute a raw SQL query.

        Args:
            sql: SQL query string

        Returns:
            Dictionary containing columns and rows
        """
        session = get_static_session() if self.use_static else get_dynamic_session()

        try:
            result = session.execute(text(sql))

            # Get column names
            columns = list(result.keys()) if result.keys() else []

            # Get rows
            rows = []
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    # Convert datetime objects to ISO format strings
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    row_dict[col] = value
                rows.append(row_dict)

            return {
                'columns': columns,
                'rows': rows,
                'row_count': len(rows)
            }

        except SQLAlchemyError as e:
            logger.error(f"SQL execution error: {str(e)}")
            raise

        finally:
            session.close()

    def _save_query_history(self, natural_query: str, sql_query: str,
                           execution_time: float, result_count: int,
                           success: bool, error_message: str = None):
        """Save query to history"""
        session = get_static_session()

        try:
            history = QueryHistory(
                natural_query=natural_query,
                sql_query=sql_query,
                execution_time_ms=execution_time,
                result_count=result_count,
                success=success,
                error_message=error_message
            )
            session.add(history)
            session.commit()

        except Exception as e:
            logger.error(f"Failed to save query history: {str(e)}")
            session.rollback()

        finally:
            session.close()

    def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent query history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of query history entries
        """
        session = get_static_session()

        try:
            history = session.query(QueryHistory)\
                .order_by(QueryHistory.executed_at.desc())\
                .limit(limit)\
                .all()

            return [h.to_dict() for h in history]

        finally:
            session.close()

    def get_forms_summary(self) -> Dict[str, Any]:
        """Get summary of all forms in the database"""
        session = get_static_session() if self.use_static else get_dynamic_session()

        try:
            forms = session.query(StaticForm).all()

            return {
                'total_forms': len(forms),
                'forms': [{
                    'session_id': f.session_id,
                    'title': f.title,
                    'description': f.description,
                    'response_count': f.response_count,
                    'field_count': len(f.fields),
                    'created_at': f.created_at.isoformat() if f.created_at else None
                } for f in forms]
            }

        finally:
            session.close()

    def get_form_fields(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all fields for a specific form"""
        session = get_static_session() if self.use_static else get_dynamic_session()

        try:
            form = session.query(StaticForm).filter_by(session_id=session_id).first()

            if not form:
                return []

            return [field.to_dict() for field in form.fields]

        finally:
            session.close()

    def get_response_data(self, session_id: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get response data for a specific form.

        Args:
            session_id: Form session ID
            limit: Maximum number of responses

        Returns:
            Dictionary with form info and responses
        """
        session = get_static_session() if self.use_static else get_dynamic_session()

        try:
            form = session.query(StaticForm).filter_by(session_id=session_id).first()

            if not form:
                return {'error': 'Form not found'}

            # Get responses with values
            responses = session.query(StaticFormResponse)\
                .filter_by(form_id=form.id)\
                .order_by(StaticFormResponse.submitted_at.desc())\
                .limit(limit)\
                .all()

            return {
                'form': form.to_dict(),
                'responses': [r.to_dict() for r in responses],
                'total_responses': form.response_count
            }

        finally:
            session.close()

    def get_field_statistics(self, session_id: str, field_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific field.

        Args:
            session_id: Form session ID
            field_name: Field name to analyze

        Returns:
            Dictionary with field statistics
        """
        session = get_static_session() if self.use_static else get_dynamic_session()

        try:
            form = session.query(StaticForm).filter_by(session_id=session_id).first()

            if not form:
                return {'error': 'Form not found'}

            # Get all values for this field
            values = session.query(StaticResponseValue.value)\
                .join(StaticFormResponse)\
                .filter(StaticFormResponse.form_id == form.id)\
                .filter(StaticResponseValue.field_name == field_name)\
                .all()

            values_list = [v[0] for v in values if v[0]]

            stats = {
                'field_name': field_name,
                'total_responses': len(values_list),
                'unique_values': len(set(values_list))
            }

            # Calculate value distribution
            value_counts = {}
            for v in values_list:
                value_counts[v] = value_counts.get(v, 0) + 1

            # Sort by count
            sorted_counts = sorted(value_counts.items(), key=lambda x: x[1], reverse=True)

            stats['distribution'] = [
                {'value': v, 'count': c, 'percentage': round(c / len(values_list) * 100, 2)}
                for v, c in sorted_counts[:20]  # Top 20 values
            ]

            # Check if numeric for additional stats
            try:
                numeric_values = [float(v) for v in values_list]
                stats['min'] = min(numeric_values)
                stats['max'] = max(numeric_values)
                stats['average'] = sum(numeric_values) / len(numeric_values)
                stats['is_numeric'] = True
            except (ValueError, TypeError):
                stats['is_numeric'] = False

            return stats

        finally:
            session.close()

    def suggest_queries(self, session_id: str = None) -> List[str]:
        """
        Suggest example queries based on available data.

        Args:
            session_id: Optional form session ID for form-specific suggestions

        Returns:
            List of suggested natural language queries
        """
        suggestions = [
            "How many responses do we have?",
            "Show me the latest 10 responses",
            "What is the distribution of responses by date?",
            "Count responses grouped by form",
            "List all forms with their response counts"
        ]

        if session_id:
            session = get_static_session()
            try:
                form = session.query(StaticForm).filter_by(session_id=session_id).first()
                if form:
                    for field in form.fields[:3]:  # Add suggestions for first 3 fields
                        suggestions.append(f"What are the most common values for {field.label}?")
                        suggestions.append(f"Show distribution of {field.label}")
            finally:
                session.close()

        return suggestions


class AgenticQueryProcessor:
    """
    Agentic AI approach to query processing.
    Uses multi-step reasoning for complex queries.
    """

    def __init__(self):
        self.executor = QueryExecutor()
        self.nlp_engine = NLPQueryEngine()

    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a query using agentic approach.

        Steps:
        1. Understand the query intent
        2. Break down into sub-queries if needed
        3. Execute queries
        4. Aggregate and format results
        5. Generate insights

        Args:
            query: Natural language query

        Returns:
            Comprehensive result with insights
        """
        # Step 1: Analyze query complexity
        parsed = self.nlp_engine.parse(query)

        # Step 2: Determine if we need multiple queries
        sub_queries = self._decompose_query(query, parsed)

        # Step 3: Execute all queries
        results = []
        for sq in sub_queries:
            result = self.executor.execute_natural_query(sq, save_history=False)
            results.append(result)

        # Step 4: Aggregate results
        aggregated = self._aggregate_results(results)

        # Step 5: Generate insights
        insights = self._generate_insights(aggregated, parsed)

        return {
            'query': query,
            'sub_queries': sub_queries,
            'results': aggregated,
            'insights': insights,
            'visualization_suggestions': self._suggest_visualizations(parsed, aggregated)
        }

    def _decompose_query(self, query: str, parsed) -> List[str]:
        """Break complex queries into simpler sub-queries"""
        sub_queries = [query]

        # If comparing, we might need multiple queries
        if parsed.intent.value == 'compare':
            # Extract entities to compare
            pass  # Implement comparison decomposition

        # If asking for trend with comparison
        if 'compare' in query.lower() and 'trend' in query.lower():
            pass  # Implement trend comparison decomposition

        return sub_queries

    def _aggregate_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Aggregate results from multiple queries"""
        if len(results) == 1:
            return results[0]

        return {
            'combined': True,
            'individual_results': results,
            'total_rows': sum(r.get('results', {}).get('row_count', 0) for r in results)
        }

    def _generate_insights(self, results: Dict, parsed) -> List[str]:
        """Generate human-readable insights from results"""
        insights = []

        if not results.get('success', False):
            return ["Query execution failed. Please check the query syntax."]

        rows = results.get('results', {}).get('rows', [])

        if not rows:
            insights.append("No data found matching your query.")
            return insights

        row_count = len(rows)
        insights.append(f"Found {row_count} result(s).")

        # Add insights based on intent
        if parsed.intent.value == 'count':
            if rows and 'COUNT(*)' in rows[0]:
                insights.append(f"Total count: {rows[0]['COUNT(*)']}")

        elif parsed.intent.value == 'aggregate':
            for agg in parsed.aggregations:
                func = agg['function']
                field = agg['field']
                key = f"{func}({field})"
                if rows and key in rows[0]:
                    insights.append(f"{func} of {field}: {rows[0][key]}")

        return insights

    def _suggest_visualizations(self, parsed, results: Dict) -> List[Dict[str, str]]:
        """Suggest appropriate visualizations for the data"""
        suggestions = []

        intent = parsed.intent.value
        rows = results.get('results', {}).get('rows', [])

        if not rows:
            return suggestions

        if intent in ['distribution', 'group']:
            suggestions.append({
                'type': 'pie',
                'reason': 'Good for showing distribution of categories'
            })
            suggestions.append({
                'type': 'bar',
                'reason': 'Good for comparing values across categories'
            })

        elif intent == 'trend':
            suggestions.append({
                'type': 'line',
                'reason': 'Best for showing changes over time'
            })
            suggestions.append({
                'type': 'area',
                'reason': 'Good for cumulative trends'
            })

        elif intent == 'compare':
            suggestions.append({
                'type': 'bar',
                'reason': 'Good for side-by-side comparisons'
            })

        else:
            suggestions.append({
                'type': 'table',
                'reason': 'Best for detailed data examination'
            })

        return suggestions
