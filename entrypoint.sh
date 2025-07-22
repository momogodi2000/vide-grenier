
# entrypoint.sh
#!/bin/bash

# Attendre que la base de données soit prête
echo "Waiting for database..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done
echo "Database is ready!"

# Appliquer les migrations
echo "Applying migrations..."
python manage.py migrate

# Collecter les fichiers statiques
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Créer les utilisateurs de test en développement
if [ "$DEBUG" = "True" ]; then
    echo "Creating test users..."
    python manage.py create_test_users --with-demo-data
fi

# Démarrer le serveur
echo "Starting server..."
exec "$@"
