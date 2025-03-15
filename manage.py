#!/usr/bin/env python
from flask.cli import FlaskGroup
from app import create_app
import os
import click

app = create_app()
cli = FlaskGroup(create_app=lambda: app)

@cli.command("init_migrations")
def init_migrations():
    """Safely initialize or update migrations."""
    from flask_migrate import init, migrate, stamp
    
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    if os.path.exists(migrations_dir) and os.listdir(migrations_dir):
        click.echo("Migrations directory already exists. Skipping initialization.")
        return
    
    click.echo("Initializing migrations directory...")
    init()
    click.echo("Creating initial migration...")
    migrate(message="Initial migration")
    click.echo("Stamping database with current version...")
    stamp()
    click.echo("Database migration initialization complete.")

if __name__ == "__main__":
    cli()
