import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { NormativaRoutingModule } from './normativa-routing.module';
import { NormativaListaComponent } from './normativa-lista.component';
import { NormativaDetalleComponent } from './normativa-detalle.component';
import { NormativaService } from './normativa.service';

@NgModule({
  declarations: [
    NormativaListaComponent,
    NormativaDetalleComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    NormativaRoutingModule,
  ],
  providers: [NormativaService],
})
export class NormativaModule {}
