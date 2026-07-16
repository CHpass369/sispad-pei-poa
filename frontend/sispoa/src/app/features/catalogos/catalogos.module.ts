import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { SharedModule } from '../../shared/shared.module';
import { CatalogoListaComponent } from './catalogo-lista.component';
import { CatalogosService } from './catalogos.service';

const routes: Routes = [
  { path: '', redirectTo: 'clasificadores-institucionales', pathMatch: 'full' },
  { path: ':tipo', component: CatalogoListaComponent },
];

@NgModule({
  declarations: [CatalogoListaComponent],
  imports: [SharedModule, RouterModule.forChild(routes)],
  providers: [CatalogosService],
})
export class CatalogosModule {}
