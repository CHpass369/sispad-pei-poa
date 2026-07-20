import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SidebarComponent } from './sidebar/sidebar.component';
import { HeaderComponent } from './header/header.component';
import { LayoutComponent } from './layout.component';
import { BreadcrumbsComponent } from '../core/components/breadcrumbs/breadcrumbs.component';

@NgModule({
  declarations: [LayoutComponent, SidebarComponent, HeaderComponent, BreadcrumbsComponent],
  imports: [CommonModule, RouterModule],
  exports: [LayoutComponent, SidebarComponent, HeaderComponent, BreadcrumbsComponent],
})
export class LayoutModule {}
