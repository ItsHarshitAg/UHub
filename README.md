# USEHub - User Skills Exchange Hub

USEHub is a platform for users to share skills, collaborate on projects, and network with professionals.

## Local Development

### Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - MacOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables:
   - Create a `.env` file with:

     ```env
     SECRET_KEY=your_secret_key
     DATABASE_URL=sqlite:///instance/database.db
     ```

### Running the Application

1. Run the application: `flask run`
2. Visit `http://localhost:5000` in your browser

## Deploying to Render

1. Push your code to GitHub
2. Log in to [Render](https://render.com)
3. Click "New +" and select "Web Service"
4. Connect your GitHub repository
5. Use the following settings:
   - Name: usehub (or your preferred name)
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
   - Region: Choose the closest to your target audience
   - Branch: main
   - Auto Deploy: Yes

6. Click "Advanced" and add environment variables:
   - `SECRET_KEY`: Generate a secure random string
   - `MIGRATION_SECRET`: Generate another secure string

7. Click "Create Web Service"

## PostgreSQL Database Setup

1. On Render dashboard, click "New +" and select "PostgreSQL"
2. Configure your database:
   - Name: "usehub-db" (or your preferred name)
   - Database: Leave default
   - User: Leave default
   - Region: Same as your web service
   - PostgreSQL Version: Latest

3. Click "Create Database"
4. Once created, go to your database dashboard to find the internal connection string
5. Go to your web service settings > Environment
6. Add the `DATABASE_URL` variable with the internal connection string
7. Deploy your web service again

8. To initialize your database in production, visit:
   `https://your-app-url.onrender.com/admin/run_migrations/YOUR_MIGRATION_SECRET`
   Replace YOUR_MIGRATION_SECRET with the value you set earlier

## Default Admin User

- Email: <admin@gmail.com>
- Password: admin

For security, change the admin password after first login in production.
