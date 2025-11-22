"""
AI Form Generator - Core Logic

This module provides the main form generation logic using agentic AI
to parse natural language input and create dynamic forms.
"""

import json
import re
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class FieldType(Enum):
    """Supported form field types."""
    TEXT = "text"
    EMAIL = "email"
    PASSWORD = "password"
    NUMBER = "number"
    PHONE = "tel"
    URL = "url"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime-local"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    FILE = "file"
    RANGE = "range"
    COLOR = "color"
    HIDDEN = "hidden"


@dataclass
class FormField:
    """Represents a single form field."""
    id: str
    label: str
    field_type: str
    name: str
    required: bool = False
    placeholder: str = ""
    description: str = ""
    options: List[str] = None
    validation: Dict[str, Any] = None
    default_value: str = ""

    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.validation is None:
            self.validation = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class FormConfig:
    """Configuration for a generated form."""
    title: str
    description: str
    fields: List[FormField]
    action: str = "#"
    method: str = "POST"

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
            "action": self.action,
            "method": self.method
        }


class AIFormParser:
    """
    AI-powered parser for extracting form fields from natural language.

    This class uses pattern matching and NLP techniques to identify:
    - Questions (which become form fields)
    - Input types (text, email, select, etc.)
    - Options/selections for dropdowns and radio buttons
    """

    # Patterns for identifying field types
    FIELD_PATTERNS = {
        "email": [
            r'\bemail\b', r'\be-mail\b', r'\bmail\s*address\b'
        ],
        "password": [
            r'\bpassword\b', r'\bpass\s*code\b', r'\bpin\b'
        ],
        "tel": [
            r'\bphone\b', r'\btelephone\b', r'\bmobile\b', r'\bcell\b',
            r'\bcontact\s*number\b'
        ],
        "number": [
            r'\bage\b', r'\bquantity\b', r'\bamount\b', r'\bnumber\s*of\b',
            r'\bhow\s*many\b', r'\bcount\b', r'\byear\b'
        ],
        "date": [
            r'\bdate\b', r'\bbirthday\b', r'\bborn\b', r'\bwhen\b.*\bdate\b',
            r'\bdate\s*of\s*birth\b', r'\bdob\b'
        ],
        "time": [
            r'\btime\b', r'\bhour\b', r'\bschedule\b'
        ],
        "url": [
            r'\bwebsite\b', r'\burl\b', r'\blink\b', r'\bhomepage\b'
        ],
        "textarea": [
            r'\bdescription\b', r'\bcomments?\b', r'\bmessage\b',
            r'\bfeedback\b', r'\bdetails\b', r'\bnotes?\b', r'\bbio\b',
            r'\babout\b', r'\btell\s*us\b', r'\bdescribe\b'
        ],
        "file": [
            r'\bupload\b', r'\bfile\b', r'\battach\b', r'\bdocument\b',
            r'\bresume\b', r'\bphoto\b', r'\bimage\b'
        ],
        "checkbox": [
            r'\bagree\b', r'\baccept\b', r'\bterms\b', r'\bconsent\b',
            r'\bsubscribe\b', r'\bnewsletter\b'
        ]
    }

    # Patterns for identifying select/radio fields
    SELECT_PATTERNS = [
        r'(?:select|choose|pick)\s+(?:your\s+)?(\w+)',
        r'(\w+)\s*:\s*\[([^\]]+)\]',
        r'(\w+)\s+options?\s*[:\-]\s*(.+)',
        r'(?:which|what)\s+(\w+)',
    ]

    def __init__(self):
        self.field_counter = 0

    def parse(self, text: str) -> FormConfig:
        """
        Parse natural language text to extract form configuration.

        Args:
            text: Natural language description of the form

        Returns:
            FormConfig object with extracted fields
        """
        # Extract form title and description
        title, description = self._extract_title_description(text)

        # Extract form fields
        fields = self._extract_fields(text)

        return FormConfig(
            title=title,
            description=description,
            fields=fields
        )

    def _extract_title_description(self, text: str) -> tuple:
        """Extract form title and description from text."""
        lines = text.strip().split('\n')

        # Try to find a title (usually the first line or line after "form:")
        title = "Generated Form"
        description = ""

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check for explicit title markers
            title_match = re.match(r'^(?:title|form|name)\s*[:=]\s*(.+)$', line, re.I)
            if title_match:
                title = title_match.group(1).strip()
                continue

            # Check for description markers
            desc_match = re.match(r'^(?:description|desc|about)\s*[:=]\s*(.+)$', line, re.I)
            if desc_match:
                description = desc_match.group(1).strip()
                continue

            # First substantial line becomes title if not set
            if title == "Generated Form" and len(line) > 3 and not self._is_field_line(line):
                title = line

        return title, description

    def _is_field_line(self, line: str) -> bool:
        """Check if a line describes a form field."""
        field_indicators = [
            r'^\d+[\.\)]\s',  # Numbered list
            r'^\-\s',  # Bullet point
            r'^\*\s',  # Asterisk bullet
            r'\?$',  # Question mark
            r':\s*\[',  # Has options in brackets
        ]
        return any(re.search(p, line) for p in field_indicators)

    def _extract_fields(self, text: str) -> List[FormField]:
        """Extract form fields from text."""
        fields = []

        # Split text into potential field descriptions
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to extract a field from this line
            field = self._parse_field_line(line)
            if field:
                fields.append(field)

        # If no fields found, try to extract from the entire text
        if not fields:
            fields = self._extract_fields_from_prose(text)

        return fields

    def _parse_field_line(self, line: str) -> Optional[FormField]:
        """Parse a single line to extract a form field."""
        # Skip title/description markers
        if re.match(r'^(?:title|form|name|description|desc|about)\s*[:=]', line, re.I):
            return None

        # Remove list markers
        line = re.sub(r'^[\d\.\)\-\*]+\s*', '', line)

        if len(line) < 3:
            return None

        # Check for field with options: "Field: [option1, option2, option3]"
        options_match = re.search(r'^(.+?)\s*:\s*\[([^\]]+)\]', line)
        if options_match:
            label = options_match.group(1).strip()
            options_str = options_match.group(2)
            options = [o.strip() for o in options_str.split(',')]

            return self._create_field(
                label=label,
                field_type="select" if len(options) > 3 else "radio",
                options=options
            )

        # Check for field with inline options: "Gender (Male/Female/Other)"
        inline_options = re.search(r'^(.+?)\s*\(([^)]+/[^)]+)\)', line)
        if inline_options:
            label = inline_options.group(1).strip()
            options_str = inline_options.group(2)
            options = [o.strip() for o in options_str.split('/')]

            return self._create_field(
                label=label,
                field_type="radio" if len(options) <= 4 else "select",
                options=options
            )

        # Check for required indicator
        required = '*' in line or 'required' in line.lower()
        line = re.sub(r'\*|required', '', line, flags=re.I).strip()

        # Remove question mark for label
        label = re.sub(r'\?$', '', line).strip()

        # Determine field type based on content
        field_type = self._infer_field_type(line)

        # Create the field
        return self._create_field(
            label=label,
            field_type=field_type,
            required=required
        )

    def _extract_fields_from_prose(self, text: str) -> List[FormField]:
        """Extract fields from prose/paragraph text."""
        fields = []

        # Common patterns for fields in prose
        patterns = [
            # "ask for their name"
            r"(?:ask\s+(?:for\s+)?(?:their\s+)?|collect\s+|get\s+|need\s+)([a-z\s]+?)(?:\s+and\s+|\s*,\s*|$)",
            # "name, email, and phone"
            r"(?:^|,\s*|\s+and\s+)([a-z]+)(?=\s*,|\s+and\s+|$)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                label = match.strip()
                if len(label) > 2 and label not in ['and', 'the', 'for']:
                    field_type = self._infer_field_type(label)
                    field = self._create_field(label=label.title(), field_type=field_type)
                    fields.append(field)

        return fields

    def _infer_field_type(self, text: str) -> str:
        """Infer the field type based on the text content."""
        text_lower = text.lower()

        for field_type, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return field_type

        # Default to text
        return "text"

    def _create_field(self, label: str, field_type: str,
                      required: bool = False, options: List[str] = None) -> FormField:
        """Create a FormField object."""
        self.field_counter += 1

        # Generate field ID and name
        field_id = f"field_{self.field_counter}"
        field_name = re.sub(r'[^a-z0-9]+', '_', label.lower()).strip('_')

        # Generate placeholder
        placeholder = self._generate_placeholder(label, field_type)

        return FormField(
            id=field_id,
            label=label,
            field_type=field_type,
            name=field_name,
            required=required,
            placeholder=placeholder,
            options=options or []
        )

    def _generate_placeholder(self, label: str, field_type: str) -> str:
        """Generate appropriate placeholder text."""
        placeholders = {
            "email": "your.email@example.com",
            "tel": "(123) 456-7890",
            "url": "https://example.com",
            "password": "Enter your password",
            "date": "Select a date",
            "time": "Select a time",
        }

        if field_type in placeholders:
            return placeholders[field_type]

        return f"Enter {label.lower()}"


class FormGenerator:
    """
    Generates HTML forms from FormConfig objects.
    """

    def __init__(self, template_path: str = None):
        self.template_path = template_path or "templates/form-template.html"

    def generate(self, config: FormConfig) -> str:
        """
        Generate HTML form from configuration.

        Args:
            config: FormConfig object

        Returns:
            Generated HTML string
        """
        # Load template
        template = self._load_template()

        # Generate field HTML
        fields_html = self._generate_fields_html(config.fields)

        # Replace placeholders
        html = template.replace("{{form_title}}", config.title)
        html = html.replace("{{form_description}}", config.description)
        html = html.replace("{{form_action}}", config.action)
        html = html.replace("{{form_method}}", config.method)
        html = html.replace("{{form_fields}}", fields_html)

        return html

    def _load_template(self) -> str:
        """Load the HTML template."""
        try:
            with open(self.template_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            # Return a basic template if file not found
            return self._get_default_template()

    def _get_default_template(self) -> str:
        """Get default HTML template."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{form_title}}</title>
    <link rel="stylesheet" href="static/css/form-styles.css">
</head>
<body>
    <div class="form-container">
        <header class="form-header">
            <h1>{{form_title}}</h1>
            <p class="form-description">{{form_description}}</p>
        </header>
        <form id="generated-form" class="dynamic-form" action="{{form_action}}" method="{{form_method}}">
            {{form_fields}}
            <div class="form-actions">
                <button type="submit" class="btn btn-primary">Submit</button>
                <button type="reset" class="btn btn-secondary">Reset</button>
            </div>
        </form>
    </div>
</body>
</html>'''

    def _generate_fields_html(self, fields: List[FormField]) -> str:
        """Generate HTML for all form fields."""
        html_parts = []

        for field in fields:
            html_parts.append(self._generate_field_html(field))

        return '\n\n'.join(html_parts)

    def _generate_field_html(self, field: FormField) -> str:
        """Generate HTML for a single form field."""
        required_attr = 'required' if field.required else ''
        required_indicator = '<span class="required-indicator">*</span>' if field.required else ''

        # Generate based on field type
        if field.field_type == "textarea":
            input_html = f'''<textarea
                id="{field.id}"
                name="{field.name}"
                class="form-control"
                placeholder="{field.placeholder}"
                {required_attr}>{field.default_value}</textarea>'''

        elif field.field_type == "select":
            options_html = '<option value="">Select an option</option>\n'
            for option in field.options:
                options_html += f'<option value="{option}">{option}</option>\n'

            input_html = f'''<select
                id="{field.id}"
                name="{field.name}"
                class="form-control"
                {required_attr}>
                {options_html}
            </select>'''

        elif field.field_type == "radio":
            options_html = ''
            for i, option in enumerate(field.options):
                option_id = f"{field.id}_{i}"
                options_html += f'''<div class="radio-item">
                    <input type="radio" id="{option_id}" name="{field.name}" value="{option}" {required_attr if i == 0 else ''}>
                    <label for="{option_id}">{option}</label>
                </div>\n'''

            input_html = f'<div class="radio-group">\n{options_html}</div>'

        elif field.field_type == "checkbox":
            if field.options:
                # Multiple checkboxes
                options_html = ''
                for i, option in enumerate(field.options):
                    option_id = f"{field.id}_{i}"
                    options_html += f'''<div class="checkbox-item">
                        <input type="checkbox" id="{option_id}" name="{field.name}" value="{option}">
                        <label for="{option_id}">{option}</label>
                    </div>\n'''
                input_html = f'<div class="checkbox-group">\n{options_html}</div>'
            else:
                # Single checkbox
                input_html = f'''<div class="checkbox-item">
                    <input type="checkbox" id="{field.id}" name="{field.name}" {required_attr}>
                    <label for="{field.id}">{field.label}</label>
                </div>'''

        else:
            # Standard input types
            input_html = f'''<input
                type="{field.field_type}"
                id="{field.id}"
                name="{field.name}"
                class="form-control"
                placeholder="{field.placeholder}"
                value="{field.default_value}"
                {required_attr}>'''

        # Wrap in form group
        description_html = f'<p class="field-description">{field.description}</p>' if field.description else ''

        # For checkbox without options, label is inside
        if field.field_type == "checkbox" and not field.options:
            return f'''<div class="form-group" data-field-id="{field.id}">
            {input_html}
            {description_html}
        </div>'''

        return f'''<div class="form-group" data-field-id="{field.id}">
            <label for="{field.id}">{field.label}{required_indicator}</label>
            {input_html}
            {description_html}
        </div>'''


class FormEditorConfig:
    """Configuration and utilities for the form editor."""

    @staticmethod
    def get_field_types() -> List[Dict[str, str]]:
        """Get all available field types."""
        return [
            {"value": "text", "label": "Text"},
            {"value": "email", "label": "Email"},
            {"value": "password", "label": "Password"},
            {"value": "number", "label": "Number"},
            {"value": "tel", "label": "Phone"},
            {"value": "url", "label": "URL"},
            {"value": "date", "label": "Date"},
            {"value": "time", "label": "Time"},
            {"value": "datetime-local", "label": "Date & Time"},
            {"value": "textarea", "label": "Text Area"},
            {"value": "select", "label": "Dropdown"},
            {"value": "radio", "label": "Radio Buttons"},
            {"value": "checkbox", "label": "Checkbox"},
            {"value": "file", "label": "File Upload"},
            {"value": "range", "label": "Range Slider"},
            {"value": "color", "label": "Color Picker"},
        ]


def create_form_from_text(text: str, output_path: str = None) -> str:
    """
    Main function to create a form from natural language text.

    Args:
        text: Natural language description of the form
        output_path: Optional path to save the generated HTML

    Returns:
        Generated HTML string
    """
    # Parse the input
    parser = AIFormParser()
    config = parser.parse(text)

    # Generate the form
    generator = FormGenerator()
    html = generator.generate(config)

    # Save to file if path provided
    if output_path:
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html)

    return html


# Example usage and testing
if __name__ == "__main__":
    # Example natural language input
    example_input = """
    Contact Form

    A form to collect contact information from users.

    1. Full Name *
    2. Email Address *
    3. Phone Number
    4. Subject: [General Inquiry, Support, Feedback, Other]
    5. Message *
    6. Preferred Contact Method (Email/Phone/Either)
    7. Subscribe to newsletter
    """

    # Create form
    html = create_form_from_text(
        example_input,
        output_path="generated_forms/contact_form.html"
    )

    print("Form generated successfully!")
    print(f"Output saved to: generated_forms/contact_form.html")
