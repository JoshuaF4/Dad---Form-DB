# AI Form Generator

An agentic AI-powered tool that creates HTML forms from natural language descriptions. It parses your input to identify questions, input types, and selection options, then generates a customizable form.

## Features

- **Natural Language Input**: Describe your form in plain English
- **AI-Powered Parsing**: Automatically detects field types (email, phone, date, etc.)
- **Live Preview**: See your form update in real-time
- **Dynamic Editor**: Add, edit, delete, and reorder fields
- **Drag & Drop**: Easily rearrange form fields
- **Export Options**: Save as HTML or JSON
- **Responsive Design**: Forms work on all devices

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd Dad---Form-DB

# Switch to the Form-dev branch
git checkout Form-dev

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Running the Web Application

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

### Using the CLI

```python
from form_generator import create_form_from_text

text = """
Contact Form

1. Full Name *
2. Email Address *
3. Phone Number
4. Subject: [General Inquiry, Support, Feedback, Other]
5. Message *
"""

html = create_form_from_text(text, output_path="my_form.html")
```

## Natural Language Syntax

### Basic Fields
```
Full Name *          # Text field, required
Email Address        # Auto-detected as email type
Phone Number         # Auto-detected as phone type
```

### Dropdowns
```
Country: [USA, Canada, UK, Other]
```

### Radio Buttons
```
Gender (Male/Female/Other)
```

### Common Patterns
- `*` or `required` = Required field
- `[option1, option2]` = Dropdown select
- `(option1/option2)` = Radio buttons
- Words like "email", "phone", "date", "message" = Auto-detected types

## Project Structure

```
├── app.py                    # Flask web application
├── form_generator.py         # Core AI parsing and generation logic
├── requirements.txt          # Python dependencies
├── templates/
│   ├── index.html           # Main editor interface
│   └── form-template.html   # Base form template
├── static/
│   ├── css/
│   │   └── form-styles.css  # Form styling
│   └── js/
│       └── form-validation.js # Client-side validation
└── generated_forms/          # Saved forms output directory
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Generate form from text |
| GET | `/api/form/{id}` | Get form configuration |
| POST | `/api/form/{id}/update` | Update form config |
| POST | `/api/form/{id}/field` | Add new field |
| PUT | `/api/form/{id}/field/{fid}` | Update field |
| DELETE | `/api/form/{id}/field/{fid}` | Delete field |
| POST | `/api/form/{id}/reorder` | Reorder fields |
| GET | `/api/form/{id}/export/html` | Export as HTML |
| GET | `/api/form/{id}/export/json` | Export as JSON |
| POST | `/api/form/{id}/save` | Save to filesystem |

## Customization

### Styling
Edit `static/css/form-styles.css` to customize the form appearance.

### Templates
Modify `templates/form-template.html` to change the base form structure.

### Field Types
Add new field type detection patterns in `form_generator.py` under `AIFormParser.FIELD_PATTERNS`.

## License

MIT License
