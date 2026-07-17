import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DocumentosRoutingModule } from './documentos-routing.module';
import { DocumentosListaComponent } from './documentos-lista.component';
import { DocumentoSubirComponent } from './documento-subir.component';
import { DocumentoDetalleComponent } from './documento-detalle.component';
import { DocumentosService } from './documentos.service';

@NgModule({
  declarations: [
    DocumentosListaComponent,
    DocumentoSubirComponent,
    DocumentoDetalleComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    DocumentosRoutingModule,
  ],
  providers: [DocumentosService],
})
export class DocumentosModule {}
