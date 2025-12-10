#!/bin/bash

# Script de diagnostic des fichiers statiques
# Usage : ./check_static.sh

echo "=========================================="
echo "   Diagnostic Fichiers Statiques"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Vérifier que WhiteNoise est installé
echo -e "${YELLOW}1. Vérification de WhiteNoise...${NC}"
if docker compose exec -T web python -c "import whitenoise; print(f'Version: {whitenoise.__version__}')" 2>/dev/null; then
    echo -e "${GREEN}✓ WhiteNoise installé${NC}"
else
    echo -e "${RED}✗ WhiteNoise non installé${NC}"
    echo "   Installer avec : pip install whitenoise"
fi
echo ""

# 2. Vérifier STATIC_ROOT
echo -e "${YELLOW}2. Vérification de STATIC_ROOT...${NC}"
STATIC_ROOT=$(docker compose exec -T web python -c "from django.conf import settings; print(settings.STATIC_ROOT)" 2>/dev/null)
if [ ! -z "$STATIC_ROOT" ]; then
    echo -e "${GREEN}✓ STATIC_ROOT configuré : $STATIC_ROOT${NC}"
else
    echo -e "${RED}✗ STATIC_ROOT non configuré${NC}"
fi
echo ""

# 3. Vérifier si les fichiers statiques existent
echo -e "${YELLOW}3. Vérification des fichiers collectés...${NC}"
FILE_COUNT=$(docker compose exec -T web find /app/staticfiles -type f 2>/dev/null | wc -l)
if [ $FILE_COUNT -gt 0 ]; then
    echo -e "${GREEN}✓ $FILE_COUNT fichiers statiques trouvés${NC}"
else
    echo -e "${RED}✗ Aucun fichier statique trouvé${NC}"
    echo "   Exécuter : docker compose exec web python manage.py collectstatic --noinput"
fi
echo ""

# 4. Vérifier les fichiers admin spécifiques
echo -e "${YELLOW}4. Vérification des fichiers admin...${NC}"
for file in "admin/css/base.css" "admin/css/login.css" "admin/js/theme.js" "admin/js/nav_sidebar.js"; do
    if docker compose exec -T web test -f "/app/staticfiles/$file" 2>/dev/null; then
        SIZE=$(docker compose exec -T web stat -f%z "/app/staticfiles/$file" 2>/dev/null || docker compose exec -T web stat -c%s "/app/staticfiles/$file" 2>/dev/null)
        echo -e "${GREEN}✓ $file ($SIZE bytes)${NC}"
    else
        echo -e "${RED}✗ $file - MANQUANT${NC}"
    fi
done
echo ""

# 5. Tester l'accès HTTP interne
echo -e "${YELLOW}5. Test d'accès HTTP interne...${NC}"
HTTP_STATUS=$(docker compose exec -T web curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/static/admin/css/base.css 2>/dev/null)
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Fichier accessible via HTTP (status: $HTTP_STATUS)${NC}"
else
    echo -e "${RED}✗ Erreur HTTP (status: $HTTP_STATUS)${NC}"
fi
echo ""

# 6. Vérifier le middleware WhiteNoise
echo -e "${YELLOW}6. Vérification du middleware WhiteNoise...${NC}"
if docker compose exec -T web python -c "from django.conf import settings; print('whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE)" 2>/dev/null | grep -q "True"; then
    echo -e "${GREEN}✓ WhiteNoise middleware activé${NC}"
else
    echo -e "${RED}✗ WhiteNoise middleware NON activé${NC}"
    echo "   Ajouter dans settings.py MIDDLEWARE"
fi
echo ""

# 7. Vérifier le storage backend
echo -e "${YELLOW}7. Vérification du storage backend...${NC}"
STORAGE_BACKEND=$(docker compose exec -T web python -c "from django.conf import settings; print(settings.STORAGES.get('staticfiles', {}).get('BACKEND', 'Not set'))" 2>/dev/null)
echo "   Backend actuel : $STORAGE_BACKEND"
if echo "$STORAGE_BACKEND" | grep -q "whitenoise"; then
    echo -e "${GREEN}✓ WhiteNoise storage configuré${NC}"
else
    echo -e "${YELLOW}⚠ Backend différent (peut fonctionner)${NC}"
fi
echo ""

# 8. Test via l'URL publique (si disponible)
echo -e "${YELLOW}8. Test via URL publique...${NC}"
PUBLIC_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://doc-doc.douniah.com/static/admin/css/base.css 2>/dev/null)
if [ "$PUBLIC_STATUS" = "200" ]; then
    echo -e "${GREEN}✓ Fichier accessible publiquement (status: $PUBLIC_STATUS)${NC}"

    # Vérifier le Content-Type
    CONTENT_TYPE=$(curl -s -I https://doc-doc.douniah.com/static/admin/css/base.css 2>/dev/null | grep -i "content-type" | cut -d: -f2 | tr -d '[:space:]')
    if [[ "$CONTENT_TYPE" == "text/css"* ]]; then
        echo -e "${GREEN}✓ Content-Type correct : $CONTENT_TYPE${NC}"
    else
        echo -e "${RED}✗ Content-Type incorrect : $CONTENT_TYPE${NC}"
    fi
else
    echo -e "${RED}✗ Erreur publique (status: $PUBLIC_STATUS)${NC}"
fi
echo ""

# 9. Résumé
echo "=========================================="
echo -e "${YELLOW}RÉSUMÉ${NC}"
echo "=========================================="
echo ""

if [ $FILE_COUNT -gt 0 ] && [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✓✓✓ Les fichiers statiques semblent correctement configurés${NC}"
    echo ""
    echo "Prochaines étapes :"
    echo "1. Tester dans le navigateur : https://doc-doc.douniah.com/admin/"
    echo "2. Ouvrir la console (F12) et vérifier qu'il n'y a plus d'erreurs"
else
    echo -e "${RED}✗✗✗ Problèmes détectés${NC}"
    echo ""
    echo "Actions recommandées :"
    echo "1. docker compose exec web python manage.py collectstatic --noinput --clear"
    echo "2. docker compose restart web"
    echo "3. Relancer ce script"
fi

echo ""
echo "=========================================="
