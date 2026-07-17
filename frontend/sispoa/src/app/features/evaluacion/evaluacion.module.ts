import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EvaluacionRoutingModule } from './evaluacion-routing.module';
import { EvaluacionListaComponent } from './evaluacion-lista.component';
import { EvaluacionFormComponent } from './evaluacion-form.component';
import { EvaluacionDetalleComponent } from './evaluacion-detalle.component';
import { EvaluacionService } from './evaluacion.service';

@NgModule({
  declarations: [
    EvaluacionListaComponent,
    EvaluacionFormComponent,
    EvaluacionDetalleComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    EvaluacionRoutingModule,
  ],
  providers: [EvaluacionService],
})
export class EvaluacionModule {}
