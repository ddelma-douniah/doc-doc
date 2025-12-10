#!/bin/bash
# Script de réparation automatique pour doc-doc
# Résout le problème "relation does not exist"
# Usage : bash fix-now.sh

set -e

echo "========================================"
echo "   Réparation doc-doc"
echo "========================================"
echo ""

cd /opt/douniah/doc-doc || {
    echo "Erreur : Impossible de trouver /opt/douniah/doc-doc"
    echo "Ajustez le chemin dans le script si nécessaire"
    exit 1
}

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les étapes
step() {
    echo ""
    echo -e "${BLUE}==> $1${NC}"
}

# Fonction pour afficher le succès
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Fonction pour afficher l'erreur
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Vérifier que Docker fonctionne
step "Vérification de Docker"
if ! docker compose ps &>/dev/null; then
    error "Docker Compose ne répond pas"
    exit 1
fi
success "Docker Compose OK"

# Vérifier l'état des containers
step "État des containers"
docker compose ps

# Étape 1 : Vérifier la connexion DB
step "Étape 1/6 : Vérification connexion base de données"
if docker compose exec -T web python manage.py check --database default &>/dev/null; then
    success "Connexion DB OK"
else
    error "La connexion à la base de données a échoué"
    echo ""
    echo "Vérifiez :"
    echo "  1. Que le container 'db' tourne : docker compose ps db"
    echo "  2. Les logs DB : docker compose logs db"
    echo "  3. Les variables d'environnement dans .env"
    exit 1
fi

# Étape 2 : Exécuter les migrations
step "Étape 2/6 : Exécution des migrations Django"
echo "Cela peut prendre quelques secondes..."
if docker compose exec -T web python manage.py migrate --noinput; then
    success "Migrations appliquées avec succès"
else
    error "Échec des migrations"
    echo "Voir les logs : docker compose logs web"
    exit 1
fi

# Étape 3 : Initialiser les SocialApps
step "Étape 3/6 : Initialisation des SocialApps (OAuth)"
if docker compose exec -T web python manage.py init_socialapps &>/dev/null; then
    success "SocialApps initialisés"
else
    echo -e "${YELLOW}⚠ Commande init_socialapps non disponible (peut être normal)${NC}"
fi

# Étape 4 : Collecter les fichiers statiques
step "Étape 4/6 : Collection des fichiers statiques"
if docker compose exec -T web python manage.py collectstatic --noinput --clear; then
    success "Fichiers statiques collectés"
else
    error "Échec de la collection des fichiers statiques"
fi

# Compter les fichiers statiques
STATIC_COUNT=$(docker compose exec -T web find /app/staticfiles -type f 2>/dev/null | wc -l || echo "0")
echo "Nombre de fichiers statiques : $STATIC_COUNT"

# Étape 5 : Redémarrer le container web
step "Étape 5/6 : Redémarrage du container web"
docker compose restart web
success "Container redémarré"

echo "Attente du démarrage (10 secondes)..."
sleep 10

# Étape 6 : Vérification finale
step "Étape 6/6 : Tests de vérification"

# Test 1 : HTTP interne
HTTP_STATUS=$(docker compose exec -T web curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    success "Application répond (HTTP $HTTP_STATUS)"
else
    error "Application erreur HTTP $HTTP_STATUS"
fi

# Test 2 : Compter les tables
TABLE_COUNT=$(docker compose exec -T db psql -U doc_doc_user -d doc_doc -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs || echo "0")
echo "Nombre de tables dans la DB : $TABLE_COUNT"

if [ "$TABLE_COUNT" -gt 10 ]; then
    success "Base de données peuplée"
else
    error "Base de données incomplète"
fi

# Résumé final
echo ""
echo "========================================"
echo -e "${GREEN}✓ RÉPARATION TERMINÉE${NC}"
echo "========================================"
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. Créer un superuser (si pas encore fait) :"
echo "   ${YELLOW}docker compose exec web python manage.py createsuperuser${NC}"
echo ""
echo "2. Tester dans le navigateur :"
echo "   ${BLUE}https://doc-doc.douniah.com/${NC}"
echo "   ${BLUE}https://doc-doc.douniah.com/admin/${NC}"
echo ""
echo "3. Vérifier les logs si problème :"
echo "   ${YELLOW}docker compose logs web --tail=50${NC}"
echo ""
echo "4. Vérifier les static files :"
echo "   ${YELLOW}curl -I https://doc-doc.douniah.com/static/admin/css/base.css${NC}"
echo ""
echo "========================================"
