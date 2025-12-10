#!/bin/bash
# Script de diagnostic pour doc-doc
# Exécuter sur le serveur : bash diagnose.sh

set -e

echo "========================================"
echo "   Diagnostic doc-doc"
echo "========================================"
echo ""

cd /opt/douniah/doc-doc

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier les containers
echo -e "${YELLOW}1. État des containers${NC}"
docker compose ps
echo ""

# 2. Vérifier la connexion DB
echo -e "${YELLOW}2. Test connexion base de données${NC}"
if docker compose exec -T web python manage.py check --database default &>/dev/null; then
    echo -e "${GREEN}✓ Connexion DB OK${NC}"
else
    echo -e "${RED}✗ Connexion DB échouée${NC}"
    echo "Vérifier les logs : docker compose logs db"
fi
echo ""

# 3. Vérifier les migrations
echo -e "${YELLOW}3. État des migrations${NC}"
docker compose exec -T web python manage.py showmigrations | head -30
echo ""

# 4. Compter les migrations non appliquées
UNAPPLIED=$(docker compose exec -T web python manage.py showmigrations | grep -c "\[ \]" || echo "0")
echo "Migrations non appliquées : $UNAPPLIED"
echo ""

# 5. Vérifier les tables dans la DB
echo -e "${YELLOW}4. Tables dans la base de données${NC}"
docker compose exec -T db psql -U doc_doc_user -d doc_doc -c "\dt" | head -20
echo ""

# 6. Vérifier les fichiers statiques
echo -e "${YELLOW}5. Fichiers statiques${NC}"
STATIC_COUNT=$(docker compose exec -T web find /app/staticfiles -type f 2>/dev/null | wc -l || echo "0")
echo "Nombre de fichiers statiques : $STATIC_COUNT"

if [ "$STATIC_COUNT" -gt 100 ]; then
    echo -e "${GREEN}✓ Static files présents${NC}"
else
    echo -e "${RED}✗ Static files manquants${NC}"
fi
echo ""

# 7. Tester l'accès HTTP interne
echo -e "${YELLOW}6. Test HTTP interne${NC}"
HTTP_STATUS=$(docker compose exec -T web curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null || echo "000")
echo "Status HTTP interne : $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "302" ]; then
    echo -e "${GREEN}✓ Application répond${NC}"
else
    echo -e "${RED}✗ Application erreur $HTTP_STATUS${NC}"
fi
echo ""

# 8. Logs récents
echo -e "${YELLOW}7. Derniers logs (20 lignes)${NC}"
docker compose logs web --tail=20
echo ""

# Résumé et actions recommandées
echo "========================================"
echo -e "${YELLOW}RÉSUMÉ${NC}"
echo "========================================"
echo ""

if [ "$UNAPPLIED" -gt 0 ]; then
    echo -e "${RED}⚠ ACTIONS REQUISES :${NC}"
    echo ""
    echo "1. Exécuter les migrations :"
    echo "   docker compose exec web python manage.py migrate --noinput"
    echo ""
    echo "2. Initialiser les SocialApps :"
    echo "   docker compose exec web python manage.py init_socialapps"
    echo ""
    echo "3. Créer un superuser :"
    echo "   docker compose exec web python manage.py createsuperuser"
    echo ""
    echo "4. Collecter les static files :"
    echo "   docker compose exec web python manage.py collectstatic --noinput --clear"
    echo ""
    echo "5. Redémarrer :"
    echo "   docker compose restart web"
    echo ""
elif [ "$STATIC_COUNT" -lt 100 ]; then
    echo -e "${YELLOW}⚠ STATIC FILES MANQUANTS :${NC}"
    echo ""
    echo "   docker compose exec web python manage.py collectstatic --noinput --clear"
    echo "   docker compose restart web"
    echo ""
elif [ "$HTTP_STATUS" != "200" ] && [ "$HTTP_STATUS" != "302" ]; then
    echo -e "${RED}⚠ APPLICATION ERREUR :${NC}"
    echo ""
    echo "Voir les logs complets :"
    echo "   docker compose logs web | less"
    echo ""
else
    echo -e "${GREEN}✓✓✓ Tout semble OK !${NC}"
    echo ""
    echo "Tester dans le navigateur :"
    echo "   https://doc-doc.douniah.com/"
    echo ""
fi

echo "========================================"
