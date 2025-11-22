# Form Analytics System

An AI-powered form generation and response analytics platform with natural language querying (NLP-to-SQL), dynamic visualizations, and cloud database support.

## Features

### Form Generator
- **Natural Language Input**: Describe your form in plain English
- **AI-Powered Parsing**: Automatically detects field types (email, phone, date, etc.)
- **Live Preview**: See your form update in real-time
- **Dynamic Editor**: Add, edit, delete, and reorder fields
- **Drag & Drop**: Easily rearrange form fields
- **Export Options**: Save as HTML or JSON

### Analytics Dashboard
- **NLP-to-SQL Query Engine**: Ask questions in plain English, get SQL queries and results
- **Dynamic/Static Database Sync**: Real-time data collection with stable production sync
- **Chart Generation**: Multiple visualization types (bar, line, pie, scatter, etc.)
- **Mobile PWA**: Progressive Web App with offline support and voice input
- **Cloud Database Support**: PostgreSQL, MySQL, SQLite, and more

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/JoshuaF4/Dad---Form-DB.git
cd Dad---Form-DB

# Install dependencies
pip install -r requirements.txt

# For cloud database support (optional)
pip install psycopg2-binary  # PostgreSQL
pip install pymysql          # MySQL
```

### Running the Applications

#### Form Generator (Port 5000)
```bash
python app.py
```
Access at: http://localhost:5000

#### Analytics Dashboard (Port 5001)
```bash
python analytics_app.py
```
Access at:
- Dashboard: http://localhost:5001
- Mobile App: http://localhost:5001/app

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Form Generator │───▶│ Dynamic Database │───▶│ Static Database │
│   (app.py)      │    │   (Staging)      │    │  (Production)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────────────────────────┐
                       │     Analytics Dashboard             │
                       │     (analytics_app.py)              │
                       │  • NLP-to-SQL Queries               │
                       │  • Chart Generation                 │
                       │  • Mobile PWA                       │
                       └─────────────────────────────────────┘
```

## Cloud Database Configuration

### Local Development (SQLite - Default)

No configuration needed. SQLite databases are created automatically in the `data/` directory.

### Cloud Database Connection Points

Configure via environment variables in `database/config.py`:

#### PostgreSQL (AWS RDS, Azure, Heroku, Supabase, Neon)

```bash
# Option 1: Individual settings
export DYNAMIC_DB_TYPE='postgresql'
export DYNAMIC_DB_HOST='your-host.region.rds.amazonaws.com'
export DYNAMIC_DB_PORT='5432'
export DYNAMIC_DB_NAME='dynamic_forms'
export DYNAMIC_DB_USER='admin'
export DYNAMIC_DB_PASSWORD='your-password'
export DYNAMIC_DB_SSL='true'

# Same for STATIC_DB_* variables for static database

# Option 2: Direct URL (takes precedence)
export DYNAMIC_DATABASE_URL='postgresql://user:password@host:5432/dbname?sslmode=require'
export STATIC_DATABASE_URL='postgresql://user:password@host:5432/dbname?sslmode=require'
```

#### MySQL (AWS RDS, PlanetScale)

```bash
export DYNAMIC_DB_TYPE='mysql'
export DYNAMIC_DB_HOST='your-host.mysql.database.azure.com'
export DYNAMIC_DB_PORT='3306'
export DYNAMIC_DB_NAME='dynamic_forms'
export DYNAMIC_DB_USER='admin'
export DYNAMIC_DB_PASSWORD='your-password'
export DYNAMIC_DB_SSL='true'
```

#### Cloud Provider Examples

| Provider | Type | Example Configuration |
|----------|------|----------------------|
| **AWS RDS** | PostgreSQL | `postgresql://user:pass@instance.region.rds.amazonaws.com:5432/db` |
| **Heroku** | PostgreSQL | Use `DATABASE_URL` from Heroku config |
| **Supabase** | PostgreSQL | `postgresql://postgres:pass@db.project.supabase.co:5432/postgres` |
| **Neon** | PostgreSQL | `postgresql://user:pass@ep-name.region.aws.neon.tech/neondb?sslmode=require` |
| **PlanetScale** | MySQL | `mysql://user:pass@host/db?ssl={"rejectUnauthorized":true}` |
| **Azure** | PostgreSQL | `postgresql://user@server:pass@server.postgres.database.azure.com:5432/db` |
| **Google Cloud SQL** | PostgreSQL | Via Unix socket: `postgresql://user:pass@/db?host=/cloudsql/project:region:instance` |
| **CockroachDB** | PostgreSQL | `cockroachdb://user:pass@host:26257/db?sslmode=verify-full` |

**View all cloud connection examples:**
```bash
python -m database.config
```

### Connection Configuration File

The database connection logic is in `database/config.py`. Key functions:

```python
from database import get_dynamic_db_url, get_static_db_url

# Get configured database URLs
dynamic_url = get_dynamic_db_url()  # Returns connection string
static_url = get_static_db_url()    # Returns connection string

# View all cloud examples
from database import print_cloud_examples
print_cloud_examples()
```

## Form Generator Usage

### Natural Language Syntax

```
Contact Form

1. Full Name *          # Text field, required
2. Email Address *      # Auto-detected as email type
3. Phone Number         # Auto-detected as phone type
4. Country: [USA, Canada, UK, Other]  # Dropdown
5. Gender (Male/Female/Other)         # Radio buttons
6. Message *            # Auto-detected as textarea
```

### Patterns
- `*` or `required` = Required field
- `[option1, option2]` = Dropdown select
- `(option1/option2)` = Radio buttons
- Words like "email", "phone", "date", "message" = Auto-detected types

## Analytics API Reference

### Natural Language Query

```bash
POST /api/query
Content-Type: application/json

{
  "query": "How many responses did we get this week?"
}
```

