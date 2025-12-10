# Fix Static Files Issues - doc-doc

## Problème Identifié

Les fichiers statiques retournent des erreurs 404 et 502 car Nginx Proxy Manager ne peut pas accéder au volume Docker `static_volume`.

**Erreurs observées :**
```
Refused to apply style from '<URL>' because its MIME type ('text/html') is not a supported stylesheet MIME type
Failed to load resource: the server responded with a status of 404 ()
Failed to load resource: the server responded with a status of 502 ()
```

## Solution Implémentée

**WhiteNoise** a été activé pour servir les fichiers statiques directement via Django.

### Changements Appliqués

#### 1. Middleware WhiteNoise Ajouté (settings.py:71)
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ← NOUVEAU
    "django.contrib.sessions.middleware.SessionMiddleware",
    ...
]
```

#### 2. Configuration WhiteNoise (settings.py:155-158)
```python
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0
```

#### 3. Storage Backend Mis à Jour (settings.py:194)
```python
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
```

## Déploiement

### Étape 1 : Rebuild des Containers

```bash
cd /opt/douniah/doc-doc
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Étape 2 : Collecter les Fichiers Statiques

```bash
docker compose exec web python manage.py collectstatic --noinput --clear
```

### Étape 3 : Vérifier les Fichiers Statiques

```bash
# Vérifier que les fichiers existent
docker compose exec web ls -la /app/staticfiles/admin/css/
docker compose exec web ls -la /app/staticfiles/admin/js/

# Devrait afficher :
# base.css, login.css, responsive.css, etc.
# theme.js, nav_sidebar.js, etc.
```

### Étape 4 : Tester l'Application

1. Ouvrir : https://doc-doc.douniah.com/admin/
2. Ouvrir la console du navigateur (F12)
3. Vérifier qu'il n'y a plus d'erreurs 404/502
4. Les styles CSS doivent être appliqués

## Configuration Nginx Proxy Manager

Avec WhiteNoise, **AUCUNE configuration spéciale** n'est nécessaire dans Nginx Proxy Manager.

### Configuration Actuelle (Devrait Être Suffisante)

**Dans Nginx Proxy Manager :**

1. **Proxy Host**
   - Domain: `doc-doc.douniah.com`
   - Scheme: `http`
   - Forward Hostname: `web` (ou l'IP du conteneur)
   - Forward Port: `8080`

2. **SSL** (onglet)
   - ✅ Force SSL
   - ✅ HTTP/2 Support
   - ✅ HSTS Enabled

3. **Advanced** (onglet) - **PAS BESOIN DE CONFIGURATION SPÉCIALE**

   Si vous aviez des directives `location /static/`, vous pouvez les supprimer.

   Configuration minimale recommandée :
   ```nginx
   # Proxy headers
   proxy_set_header Host $host;
   proxy_set_header X-Real-IP $remote_addr;
   proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
   proxy_set_header X-Forwarded-Proto $scheme;

   # Max upload size (correspond à Django)
   client_max_body_size 10M;
   ```

## Vérification

### Test 1 : Fichiers Statiques Servis par WhiteNoise

```bash
# Tester directement depuis le conteneur
docker compose exec web curl -I http://localhost:8080/static/admin/css/base.css

# Devrait retourner :
# HTTP/1.1 200 OK
# Content-Type: text/css
```

### Test 2 : Via Nginx Proxy Manager

```bash
# Depuis votre machine locale
curl -I https://doc-doc.douniah.com/static/admin/css/base.css

# Devrait retourner :
# HTTP/2 200
# Content-Type: text/css
# Cache-Control: max-age=31536000, public, immutable (en production)
```

### Test 3 : Interface Admin

1. Ouvrir : https://doc-doc.douniah.com/admin/
2. La page doit avoir les styles CSS appliqués
3. Console du navigateur : aucune erreur 404/502

## Avantages de WhiteNoise

✅ **Simple** - Aucune configuration Nginx complexe nécessaire
✅ **Compression** - Fichiers automatiquement compressés (gzip, brotli)
✅ **Cache** - Headers de cache optimaux automatiquement
✅ **CDN-Ready** - Génère des noms de fichiers avec hash pour cache-busting
✅ **Production-Ready** - Utilisé par des milliers de projets Django

## Performance

WhiteNoise ajoute une surcharge minimale :
- Les fichiers sont servis en mémoire
- Compression préalable (pas à la volée)
- Headers de cache agressifs

**Pour un trafic très élevé (>10000 req/s)**, vous pouvez ensuite ajouter un CDN devant.

## Troubleshooting

### Problème : Fichiers statiques toujours 404

**Solution 1 : Recollect staticfiles**
```bash
docker compose exec web python manage.py collectstatic --noinput --clear
docker compose restart web
```

**Solution 2 : Vérifier STATIC_ROOT**
```bash
docker compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.STATIC_ROOT)
# Devrait afficher : /app/staticfiles
```

**Solution 3 : Vérifier les permissions**
```bash
docker compose exec web ls -la /app/staticfiles
# Les fichiers doivent être lisibles
```

### Problème : Styles CSS ne s'appliquent pas

**Vider le cache du navigateur**
- Chrome : Ctrl+Shift+R
- Firefox : Ctrl+F5

**Vider le cache de Nginx Proxy Manager**
- Redémarrer Nginx Proxy Manager

### Problème : Erreurs de compression

Si vous voyez des erreurs avec `CompressedManifestStaticFilesStorage` :

**Fallback temporaire :**
```python
# Dans settings.py, ligne 194
STORAGES = {
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
```

## Commandes de Diagnostic

```bash
# 1. Vérifier que WhiteNoise est installé
docker compose exec web python -c "import whitenoise; print(whitenoise.__version__)"

# 2. Lister les fichiers statiques collectés
docker compose exec web find /app/staticfiles -type f | head -20

# 3. Tester un fichier statique spécifique
docker compose exec web cat /app/staticfiles/admin/css/base.css | head -10

# 4. Vérifier les logs Django
docker compose logs web | grep -i static

# 5. Vérifier la configuration
docker compose exec web python manage.py check --deploy
```

## Alternative : Nginx Standalone (Si WhiteNoise Ne Suffit Pas)

Si vous avez vraiment besoin de servir les statiques via Nginx (rare), voir `NGINX_STATIC_ALTERNATIVE.md`.

## Statut

- ✅ WhiteNoise middleware ajouté
- ✅ Configuration optimisée
- ✅ Compression activée
- ✅ Cache headers configurés
- ⏳ **À FAIRE : Rebuild et tester**

## Commandes de Déploiement Rapide

```bash
# Arrêter les containers
docker compose down

# Rebuild avec nouveau settings.py
docker compose build --no-cache web

# Démarrer
docker compose up -d

# Collecter les statiques
docker compose exec web python manage.py collectstatic --noinput --clear

# Vérifier
curl -I https://doc-doc.douniah.com/static/admin/css/base.css

# Tester dans le navigateur
open https://doc-doc.douniah.com/admin/
```

## Vérification Finale

Après le déploiement, vérifier :

1. [ ] Page admin charge avec styles CSS ✓
2. [ ] Console navigateur sans erreurs 404/502 ✓
3. [ ] JavaScript fonctionne (sidebar collapse, etc.) ✓
4. [ ] Fichiers compressés (.gz) créés dans staticfiles/ ✓
5. [ ] Headers de cache présents dans réponses HTTP ✓

---

**Date de fix :** 2025-12-10
**Méthode :** WhiteNoise middleware
**Impact :** Aucun changement dans Nginx Proxy Manager nécessaire
