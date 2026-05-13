# 🚀 AI Investment Platform - Complete Deployment Guide

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Production Setup](#production-setup)
4. [End-to-End Testing](#end-to-end-testing)
5. [Architecture Overview](#architecture-overview)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Prerequisites

### Required Software:
- **Docker** & **Docker Compose**
- **Git** (for cloning)
- **Node.js 18+** (if running locally)
- **Python 3.12+** (if running locally)

### Required API Keys:
- **Groq API Key** (for LLM functionality)
- **OpenAI API Key** (optional alternative)

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
# Clone the repository
git clone <repository-url>
cd AI-Investment-Platform

# Create environment file (optional)
echo "GROQ_API_KEY=your_groq_key_here" > .env
```

### 2. Start Development Stack
```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access URLs
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

---

## 🏭 Production Setup

### 1. Environment Configuration
```bash
# Create production environment file
cat > .env << EOF
# Database (PostgreSQL)
DATABASE_URL=postgresql://ai_app:your_secure_password@postgres:5432/ai_investment

# Redis
REDIS_URL=redis://redis:6379/0

# CORS Origins
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Optional: Default LLM (if user hasn't set)
DEFAULT_LLM_PROVIDER=groq
EOF
```

### 2. Production Deployment
```bash
# Deploy with PostgreSQL
docker-compose -f docker-compose.yml up -d --build

# Run database migrations (one-time)
docker-compose exec backend python -m alembic upgrade head

# Check service status
docker-compose ps
```

### 3. Production URLs
- **Frontend**: https://yourdomain.com
- **Backend API**: https://api.yourdomain.com
- **Load Balancer**: Configure Nginx/Cloudflare

---

## 🧪 End-to-End Testing

### 1. Test Backend Services
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test LLM providers
curl http://localhost:8000/api/v1/llm/providers

# Expected response:
{
  "providers": [
    {"value": "openai", "label": "OpenAI GPT", "model": "gpt-3.5-turbo"},
    {"value": "groq", "label": "Groq (Llama)", "model": "llama-3.1-8b-instant"}
  ]
}
```

### 2. Test User Registration & Authentication
```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123456"}'

# Login user
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123456"}'
```

### 3. Test LLM Configuration
```bash
# Test connection with Groq
curl -X POST http://localhost:8000/api/v1/llm/test \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "groq", "api_key": "gsk_your_groq_key"}'

# Save LLM settings
curl -X POST http://localhost:8000/api/v1/llm/settings \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"provider": "groq", "api_key": "gsk_your_groq_key"}'

# Load saved settings
curl -X GET http://localhost:8000/api/v1/llm/settings \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Test Investment Analysis
```bash
# Start analysis
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "budget": 10000,
    "risk": "medium",
    "goal": "growth",
    "interests": ["Technology", "Semiconductors"]
  }'

# Expected response:
{
  "session_id": "uuid-here",
  "status": "processing"
}
```

### 5. Check Analysis Progress
```bash
# Monitor analysis status
curl -X GET http://localhost:8000/api/v1/analysis/{session_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Expected response:
{
  "session_id": "uuid-here",
  "status": "completed",
  "progress": {
    "planner": "completed",
    "market_research": "completed",
    "financial_analysis": "completed",
    "technical_analysis": "completed",
    "news_sentiment": "completed",
    "risk_analysis": "completed",
    "portfolio_allocation": "completed",
    "report_generation": "completed"
  }
}
```

---

## 🏗️ Architecture Overview

### 📊 Service Components
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend    │    │    Backend     │    │   Database     │
│   (React)    │◄──►│   (FastAPI)   │◄──►│ (PostgreSQL)   │
│   Port: 3000  │    │   Port: 8000  │    │   Port: 5432  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────────────┐    ┌─────────────────┐
    │     Redis     │    │     Nginx     │
    │   (Caching)   │◄──►│ (Reverse Proxy)│
    │   Port: 6379  │    │   Port: 80/443 │
    └─────────────────┘    └─────────────────┘
```

### 🔄 Data Flow
1. **User Input** → Frontend React App
2. **API Calls** → Backend FastAPI
3. **Authentication** → JWT Token Validation
4. **LLM Settings** → Database Storage (Encrypted)
5. **Analysis Request** → Background Job Queue
6. **Multi-Agent System** → LangGraph Workflow
7. **Report Generation** → User's Selected LLM Provider
8. **Results** → Database Storage → Frontend Display

### 🧠 AI Agent Pipeline
```
Input Analysis
       ↓
Market Research → Financial Analysis → Technical Analysis
       ↓                              ↓
   News Sentiment Analysis → Risk Assessment
       ↓                              ↓
     Portfolio Allocation → Report Generation
       ↓                              ↓
          User's Selected LLM (Groq/OpenAI)
```

---

## 🔍 Monitoring & Troubleshooting

### Check Service Health
```bash
# All services status
docker-compose ps

# Individual service logs
docker-compose logs backend    # FastAPI logs
docker-compose logs frontend   # Nginx logs
docker-compose logs postgres   # Database logs
docker-compose logs redis      # Cache logs
```

### Common Issues & Solutions

#### Database Connection Issues
```bash
# Check PostgreSQL connection
docker-compose exec backend python -c "
from app.db.init_db import get_connection
import asyncio
async def test():
    db = await get_connection()
    print('Database connection: OK')
asyncio.run(test())
"
```

#### LLM Provider Issues
```bash
# Test API key validity
curl -X POST http://localhost:8000/api/v1/llm/test \
  -H "Authorization: Bearer TOKEN" \
  -d '{"provider": "groq", "api_key": "INVALID_KEY"}'

# Expected error: "Invalid API key. Please check your Groq API key"
```

#### Analysis Job Issues
```bash
# Check analysis jobs table
docker-compose exec postgres psql -U ai_app -d ai_investment -c "
SELECT session_id, status, created_at FROM analysis_sessions ORDER BY created_at DESC LIMIT 10;
"
```

---

## 🚀 Production Deployment Checklist

### Pre-Deployment:
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Load balancer configured
- [ ] Monitoring tools set up

### Post-Deployment:
- [ ] All services running (`docker-compose ps`)
- [ ] Health endpoints responding
- [ ] Database accessible
- [ ] API documentation accessible
- [ ] Frontend loads correctly
- [ ] User registration works
- [ ] LLM configuration saves
- [ ] Analysis pipeline completes

---

## 📝 Development Commands

### Local Development
```bash
# Start backend only
cd backend && python -m uvicorn app.main:app --reload

# Start frontend only
cd frontend && npm run dev

# Run tests
pytest backend/tests/
```

### Database Management
```bash
# Create migrations
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Reset database (development only)
alembic downgrade base
```

---

## 🔐 Security Notes

### API Key Security
- API keys are encrypted using Fernet (AES-256)
- Keys stored in PostgreSQL with user isolation
- Each user can have multiple provider configurations
- JWT tokens expire after configurable time

### Network Security
- CORS configured for specific origins
- Database not exposed to internet
- All API endpoints require authentication

---

## 📈 Scaling Considerations

### Horizontal Scaling
- **Frontend**: Multiple Nginx instances behind load balancer
- **Backend**: Multiple FastAPI containers with Redis session store
- **Database**: PostgreSQL read replicas for analytics queries
- **Cache**: Redis cluster for session management

### Performance Optimization
- **Database**: Connection pooling, query optimization
- **API**: Response caching, rate limiting
- **Frontend**: Code splitting, lazy loading
- **LLM**: Request batching, provider failover

---

## 🎯 Production URLs Summary

| Service | Local | Production |
|----------|--------|------------|
| Frontend | http://localhost:3000 | https://yourdomain.com |
| Backend API | http://localhost:8000 | https://api.yourdomain.com |
| Database | localhost:5432 | postgres:5432 |
| Redis | localhost:6379 | redis:6379 |
| API Docs | http://localhost:8000/docs | https://api.yourdomain.com/docs |

---

**🎉 Your AI Investment Platform is now ready for production deployment!**
