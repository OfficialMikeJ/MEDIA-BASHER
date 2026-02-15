#!/bin/bash

echo "========================================="
echo "   Switch to PostgreSQL"
echo "========================================="
echo ""

# Stop MongoDB attempts
sudo docker stop mongodb 2>/dev/null || true
sudo docker rm mongodb 2>/dev/null || true
sudo systemctl stop mongod 2>/dev/null || true
sudo systemctl disable mongod 2>/dev/null || true

# Install PostgreSQL
echo "Installing PostgreSQL..."
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
echo "Creating database..."
sudo -u postgres psql -c "CREATE DATABASE media_basher;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER mediabasher WITH PASSWORD 'mediabasher123';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE media_basher TO mediabasher;"
sudo -u postgres psql -d media_basher -c "GRANT ALL ON SCHEMA public TO mediabasher;"

# Update backend requirements
echo "Updating Python dependencies..."
cd /opt/media-basher/backend
source venv/bin/activate
pip install psycopg2-binary sqlalchemy asyncpg -q

# Update .env file
echo "Updating configuration..."
cat > .env << EOF
DATABASE_URL=postgresql://mediabasher:mediabasher123@localhost/media_basher
CORS_ORIGINS=*
JWT_SECRET=$(openssl rand -hex 32)
EOF

deactivate

echo ""
echo "✓ PostgreSQL is installed and configured!"
echo ""
echo "Next step: Update the backend code to use PostgreSQL."
echo "I'll provide the updated server.py file."
echo ""
echo "========================================="
