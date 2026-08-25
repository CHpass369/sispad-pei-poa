import { CapabilityGuard } from '../../core/guards/capability.guard';
import {
  ADMIN_USUARIOS_CAPABILITIES,
  ADMIN_USUARIOS_ROUTES,
} from './admin-usuarios-routing.module';
import { UsuariosListaComponent } from './usuarios-lista.component';

describe('AdminUsuariosRoutingModule', () => {
  it('protects the single feature entry with any administrative capability', () => {
    expect(ADMIN_USUARIOS_ROUTES.length).toBe(1);
    expect(ADMIN_USUARIOS_ROUTES[0].path).toBe('');
    expect(ADMIN_USUARIOS_ROUTES[0].component).toBe(UsuariosListaComponent);
    expect(ADMIN_USUARIOS_ROUTES[0].canActivate).toContain(CapabilityGuard);
    expect(ADMIN_USUARIOS_ROUTES[0].data?.['capacidades']).toEqual(ADMIN_USUARIOS_CAPABILITIES);
    expect(ADMIN_USUARIOS_CAPABILITIES).toEqual([
      'accounts.usuario.view',
      'accounts.rol.view',
      'accounts.capacidad.view',
      'accounts.solicitud.view',
    ]);
  });
});
