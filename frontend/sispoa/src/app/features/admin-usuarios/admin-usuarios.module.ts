import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import {
  ArrowRight,
  Badge,
  CircleAlert,
  CircleUserRound,
  ClipboardClock,
  CloudOff,
  Eye,
  KeyRound,
  LucideAngularModule,
  Pencil,
  Plus,
  Save,
  Search,
  SearchX,
  ShieldCheck,
  UserRoundCheck,
  UserRoundX,
  Trash2,
  X,
} from 'lucide-angular';
import { AdminUsuariosRoutingModule } from './admin-usuarios-routing.module';
import { UsuariosListaComponent } from './usuarios-lista.component';
import { AdminUsuariosService } from './admin-usuarios.service';
import { UsuarioEdicionDialogComponent } from './usuario-edicion-dialog.component';

@NgModule({
  declarations: [
    UsuariosListaComponent,
    UsuarioEdicionDialogComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatDividerModule,
    MatFormFieldModule,
    MatInputModule,
    MatPaginatorModule,
    MatProgressBarModule,
    MatSelectModule,
    MatTableModule,
    MatTabsModule,
    MatTooltipModule,
    LucideAngularModule.pick({
      Badge,
      ArrowRight,
      CircleAlert,
      CircleUserRound,
      ClipboardClock,
      CloudOff,
      Eye,
      KeyRound,
      Pencil,
      Plus,
      Save,
      Search,
      SearchX,
      ShieldCheck,
      UserRoundCheck,
      UserRoundX,
      Trash2,
      X,
    }),
    AdminUsuariosRoutingModule,
  ],
  providers: [AdminUsuariosService],
})
export class AdminUsuariosModule {}
