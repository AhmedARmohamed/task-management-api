# FastAPI Task Management System

A secure, production-ready FastAPI backend for task management with user authentication, JWT tokens, and API key protection.

## Features

- **User Authentication**: Secure user registration and login with JWT tokens
- **Task Management**: Full CRUD operations for tasks with user isolation
- **Security**: Dual authentication (JWT + API Key) for all protected endpoints
- **Database**: Async SQLite with SQLAlchemy ORM
- **Docker**: Containerized for easy deployment
- **CI/CD**: GitHub Actions pipeline for testing and deployment
- **Production Ready**: Comprehensive error handling, logging, and security measures

## Quick Start

### Local Development

1. **Set up environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Copy environment variables
   cp .env.example .env
   ```

2. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

3. **Access the API**
   - API Documentation: http://localhost:8000/docs
   - Alternative Docs: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

### Docker Deployment

1. **Build and run with Docker**
   ```bash
   docker build -t task-management-api .
   docker run -p 8000:8000 task-management-api
   ```

2. **Or use Docker Compose**
   ```bash
   docker-compose up --build
   ```

## API Endpoints

### Authentication

- `POST /signup` - Create a new user account
- `POST /token` - Login and get JWT token (OAuth2 password flow)

### Tasks

All task endpoints require both JWT token and API key authentication.

- `POST /tasks` - Create a new task
- `GET /tasks` - Get all tasks for the authenticated user
- `GET /task/{id}` - Get a specific task
- `PUT /task/{id}` - Update a task
- `DELETE /task/{id}` - Delete a task

### Health Check

- `GET /health` - API health status

## Authentication

The API uses dual authentication:

1. **JWT Token**: Include `Authorization: Bearer <token>` header
2. **API Key**: Include `x-api-key: 123456` header

### Example Usage with cURL

1. **Register a user**
   ```bash
   curl -X POST "http://localhost:8000/signup" \
     -H "Content-Type: application/json" \
     -d '{"username": "johndoe", "password": "secret123"}'
   ```

2. **Login to get token**
   ```bash
   curl -X POST "http://localhost:8000/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=johndoe&password=secret123"
   ```

3. **Create a task**
   ```bash
   curl -X POST "http://localhost:8000/tasks" \
     -H "Authorization: Bearer <your-jwt-token>" \
     -H "x-api-key: 123456" \
     -H "Content-Type: application/json" \
     -d '{"title": "My Task", "description": "Task description", "status": "pending"}'
   ```

4. **Get all tasks**
   ```bash
   curl -X GET "http://localhost:8000/tasks" \
     -H "Authorization: Bearer <your-jwt-token>" \
     -H "x-api-key: 123456"
   ```

5. **Update a task**
   ```bash
   curl -X PUT "http://localhost:8000/task/1" \
     -H "Authorization: Bearer <your-jwt-token>" \
     -H "x-api-key: 123456" \
     -H "Content-Type: application/json" \
     -d '{"status": "completed"}'
   ```

6. **Delete a task**
   ```bash
   curl -X DELETE "http://localhost:8000/task/1" \
     -H "Authorization: Bearer <your-jwt-token>" \
     -H "x-api-key: 123456"
   ```

## Data Models

### User Model
- `id`: Integer (auto-generated)
- `username`: String (unique)
- `hashed_password`: String (securely hashed)
- `created_at`: Timestamp

### Task Model
- `id`: Integer (auto-generated)
- `user_id`: Foreign key to users
- `title`: String
- `description`: String (optional)
- `status`: Enum ("pending", "completed")
- `created_at`: Timestamp

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
DATABASE_URL=sqlite+aiosqlite:///./tasks.db
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY=123456
APP_NAME=Task Management API
DEBUG=False
```

## Testing

Run tests with pytest:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Deployment

### Railway

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard
3. Deploy automatically on git push

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- API key validation
- SQL injection prevention with ORM
- Input validation with Pydantic
- CORS protection
- Rate limiting ready (can be added with slowapi)
- Secure headers

## Testing with Postman

Import the following collection or create requests manually:

### 1. Health Check
- Method: GET
- URL: `http://localhost:8000/health`

### 2. User Signup
- Method: POST
- URL: `http://localhost:8000/signup`
- Body (JSON):
  ```json
  {
    "username": "testuser",
    "password": "testpass123"
  }
  ```

### 3. User Login
- Method: POST
- URL: `http://localhost:8000/token`
- Body (form-data):
  - username: testuser
  - password: testpass123

### 4. Create Task
- Method: POST
- URL: `http://localhost:8000/tasks`
- Headers:
  - Authorization: Bearer {your_jwt_token}
  - x-api-key: 123456
- Body (JSON):
  ```json
  {
    "title": "Complete project",
    "description": "Finish the FastAPI task management system",
    "status": "pending"
  }
  ```

### 5. Get All Tasks
- Method: GET
- URL: `http://localhost:8000/tasks`
- Headers:
  - Authorization: Bearer {your_jwt_token}
  - x-api-key: 123456

### 6. Get Specific Task
- Method: GET
- URL: `http://localhost:8000/task/1`
- Headers:
  - Authorization: Bearer {your_jwt_token}
  - x-api-key: 123456

### 7. Update Task
- Method: PUT
- URL: `http://localhost:8000/task/1`
- Headers:
  - Authorization: Bearer {your_jwt_token}
  - x-api-key: 123456
- Body (JSON):
  ```json
  {
    "status": "completed"
  }
  ```

### 8. Delete Task
- Method: DELETE
- URL: `http://localhost:8000/task/1`
- Headers:
  - Authorization: Bearer {your_jwt_token}
  - x-api-key: 123456

## Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a secure random string
- [ ] Update `API_KEY` to a secure value
- [ ] Set `DEBUG=False`
- [ ] Configure proper CORS origins
- [ ] Set up proper logging
- [ ] Configure database backups
- [ ] Set up monitoring and alerting
- [ ] Review and update security settings
- [ ] Configure SSL/TLS termination
- [ ] Set up rate limiting
- [ ] Configure proper error handling