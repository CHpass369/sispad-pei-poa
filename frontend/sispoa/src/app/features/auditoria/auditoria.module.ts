import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { AuditoriaComponent } from './auditoria.component';

const routes: Routes = [
  { path: '', component: AuditoriaComponent },
];

@NgModule({
  declarations: [AuditoriaComponent],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class AuditoriaModule { }
