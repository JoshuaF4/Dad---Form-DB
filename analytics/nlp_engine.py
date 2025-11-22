"""
NLP to SQL Query Engine
Converts natural language queries to SQL for form response analysis
Uses pattern matching and agentic AI approach for accurate conversions
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    """Types of query intents"""
    COUNT = "count"
    LIST = "list"
    AGGREGATE = "aggregate"
    FILTER = "filter"
    GROUP = "group"
    COMPARE = "compare"
    TREND = "trend"
    DISTRIBUTION = "distribution"


@dataclass
class ParsedQuery:
    """Represents a parsed natural language query"""
    intent: QueryIntent
    target_table: str
    select_fields: List[str]
    conditions: List[Dict[str, Any]]
    group_by: Optional[str]
    order_by: Optional[str]
    order_direction: str
    limit: Optional[int]
    aggregations: List[Dict[str, str]]
    time_range: Optional[Dict[str, str]]


class NLPQueryEngine:
    """
    Converts natural language queries to SQL using pattern matching
    and intelligent parsing for form response analysis.
    """

    def __init__(self, schema: Dict[str, List[str]] = None):
        """
        Initialize the NLP engine.

        Args:
            schema: Dictionary mapping table names to column names
        """
        self.schema = schema or self._default_schema()
        self._init_patterns()

    def _default_schema(self) -> Dict[str, List[str]]:
        """Default schema for form response database"""
        return {
            'forms': ['id', 'session_id', 'title', 'description', 'created_at',
                     'updated_at', 'response_count'],
            'form_fields': ['id', 'field_id', 'form_id', 'label', 'field_type',
                           'name', 'required', 'options'],
            'form_responses': ['id', 'form_id', 'submitted_at', 'ip_address'],
            'response_values': ['id', 'response_id', 'field_name', 'value', 'field_type']
        }

    def _init_patterns(self):
        """Initialize regex patterns for query parsing"""

        # Intent patterns
        self.intent_patterns = {
            QueryIntent.COUNT: [
                r'\bhow many\b', r'\bcount\b', r'\btotal\b', r'\bnumber of\b',
                r'\bquantity\b', r'\bamount\b'
            ],
            QueryIntent.LIST: [
                r'\blist\b', r'\bshow\b', r'\bdisplay\b', r'\bget\b', r'\bfind\b',
                r'\bretrieve\b', r'\bwhat are\b', r'\bwhich\b'
            ],
            QueryIntent.AGGREGATE: [
                r'\baverage\b', r'\bmean\b', r'\bsum\b', r'\bmax\b', r'\bmin\b',
                r'\bmaximum\b', r'\bminimum\b', r'\btotal\b'
            ],
            QueryIntent.GROUP: [
                r'\bgroup by\b', r'\bby\s+\w+\b', r'\bper\b', r'\beach\b',
                r'\bbroken down\b', r'\bcategorized\b'
            ],
            QueryIntent.COMPARE: [
                r'\bcompare\b', r'\bvs\b', r'\bversus\b', r'\bdifference\b',
                r'\bbetween\b'
            ],
            QueryIntent.TREND: [
                r'\btrend\b', r'\bover time\b', r'\bhistory\b', r'\bprogression\b',
                r'\bgrowth\b', r'\bchange\b'
            ],
            QueryIntent.DISTRIBUTION: [
                r'\bdistribution\b', r'\bbreakdown\b', r'\bspread\b',
                r'\bpercentage\b', r'\bproportion\b'
            ]
        }

        # Time patterns
        self.time_patterns = {
            'today': ('today', 0),
            'yesterday': ('yesterday', 1),
            'this week': ('week', 7),
            'last week': ('last_week', 14),
            'this month': ('month', 30),
            'last month': ('last_month', 60),
            'this year': ('year', 365),
            'last 7 days': ('days', 7),
            'last 30 days': ('days', 30),
            'last 90 days': ('days', 90)
        }

        # Comparison operators
        self.comparison_patterns = {
            r'greater than|more than|above|over|>': '>',
            r'less than|fewer than|below|under|<': '<',
            r'equal to|equals|=|is': '=',
            r'not equal|not|!=|isn\'t': '!=',
            r'at least|minimum|>=': '>=',
            r'at most|maximum|<=': '<=',
            r'between': 'BETWEEN',
            r'like|contains|includes': 'LIKE',
            r'starts with|beginning with': 'LIKE_START',
            r'ends with|ending with': 'LIKE_END'
        }

        # Aggregation functions
        self.aggregation_patterns = {
            r'\baverage\b|\bmean\b|\bavg\b': 'AVG',
            r'\bsum\b|\btotal\b': 'SUM',
            r'\bmaximum\b|\bmax\b|\bhighest\b|\blargest\b': 'MAX',
            r'\bminimum\b|\bmin\b|\blowest\b|\bsmallest\b': 'MIN',
            r'\bcount\b|\bnumber\b|\bhow many\b': 'COUNT'
        }

        # Field name mappings (natural language to column names)
        self.field_mappings = {
            'form': 'forms',
            'forms': 'forms',
            'response': 'form_responses',
            'responses': 'form_responses',
            'submission': 'form_responses',
            'submissions': 'form_responses',
            'answer': 'response_values',
            'answers': 'response_values',
            'value': 'response_values',
            'values': 'response_values',
            'field': 'form_fields',
            'fields': 'form_fields',
            'question': 'form_fields',
            'questions': 'form_fields'
        }

    def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into structured components.

        Args:
            query: Natural language query string

        Returns:
            ParsedQuery object with structured query components
        """
        query_lower = query.lower().strip()

        # Detect intent
        intent = self._detect_intent(query_lower)

        # Detect target table
        target_table = self._detect_table(query_lower)

        # Parse select fields
        select_fields = self._parse_select_fields(query_lower, target_table)

        # Parse conditions/filters
        conditions = self._parse_conditions(query_lower)

        # Parse grouping
        group_by = self._parse_group_by(query_lower)

        # Parse ordering
        order_by, order_direction = self._parse_order_by(query_lower)

        # Parse limit
        limit = self._parse_limit(query_lower)

        # Parse aggregations
        aggregations = self._parse_aggregations(query_lower)

        # Parse time range
        time_range = self._parse_time_range(query_lower)

        return ParsedQuery(
            intent=intent,
            target_table=target_table,
            select_fields=select_fields,
            conditions=conditions,
            group_by=group_by,
            order_by=order_by,
            order_direction=order_direction,
            limit=limit,
            aggregations=aggregations,
            time_range=time_range
        )

    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the primary intent of the query"""
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, query))
            intent_scores[intent] = score

        # Default to LIST if no clear intent
        max_score = max(intent_scores.values()) if intent_scores else 0
        if max_score == 0:
            return QueryIntent.LIST

        return max(intent_scores, key=intent_scores.get)

    def _detect_table(self, query: str) -> str:
        """Detect the target table from the query"""
        for keyword, table in self.field_mappings.items():
            if keyword in query:
                return table

        # Default to form_responses as most common use case
        return 'form_responses'

    def _parse_select_fields(self, query: str, table: str) -> List[str]:
        """Parse which fields to select"""
        fields = []

        # Check for specific field mentions
        if table in self.schema:
            for field in self.schema[table]:
                if field.replace('_', ' ') in query or field in query:
                    fields.append(field)

        # Check for common field references
        field_keywords = {
            'name': ['name', 'title', 'label'],
            'date': ['date', 'time', 'when', 'submitted'],
            'count': ['count', 'number', 'total'],
            'value': ['value', 'answer', 'response']
        }

        for field_type, keywords in field_keywords.items():
            if any(kw in query for kw in keywords):
                if field_type == 'date' and 'submitted_at' in self.schema.get(table, []):
                    fields.append('submitted_at')
                elif field_type == 'name' and 'title' in self.schema.get(table, []):
                    fields.append('title')

        return fields if fields else ['*']

    def _parse_conditions(self, query: str) -> List[Dict[str, Any]]:
        """Parse filtering conditions from the query"""
        conditions = []

        # Parse comparison conditions
        for pattern, operator in self.comparison_patterns.items():
            match = re.search(f'({pattern})\\s+(\\w+)\\s+([\\w\\d\\.]+)', query)
            if match:
                field = match.group(2)
                value = match.group(3)

                if operator == 'LIKE':
                    value = f'%{value}%'
                elif operator == 'LIKE_START':
                    operator = 'LIKE'
                    value = f'{value}%'
                elif operator == 'LIKE_END':
                    operator = 'LIKE'
                    value = f'%{value}'

                conditions.append({
                    'field': field,
                    'operator': operator,
                    'value': value
                })

        # Parse "where field = value" patterns
        where_match = re.search(r'where\s+(\w+)\s*(=|is)\s*["\']?([^"\']+)["\']?', query)
        if where_match:
            conditions.append({
                'field': where_match.group(1),
                'operator': '=',
                'value': where_match.group(3).strip()
            })

        # Parse "for form X" patterns
        form_match = re.search(r'for\s+(?:form\s+)?["\']?([^"\']+)["\']?(?:\s+form)?', query)
        if form_match:
            form_name = form_match.group(1).strip()
            if form_name and form_name not in ['form', 'the']:
                conditions.append({
                    'field': 'title',
                    'operator': 'LIKE',
                    'value': f'%{form_name}%'
                })

        return conditions

    def _parse_group_by(self, query: str) -> Optional[str]:
        """Parse GROUP BY clause from query"""
        # Explicit "group by" pattern
        match = re.search(r'group(?:ed)?\s+by\s+(\w+)', query)
        if match:
            return match.group(1)

        # "by X" pattern
        match = re.search(r'\bby\s+(\w+)(?:\s|$)', query)
        if match and match.group(1) not in ['the', 'a', 'an']:
            return match.group(1)

        # "per X" pattern
        match = re.search(r'\bper\s+(\w+)', query)
        if match:
            return match.group(1)

        # "each X" pattern
        match = re.search(r'\beach\s+(\w+)', query)
        if match:
            return match.group(1)

        return None

    def _parse_order_by(self, query: str) -> Tuple[Optional[str], str]:
        """Parse ORDER BY clause and direction"""
        direction = 'DESC'  # Default

        # Check for explicit ordering
        if any(word in query for word in ['ascending', 'oldest', 'lowest', 'first', 'asc']):
            direction = 'ASC'
        elif any(word in query for word in ['descending', 'newest', 'highest', 'latest', 'desc']):
            direction = 'DESC'

        # Parse "order by X" pattern
        match = re.search(r'order(?:ed)?\s+by\s+(\w+)', query)
        if match:
            return match.group(1), direction

        # Parse "sort by X" pattern
        match = re.search(r'sort(?:ed)?\s+by\s+(\w+)', query)
        if match:
            return match.group(1), direction

        # Implicit ordering based on keywords
        if any(word in query for word in ['latest', 'recent', 'newest']):
            return 'submitted_at', 'DESC'
        elif any(word in query for word in ['oldest', 'earliest', 'first']):
            return 'submitted_at', 'ASC'

        return None, direction

    def _parse_limit(self, query: str) -> Optional[int]:
        """Parse LIMIT clause from query"""
        # "top N" pattern
        match = re.search(r'\btop\s+(\d+)', query)
        if match:
            return int(match.group(1))

        # "first N" pattern
        match = re.search(r'\bfirst\s+(\d+)', query)
        if match:
            return int(match.group(1))

        # "last N" pattern
        match = re.search(r'\blast\s+(\d+)', query)
        if match:
            return int(match.group(1))

        # "limit N" pattern
        match = re.search(r'\blimit\s+(\d+)', query)
        if match:
            return int(match.group(1))

        # "N responses/forms" pattern
        match = re.search(r'(\d+)\s+(?:responses?|forms?|submissions?|results?)', query)
        if match:
            return int(match.group(1))

        return None

    def _parse_aggregations(self, query: str) -> List[Dict[str, str]]:
        """Parse aggregation functions from query"""
        aggregations = []

        for pattern, func in self.aggregation_patterns.items():
            if re.search(pattern, query):
                # Try to find what field to aggregate
                match = re.search(f'{pattern}\\s+(?:of\\s+)?(?:the\\s+)?(\\w+)', query)
                if match:
                    field = match.group(1)
                else:
                    field = '*' if func == 'COUNT' else 'value'

                aggregations.append({
                    'function': func,
                    'field': field
                })

        return aggregations

    def _parse_time_range(self, query: str) -> Optional[Dict[str, str]]:
        """Parse time range from query"""
        for time_phrase, (period_type, days) in self.time_patterns.items():
            if time_phrase in query:
                end_date = datetime.now()

                if period_type == 'today':
                    start_date = end_date.replace(hour=0, minute=0, second=0)
                elif period_type == 'yesterday':
                    start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0)
                    end_date = start_date.replace(hour=23, minute=59, second=59)
                else:
                    start_date = end_date - timedelta(days=days)

                return {
                    'start': start_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'end': end_date.strftime('%Y-%m-%d %H:%M:%S')
                }

        # Check for specific date patterns
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
        if date_match:
            return {
                'start': f"{date_match.group(1)} 00:00:00",
                'end': f"{date_match.group(1)} 23:59:59"
            }

        return None

    def to_sql(self, query: str) -> str:
        """
        Convert a natural language query to SQL.

        Args:
            query: Natural language query string

        Returns:
            SQL query string
        """
        parsed = self.parse(query)
        return self._build_sql(parsed)

    def _build_sql(self, parsed: ParsedQuery) -> str:
        """Build SQL query from parsed components"""
        parts = []

        # SELECT clause
        select_clause = self._build_select(parsed)
        parts.append(f"SELECT {select_clause}")

        # FROM clause
        from_clause = self._build_from(parsed)
        parts.append(f"FROM {from_clause}")

        # WHERE clause
        where_clause = self._build_where(parsed)
        if where_clause:
            parts.append(f"WHERE {where_clause}")

        # GROUP BY clause
        if parsed.group_by:
            parts.append(f"GROUP BY {parsed.group_by}")

        # ORDER BY clause
        if parsed.order_by:
            parts.append(f"ORDER BY {parsed.order_by} {parsed.order_direction}")

        # LIMIT clause
        if parsed.limit:
            parts.append(f"LIMIT {parsed.limit}")

        return '\n'.join(parts)

    def _build_select(self, parsed: ParsedQuery) -> str:
        """Build SELECT clause"""
        if parsed.aggregations:
            agg_parts = []
            for agg in parsed.aggregations:
                agg_parts.append(f"{agg['function']}({agg['field']})")

            if parsed.group_by:
                agg_parts.insert(0, parsed.group_by)

            return ', '.join(agg_parts)

        return ', '.join(parsed.select_fields)

    def _build_from(self, parsed: ParsedQuery) -> str:
        """Build FROM clause with necessary JOINs"""
        table = parsed.target_table

        # Add JOINs based on what we need
        if table == 'response_values':
            return """response_values rv
            JOIN form_responses fr ON rv.response_id = fr.id
            JOIN forms f ON fr.form_id = f.id"""
        elif table == 'form_responses':
            return """form_responses fr
            JOIN forms f ON fr.form_id = f.id"""
        elif table == 'form_fields':
            return """form_fields ff
            JOIN forms f ON ff.form_id = f.id"""

        return table

    def _build_where(self, parsed: ParsedQuery) -> str:
        """Build WHERE clause"""
        conditions = []

        # Add parsed conditions
        for cond in parsed.conditions:
            if cond['operator'] in ['LIKE', 'NOT LIKE']:
                conditions.append(f"{cond['field']} {cond['operator']} '{cond['value']}'")
            elif cond['operator'] == 'BETWEEN':
                conditions.append(f"{cond['field']} BETWEEN {cond['value']}")
            else:
                # Check if value is numeric
                try:
                    float(cond['value'])
                    conditions.append(f"{cond['field']} {cond['operator']} {cond['value']}")
                except ValueError:
                    conditions.append(f"{cond['field']} {cond['operator']} '{cond['value']}'")

        # Add time range condition
        if parsed.time_range:
            time_field = 'submitted_at' if 'form_responses' in parsed.target_table else 'created_at'
            conditions.append(
                f"{time_field} BETWEEN '{parsed.time_range['start']}' AND '{parsed.time_range['end']}'"
            )

        return ' AND '.join(conditions) if conditions else ''

    def explain(self, query: str) -> Dict[str, Any]:
        """
        Explain how the query will be interpreted.

        Args:
            query: Natural language query

        Returns:
            Dictionary explaining the query interpretation
        """
        parsed = self.parse(query)
        sql = self._build_sql(parsed)

        return {
            'original_query': query,
            'intent': parsed.intent.value,
            'target_table': parsed.target_table,
            'select_fields': parsed.select_fields,
            'conditions': parsed.conditions,
            'group_by': parsed.group_by,
            'order_by': parsed.order_by,
            'order_direction': parsed.order_direction,
            'limit': parsed.limit,
            'aggregations': parsed.aggregations,
            'time_range': parsed.time_range,
            'generated_sql': sql
        }
