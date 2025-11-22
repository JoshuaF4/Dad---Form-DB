"""
Chart Generator for Form Response Analytics
Generates chart configurations for various visualization types
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import colorsys


class ChartType(str, Enum):
    """Supported chart types"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    POLAR = "polarArea"
    HORIZONTAL_BAR = "horizontalBar"


class ChartGenerator:
    """
    Generates chart configurations for Chart.js visualization.
    """

    def __init__(self):
        self.default_colors = self._generate_color_palette(20)

    def _generate_color_palette(self, n: int) -> List[str]:
        """Generate a palette of n distinct colors"""
        colors = []
        for i in range(n):
            hue = i / n
            # Use golden ratio for better color distribution
            hue = (hue + 0.618033988749895) % 1
            rgb = colorsys.hsv_to_rgb(hue, 0.7, 0.9)
            color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb[0] * 255),
                int(rgb[1] * 255),
                int(rgb[2] * 255)
            )
            colors.append(color)
        return colors

    def generate(self, data: Dict[str, Any], chart_type: str = "bar",
                 title: str = "", options: Dict = None) -> Dict[str, Any]:
        """
        Generate a chart configuration.

        Args:
            data: Query result data with 'columns' and 'rows'
            chart_type: Type of chart to generate
            title: Chart title
            options: Additional chart options

        Returns:
            Chart.js compatible configuration
        """
        rows = data.get('rows', [])
        columns = data.get('columns', [])

        if not rows or not columns:
            return self._empty_chart_config(title)

        # Determine chart type
        chart_type = ChartType(chart_type) if chart_type in [ct.value for ct in ChartType] else ChartType.BAR

        # Generate appropriate configuration
        if chart_type in [ChartType.PIE, ChartType.DOUGHNUT, ChartType.POLAR]:
            return self._generate_pie_config(rows, columns, chart_type, title, options)
        elif chart_type == ChartType.LINE:
            return self._generate_line_config(rows, columns, title, options)
        elif chart_type == ChartType.SCATTER:
            return self._generate_scatter_config(rows, columns, title, options)
        elif chart_type == ChartType.RADAR:
            return self._generate_radar_config(rows, columns, title, options)
        elif chart_type == ChartType.AREA:
            return self._generate_area_config(rows, columns, title, options)
        else:
            return self._generate_bar_config(rows, columns, title, options)

    def _empty_chart_config(self, title: str) -> Dict[str, Any]:
        """Generate config for empty data"""
        return {
            'type': 'bar',
            'data': {
                'labels': ['No Data'],
                'datasets': [{
                    'label': 'No Data',
                    'data': [0],
                    'backgroundColor': '#cccccc'
                }]
            },
            'options': {
                'responsive': True,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': title or 'No Data Available'
                    }
                }
            }
        }

    def _generate_bar_config(self, rows: List[Dict], columns: List[str],
                             title: str, options: Dict) -> Dict[str, Any]:
        """Generate bar chart configuration"""
        labels = []
        datasets = []

        # First column is usually the label
        label_col = columns[0]
        value_cols = columns[1:] if len(columns) > 1 else columns

        for row in rows:
            labels.append(str(row.get(label_col, '')))

        # Create dataset for each value column
        for i, col in enumerate(value_cols):
            data = []
            for row in rows:
                value = row.get(col, 0)
                try:
                    data.append(float(value) if value else 0)
                except (ValueError, TypeError):
                    data.append(0)

            datasets.append({
                'label': col,
                'data': data,
                'backgroundColor': self.default_colors[i % len(self.default_colors)],
                'borderColor': self.default_colors[i % len(self.default_colors)],
                'borderWidth': 1
            })

        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'options': self._merge_options({
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': bool(title),
                        'text': title
                    },
                    'legend': {
                        'display': len(datasets) > 1
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }, options)
        }

    def _generate_line_config(self, rows: List[Dict], columns: List[str],
                              title: str, options: Dict) -> Dict[str, Any]:
        """Generate line chart configuration"""
        labels = []
        datasets = []

        label_col = columns[0]
        value_cols = columns[1:] if len(columns) > 1 else columns

        for row in rows:
            labels.append(str(row.get(label_col, '')))

        for i, col in enumerate(value_cols):
            data = []
            for row in rows:
                value = row.get(col, 0)
                try:
                    data.append(float(value) if value else 0)
                except (ValueError, TypeError):
                    data.append(0)

            datasets.append({
                'label': col,
                'data': data,
                'borderColor': self.default_colors[i % len(self.default_colors)],
                'backgroundColor': self.default_colors[i % len(self.default_colors)] + '33',
                'fill': False,
                'tension': 0.1
            })

        return {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'options': self._merge_options({
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': bool(title),
                        'text': title
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }, options)
        }

    def _generate_pie_config(self, rows: List[Dict], columns: List[str],
                             chart_type: ChartType, title: str, options: Dict) -> Dict[str, Any]:
        """Generate pie/doughnut chart configuration"""
        labels = []
        data = []

        label_col = columns[0]
        value_col = columns[1] if len(columns) > 1 else columns[0]

        for row in rows:
            labels.append(str(row.get(label_col, '')))
            value = row.get(value_col, 0)
            try:
                data.append(float(value) if value else 0)
            except (ValueError, TypeError):
                data.append(0)

        return {
            'type': chart_type.value,
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': self.default_colors[:len(data)],
                    'borderWidth': 2,
                    'borderColor': '#ffffff'
                }]
            },
            'options': self._merge_options({
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': bool(title),
                        'text': title
                    },
                    'legend': {
                        'position': 'right'
                    }
                }
            }, options)
        }

    def _generate_area_config(self, rows: List[Dict], columns: List[str],
                              title: str, options: Dict) -> Dict[str, Any]:
        """Generate area chart configuration"""
        config = self._generate_line_config(rows, columns, title, options)

        # Modify for area chart
        for dataset in config['data']['datasets']:
            dataset['fill'] = True

        return config

    def _generate_scatter_config(self, rows: List[Dict], columns: List[str],
                                 title: str, options: Dict) -> Dict[str, Any]:
        """Generate scatter plot configuration"""
        data = []

        x_col = columns[0]
        y_col = columns[1] if len(columns) > 1 else columns[0]

        for row in rows:
            try:
                x = float(row.get(x_col, 0)) if row.get(x_col) else 0
                y = float(row.get(y_col, 0)) if row.get(y_col) else 0
                data.append({'x': x, 'y': y})
            except (ValueError, TypeError):
                continue

        return {
            'type': 'scatter',
            'data': {
                'datasets': [{
                    'label': f'{x_col} vs {y_col}',
                    'data': data,
                    'backgroundColor': self.default_colors[0]
                }]
            },
            'options': self._merge_options({
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': bool(title),
                        'text': title
                    }
                },
                'scales': {
                    'x': {
                        'title': {
                            'display': True,
                            'text': x_col
                        }
                    },
                    'y': {
                        'title': {
                            'display': True,
                            'text': y_col
                        }
                    }
                }
            }, options)
        }

    def _generate_radar_config(self, rows: List[Dict], columns: List[str],
                               title: str, options: Dict) -> Dict[str, Any]:
        """Generate radar chart configuration"""
        labels = []
        datasets = []

        label_col = columns[0]
        value_cols = columns[1:] if len(columns) > 1 else columns

        for row in rows:
            labels.append(str(row.get(label_col, '')))

        for i, col in enumerate(value_cols):
            data = []
            for row in rows:
                value = row.get(col, 0)
                try:
                    data.append(float(value) if value else 0)
                except (ValueError, TypeError):
                    data.append(0)

            datasets.append({
                'label': col,
                'data': data,
                'borderColor': self.default_colors[i % len(self.default_colors)],
                'backgroundColor': self.default_colors[i % len(self.default_colors)] + '33',
                'fill': True
            })

        return {
            'type': 'radar',
            'data': {
                'labels': labels,
                'datasets': datasets
            },
            'options': self._merge_options({
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': bool(title),
                        'text': title
                    }
                },
                'scales': {
                    'r': {
                        'beginAtZero': True
                    }
                }
            }, options)
        }

    def _merge_options(self, default: Dict, custom: Dict) -> Dict:
        """Merge custom options with defaults"""
        if not custom:
            return default

        result = default.copy()
        for key, value in custom.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_options(result[key], value)
            else:
                result[key] = value

        return result

    def generate_from_distribution(self, distribution: List[Dict],
                                   chart_type: str = "pie",
                                   title: str = "") -> Dict[str, Any]:
        """
        Generate chart from distribution data.

        Args:
            distribution: List of {'value': x, 'count': n} dicts
            chart_type: Type of chart
            title: Chart title

        Returns:
            Chart configuration
        """
        rows = [{'label': d['value'], 'count': d['count']} for d in distribution]
        columns = ['label', 'count']

        return self.generate(
            {'rows': rows, 'columns': columns},
            chart_type,
            title
        )

    def generate_time_series(self, data: List[Dict], date_field: str,
                            value_field: str, title: str = "") -> Dict[str, Any]:
        """
        Generate time series chart.

        Args:
            data: List of data points
            date_field: Name of date field
            value_field: Name of value field
            title: Chart title

        Returns:
            Line chart configuration for time series
        """
        # Sort by date
        sorted_data = sorted(data, key=lambda x: x.get(date_field, ''))

        rows = [{date_field: d.get(date_field), value_field: d.get(value_field)}
                for d in sorted_data]
        columns = [date_field, value_field]

        return self.generate(
            {'rows': rows, 'columns': columns},
            'line',
            title
        )

    def auto_select_chart_type(self, data: Dict[str, Any],
                               intent: str = None) -> str:
        """
        Automatically select the best chart type for the data.

        Args:
            data: Query result data
            intent: Query intent (if known)

        Returns:
            Recommended chart type
        """
        rows = data.get('rows', [])
        columns = data.get('columns', [])

        if not rows:
            return 'bar'

        num_rows = len(rows)
        num_cols = len(columns)

        # Check if it's categorical data
        is_categorical = num_rows <= 10 and num_cols == 2

        # Check if it's time series
        is_time_series = any('date' in col.lower() or 'time' in col.lower()
                            for col in columns)

        # Based on intent
        if intent == 'distribution':
            return 'pie' if is_categorical else 'bar'
        elif intent == 'trend':
            return 'line'
        elif intent == 'compare':
            return 'bar'

        # Based on data characteristics
        if is_time_series:
            return 'line'
        elif is_categorical:
            return 'pie' if num_rows <= 6 else 'bar'
        elif num_cols >= 3:
            return 'radar' if num_rows <= 8 else 'bar'

        return 'bar'
