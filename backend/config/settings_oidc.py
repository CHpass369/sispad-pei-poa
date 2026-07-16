"""
Configuración OIDC (Keycloak) para SISPAD-PEI-POA.

Se activa cuando OIDC_RP_CLIENT_ID está presente en el entorno.
Coexiste con SimpleJWT — ambos métodos de auth funcionan simultáneamente.

Importado desde settings.py al final del archivo.
Sigue el mismo patrón que settings_storage.py.
"""
import os

USE_OIDC = bool(os.environ.get('OIDC_RP_CLIENT_ID'))

if USE_OIDC:
    OIDC_RP_CLIENT_ID = os.environ['OIDC_RP_CLIENT_ID']
    OIDC_RP_CLIENT_SECRET = os.environ.get('OIDC_RP_CLIENT_SECRET', '')
    OIDC_OP_AUTHORITY = os.environ['OIDC_OP_AUTHORITY']

    # Construir URLs desde el authority
    OIDC_OP_TOKEN_ENDPOINT = f'{OIDC_OP_AUTHORITY}/protocol/openid-connect/token'
    OIDC_OP_USER_ENDPOINT = f'{OIDC_OP_AUTHORITY}/protocol/openid-connect/userinfo'
    OIDC_OP_JWKS_ENDPOINT = f'{OIDC_OP_AUTHORITY}/protocol/openid-connect/certs'

    OIDC_RP_SIGN_ALGO = 'RS256'
    OIDC_OP_LOGOUT_ENDPOINT = f'{OIDC_OP_AUTHORITY}/protocol/openid-connect/logout'
    LOGIN_REDIRECT_URL = '/'
    LOGOUT_REDIRECT_URL = '/'
