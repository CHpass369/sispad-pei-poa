import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RecursosRoutingModule } from './recursos-routing.module';
import { RecursosListaComponent } from './recursos-lista.component';
import { RecursosFormComponent } from './recursos-form.component';
import { RecursosService } from './recursos.service';

@NgModule({
  declarations: [
    RecursosListaComponent,
    RecursosFormComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    RecursosRoutingModule,
  ],
  providers: [RecursosService],
})
export class RecursosModule {}
