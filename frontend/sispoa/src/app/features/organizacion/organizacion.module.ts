import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { OrganizacionPageComponent } from './organizacion-page.component';
import { OrganizacionTreeComponent } from './organizacion-tree.component';
import { OrganizacionTreeNodeComponent } from './organizacion-tree-node.component';
import { OrganizacionDaComponent } from './organizacion-da.component';
import { OrganizacionUeComponent } from './organizacion-ue.component';

const routes: Routes = [
  { path: '', component: OrganizacionPageComponent },
];

@NgModule({
  declarations: [
    OrganizacionPageComponent,
    OrganizacionTreeComponent,
    OrganizacionTreeNodeComponent,
    OrganizacionDaComponent,
    OrganizacionUeComponent,
  ],
  imports: [
    CommonModule,
    FormsModule,
    RouterModule.forChild(routes),
  ],
})
export class OrganizacionModule { }
