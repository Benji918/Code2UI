#!/bin/bash
# Quick setup script for Code2UI with streaming

echo "🚀 Code2UI - Installing dependencies..."

# Install missing Python packages
pip install python-dotenv celery redis sse-starlette

echo "✅ Dependencies installed!"
echo ""
echo "📋 Next steps:"
echo "1. Make sure Redis is running: sudo service redis-server start"
echo "2. Restart Celery worker (Ctrl+C then re-run):"
echo "   celery -A celery_app worker --loglevel=info"
echo ""
echo "3. Your .env file is already configured with the Mistral API key"
echo ""
echo "4. The FastAPI server should also be restarted to pick up changes"
