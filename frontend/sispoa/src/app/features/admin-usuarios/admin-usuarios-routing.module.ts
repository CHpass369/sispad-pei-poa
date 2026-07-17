import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { UsuariosListaComponent } from './usuarios-lista.component';
import { UsuarioFormComponent } from './usuario-form.component';

const routes: Routes = [
  { path: '', component: UsuariosListaComponent },
  { path: 'nuevo', component: UsuarioFormComponent },
  { path: ':id', component: UsuarioFormComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class AdminUsuariosRoutingModule {}
