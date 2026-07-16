import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule, Routes } from '@angular/router';
import { ArticuladorComponent } from './articulador.component';

const routes: Routes = [
  { path: '', component: ArticuladorComponent },
];

@NgModule({
  declarations: [ArticuladorComponent],
  imports: [CommonModule, FormsModule, RouterModule.forChild(routes)],
})
export class PadModule { }
