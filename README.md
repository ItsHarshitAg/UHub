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
