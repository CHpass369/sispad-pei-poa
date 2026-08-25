import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { CapabilityGuard } from '../../core/guards/capability.guard';
import { UsuariosListaComponent } from './usuarios-lista.component';

export const ADMIN_USUARIOS_CAPABILITIES = [
  'accounts.usuario.view',
  'accounts.rol.view',
  'accounts.capacidad.view',
  'accounts.solicitud.view',
];

export const ADMIN_USUARIOS_ROUTES: Routes = [
  {
    path: '',
    component: UsuariosListaComponent,
    canActivate: [CapabilityGuard],
    data: { capacidades: ADMIN_USUARIOS_CAPABILITIES },
  },
];

@NgModule({
  imports: [RouterModule.forChild(ADMIN_USUARIOS_ROUTES)],
  exports: [RouterModule],
})
export class AdminUsuariosRoutingModule {}
