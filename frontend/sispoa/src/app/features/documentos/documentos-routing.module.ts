import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DocumentosListaComponent } from './documentos-lista.component';
import { DocumentoSubirComponent } from './documento-subir.component';
import { DocumentoDetalleComponent } from './documento-detalle.component';

const routes: Routes = [
  { path: '', component: DocumentosListaComponent },
  { path: 'subir', component: DocumentoSubirComponent },
  { path: ':id', component: DocumentoDetalleComponent },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class DocumentosRoutingModule {}
