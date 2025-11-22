"""
Database Configuration for Cloud and Local Databases
Supports PostgreSQL, MySQL, SQLite, and other SQLAlchemy-compatible databases
"""

import os
from urllib.parse import quote_plus

# ============ ENVIRONMENT VARIABLES ============
# Set these environment variables for cloud database connections

# Dynamic Database (Staging/Real-time)
DYNAMIC_DB_TYPE = os.environ.get('DYNAMIC_DB_TYPE', 'sqlite')  # sqlite, postgresql, mysql
DYNAMIC_DB_HOST = os.environ.get('DYNAMIC_DB_HOST', 'localhost')
DYNAMIC_DB_PORT = os.environ.get('DYNAMIC_DB_PORT', '5432')
DYNAMIC_DB_NAME = os.environ.get('DYNAMIC_DB_NAME', 'dynamic_forms')
DYNAMIC_DB_USER = os.environ.get('DYNAMIC_DB_USER', '')
DYNAMIC_DB_PASSWORD = os.environ.get('DYNAMIC_DB_PASSWORD', '')
DYNAMIC_DB_SSL = os.environ.get('DYNAMIC_DB_SSL', 'false').lower() == 'true'

# Static Database (Production/Stable)
STATIC_DB_TYPE = os.environ.get('STATIC_DB_TYPE', 'sqlite')  # sqlite, postgresql, mysql
STATIC_DB_HOST = os.environ.get('STATIC_DB_HOST', 'localhost')
STATIC_DB_PORT = os.environ.get('STATIC_DB_PORT', '5432')
STATIC_DB_NAME = os.environ.get('STATIC_DB_NAME', 'static_forms')
STATIC_DB_USER = os.environ.get('STATIC_DB_USER', '')
STATIC_DB_PASSWORD = os.environ.get('STATIC_DB_PASSWORD', '')
STATIC_DB_SSL = os.environ.get('STATIC_DB_SSL', 'false').lower() == 'true'

# Direct URL override (takes precedence over individual settings)
DYNAMIC_DATABASE_URL = os.environ.get('DYNAMIC_DATABASE_URL', '')
STATIC_DATABASE_URL = os.environ.get('STATIC_DATABASE_URL', '')


def get_database_url(db_type: str, host: str, port: str, name: str,
                     user: str, password: str, ssl: bool = False) -> str:
    """
    Build a database URL from components.

    Args:
        db_type: Database type (sqlite, postgresql, mysql)
        host: Database host
        port: Database port
        name: Database name
        user: Database user
        password: Database password
        ssl: Whether to use SSL

    Returns:
        SQLAlchemy database URL
    """
    if db_type == 'sqlite':
        # SQLite uses file path
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(db_dir, exist_ok=True)
        return f"sqlite:///{os.path.join(db_dir, f'{name}.db')}"

    elif db_type == 'postgresql':
        # PostgreSQL connection string
        url = f"postgresql://{user}:{quote_plus(password)}@{host}:{port}/{name}"
        if ssl:
            url += "?sslmode=require"
        return url

    elif db_type == 'mysql':
        # MySQL connection string
        url = f"mysql+pymysql://{user}:{quote_plus(password)}@{host}:{port}/{name}"
        if ssl:
            url += "?ssl=true"
        return url

    elif db_type == 'mssql':
        # Microsoft SQL Server
        return f"mssql+pyodbc://{user}:{quote_plus(password)}@{host}:{port}/{name}?driver=ODBC+Driver+17+for+SQL+Server"

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def get_dynamic_db_url() -> str:
    """Get the dynamic database URL"""
    if DYNAMIC_DATABASE_URL:
        return DYNAMIC_DATABASE_URL

    return get_database_url(
        DYNAMIC_DB_TYPE, DYNAMIC_DB_HOST, DYNAMIC_DB_PORT,
        DYNAMIC_DB_NAME, DYNAMIC_DB_USER, DYNAMIC_DB_PASSWORD, DYNAMIC_DB_SSL
    )