**Response:**
```json
{
  "success": true,
  "natural_query": "How many responses did we get this week?",
  "sql_query": "SELECT COUNT(*) FROM form_responses WHERE submitted_at BETWEEN...",
  "results": {
    "columns": ["COUNT(*)"],
    "rows": [{"COUNT(*)": 42}],
    "row_count": 1
  },
  "execution_time_ms": 15.3
}
```

### Example NLP Queries

| Natural Language | Intent |
|------------------|--------|
| "How many responses do we have?" | Count |
| "Show me the latest 10 responses" | List with limit |
| "What's the average response count per form?" | Aggregate |
| "Count responses grouped by form" | Group by |
| "Show distribution of field 'satisfaction'" | Distribution |
| "Responses for the past 7 days" | Time filter |

### Chart Generation

```bash
POST /api/chart
Content-Type: application/json

{
  "data": {
    "columns": ["category", "count"],
    "rows": [
      {"category": "A", "count": 10},
      {"category": "B", "count": 25}
    ]
  },
  "chart_type": "pie",
  "title": "Response Distribution"
}
```

### Form Submission

```bash
POST /api/submit/{session_id}
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "feedback": "Great service!"
}
```

### Database Sync

```bash
# Check sync status
GET /api/sync/status

# Run sync (dynamic → static)
POST /api/sync/run

# Force sync specific form
POST /api/sync/force/{session_id}
```

## Project Structure

```
Dad---Form-DB/
├── app.py                    # Form generator Flask app
├── analytics_app.py          # Analytics dashboard Flask app
├── form_generator.py         # AI form parsing logic
├── requirements.txt          # Python dependencies
│
├── database/
│   ├── __init__.py          # Package exports
│   ├── config.py            # Cloud DB configuration ⭐
│   ├── models.py            # SQLAlchemy models
│   └── sync.py              # Dynamic→Static sync
│
├── analytics/
│   ├── __init__.py          # Package exports
│   ├── nlp_engine.py        # NLP-to-SQL converter
│   ├── query_executor.py    # Query execution
│   └── chart_generator.py   # Chart.js configs
│
├── templates/
│   ├── index.html           # Form generator UI
│   ├── form-template.html   # Generated form template
│   └── analytics/
│       ├── dashboard.html   # Analytics dashboard
│       └── app.html         # Mobile PWA
│
├── static/
│   ├── css/form-styles.css  # Form styling
│   ├── js/form-validation.js # Client validation
│   ├── sw.js                # Service worker
│   └── icons/               # PWA icons
│
├── data/                    # SQLite databases (auto-created)
└── generated_forms/         # Exported forms
```

## Database Models

### Dynamic Database (Staging)
Receives real-time form submissions:
- **DynamicForm**: Form definitions
- **DynamicFormField**: Field configurations
- **DynamicFormResponse**: User submissions
- **DynamicResponseValue**: Individual field values

### Static Database (Production)
Stable, synced data for analytics:
- **StaticForm**: Synced form definitions
- **StaticFormField**: Synced field configs
- **StaticFormResponse**: Synced submissions
- **StaticResponseValue**: Synced values
- **QueryHistory**: NLP query log

### Sync Process
Forms automatically sync from dynamic to static when:
1. Response count reaches threshold (default: 5)
2. No updates for time threshold (default: 5 minutes)

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | auto-generated |
| `DYNAMIC_DB_TYPE` | Database type (sqlite/postgresql/mysql) | sqlite |
| `DYNAMIC_DB_HOST` | Database host | localhost |
| `DYNAMIC_DB_PORT` | Database port | 5432 |
| `DYNAMIC_DB_NAME` | Database name | dynamic_forms |
| `DYNAMIC_DB_USER` | Database user | (empty) |
| `DYNAMIC_DB_PASSWORD` | Database password | (empty) |
| `DYNAMIC_DB_SSL` | Use SSL connection | false |
| `DYNAMIC_DATABASE_URL` | Full connection URL (overrides above) | (empty) |
| `STATIC_*` | Same variables for static database | (same defaults) |

## Deployment

### Docker

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5001
CMD ["python", "analytics_app.py"]
```

### Heroku

```bash
# Procfile
web: python analytics_app.py

# Set environment variables
heroku config:set DYNAMIC_DATABASE_URL=$DATABASE_URL
heroku config:set STATIC_DATABASE_URL=$DATABASE_URL
```

## Troubleshooting

### Database Connection Issues

```bash
# Test connection
python -c "from database import init_databases; init_databases(); print('Connected!')"

# View configured URLs
python -c "from database import get_dynamic_db_url; print(get_dynamic_db_url())"
```

### SSL Certificate Errors
For cloud databases, ensure SSL is properly configured:
```bash
export DYNAMIC_DB_SSL='true'
```

## API Endpoints Summary

### Form Generator API
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Generate form from text |
| GET | `/api/form/{id}` | Get form configuration |
| POST | `/api/form/{id}/update` | Update form config |
| POST | `/api/form/{id}/field` | Add new field |
| PUT | `/api/form/{id}/field/{fid}` | Update field |
| DELETE | `/api/form/{id}/field/{fid}` | Delete field |
| GET | `/api/form/{id}/export/html` | Export as HTML |
| GET | `/api/form/{id}/export/json` | Export as JSON |

### Analytics API
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/query` | Execute NLP query |
| POST | `/api/query/raw` | Execute raw SQL |
| GET | `/api/forms` | List all forms |
| GET | `/api/forms/{id}/responses` | Get form responses |
| POST | `/api/chart` | Generate chart config |
| POST | `/api/submit/{id}` | Submit form response |
| GET | `/api/sync/status` | Check sync status |
| POST | `/api/sync/run` | Run database sync |

## License

MIT License
