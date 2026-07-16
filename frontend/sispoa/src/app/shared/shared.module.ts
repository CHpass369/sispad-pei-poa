import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { TablaGenericaComponent } from './components/tabla-generica/tabla-generica.component';

const EXPORTED_DECLARABLES = [TablaGenericaComponent];

@NgModule({
  declarations: [...EXPORTED_DECLARABLES],
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterModule],
  exports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    RouterModule,
    ...EXPORTED_DECLARABLES,
  ],
})
export class SharedModule {}