def get_static_db_url() -> str:
    """Get the static database URL"""
    if STATIC_DATABASE_URL:
        return STATIC_DATABASE_URL

    return get_database_url(
        STATIC_DB_TYPE, STATIC_DB_HOST, STATIC_DB_PORT,
        STATIC_DB_NAME, STATIC_DB_USER, STATIC_DB_PASSWORD, STATIC_DB_SSL
    )


# ============ CLOUD PROVIDER EXAMPLES ============

CLOUD_EXAMPLES = {
    'aws_rds_postgresql': {
        'env_vars': {
            'DYNAMIC_DB_TYPE': 'postgresql',
            'DYNAMIC_DB_HOST': 'your-instance.region.rds.amazonaws.com',
            'DYNAMIC_DB_PORT': '5432',
            'DYNAMIC_DB_NAME': 'dynamic_forms',
            'DYNAMIC_DB_USER': 'admin',
            'DYNAMIC_DB_PASSWORD': 'your-password',
            'DYNAMIC_DB_SSL': 'true'
        },
        'description': 'Amazon RDS PostgreSQL'
    },
    'aws_rds_mysql': {
        'env_vars': {
            'DYNAMIC_DB_TYPE': 'mysql',
            'DYNAMIC_DB_HOST': 'your-instance.region.rds.amazonaws.com',
            'DYNAMIC_DB_PORT': '3306',
            'DYNAMIC_DB_NAME': 'dynamic_forms',
            'DYNAMIC_DB_USER': 'admin',
            'DYNAMIC_DB_PASSWORD': 'your-password',
            'DYNAMIC_DB_SSL': 'true'
        },
        'description': 'Amazon RDS MySQL'
    },
    'google_cloud_sql': {
        'env_vars': {
            'DYNAMIC_DATABASE_URL': 'postgresql://user:password@/dbname?host=/cloudsql/project:region:instance'
        },
        'description': 'Google Cloud SQL (via Unix socket)'
    },
    'azure_postgresql': {
        'env_vars': {
            'DYNAMIC_DB_TYPE': 'postgresql',
            'DYNAMIC_DB_HOST': 'your-server.postgres.database.azure.com',
            'DYNAMIC_DB_PORT': '5432',
            'DYNAMIC_DB_NAME': 'dynamic_forms',
            'DYNAMIC_DB_USER': 'user@your-server',
            'DYNAMIC_DB_PASSWORD': 'your-password',
            'DYNAMIC_DB_SSL': 'true'
        },
        'description': 'Azure Database for PostgreSQL'
    },
    'heroku_postgres': {
        'env_vars': {
            'DYNAMIC_DATABASE_URL': 'postgres://user:password@host:5432/dbname'
        },
        'description': 'Heroku Postgres (use DATABASE_URL from Heroku config)'
    },
    'supabase': {
        'env_vars': {
            'DYNAMIC_DATABASE_URL': 'postgresql://postgres:password@db.your-project.supabase.co:5432/postgres'
        },
        'description': 'Supabase PostgreSQL'
    },
    'planetscale': {
        'env_vars': {
            'DYNAMIC_DB_TYPE': 'mysql',
            'DYNAMIC_DATABASE_URL': 'mysql://user:password@host/database?ssl={"rejectUnauthorized":true}'
        },
        'description': 'PlanetScale MySQL'
    },
    'neon': {
        'env_vars': {
            'DYNAMIC_DATABASE_URL': 'postgresql://user:password@ep-cool-name.region.aws.neon.tech/neondb?sslmode=require'
        },
        'description': 'Neon Serverless Postgres'
    },
    'cockroachdb': {
        'env_vars': {
            'DYNAMIC_DATABASE_URL': 'cockroachdb://user:password@free-tier.gcp-us-central1.cockroachlabs.cloud:26257/database?sslmode=verify-full'
        },
        'description': 'CockroachDB Serverless'
    }
}


def print_cloud_examples():
    """Print cloud configuration examples"""
    print("\n" + "="*60)
    print("CLOUD DATABASE CONFIGURATION EXAMPLES")
    print("="*60 + "\n")

    for provider, config in CLOUD_EXAMPLES.items():
        print(f"\n{config['description']} ({provider})")
        print("-" * 40)
        for key, value in config['env_vars'].items():
            print(f"export {key}='{value}'")

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    print_cloud_examples()
