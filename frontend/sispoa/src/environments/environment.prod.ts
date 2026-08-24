// Configuración de producción. Se activa por `fileReplacements` en la
// configuración `production` de angular.json: durante el build reemplaza a
// `environment.ts`, que es la de desarrollo.
//
// El prefijo `/pip` no es decorativo. En el servidor de la municipalidad la
// plataforma se sirve como subruta de un nginx que ya atiende otro sistema en
// la misma dirección, así que el navegador tiene que pedir `/pip/api/v1/...`.
// nginx quita el prefijo antes de pasar la petición a Django, que sigue viendo
// sus rutas de siempre.
//
// Se escribe completo y explícito, en vez de depender del `<base href>`: hay 53
// usos de `apiUrl` en el código y no todos terminan en una petición que el
// navegador resuelva contra la base del documento.
export const environment = {
  production: true,
  apiUrl: '/pip/api/v1',
  apiUrlV2: '/pip/api/v2',
  tokenKey: 'pip_token',
  // Los tres de abajo no tienen ningún uso en el código hoy (0 referencias).
  // Se conservan para no romper la forma del objeto si alguien los consume más
  // adelante; si siguen sin usarse conviene retirarlos de las dos variantes.
  geoserverUrl: 'https://geoserver.sacaba.gob.bo/geoserver',
  minioPublicUrl: 'https://minio.sacaba.gob.bo',
  keycloakUrl: 'https://auth.sacaba.gob.bo',
};
