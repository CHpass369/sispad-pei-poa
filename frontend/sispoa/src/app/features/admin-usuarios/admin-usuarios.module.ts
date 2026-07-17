import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AdminUsuariosRoutingModule } from './admin-usuarios-routing.module';
import { UsuariosListaComponent } from './usuarios-lista.component';
import { UsuarioFormComponent } from './usuario-form.component';
import { AdminUsuariosService } from './admin-usuarios.service';

@NgModule({
  declarations: [
    UsuariosListaComponent,
    UsuarioFormComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    AdminUsuariosRoutingModule,
  ],
  providers: [AdminUsuariosService],
})
export class AdminUsuariosModule {}
