from app import create_app, db

application = app = create_app()  # Both names for compatibility with different WSGI servers

# No __main__ block - this file just exposes the application for WSGI servers



