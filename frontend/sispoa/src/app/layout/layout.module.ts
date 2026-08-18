import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LucideAngularModule, Home, Gauge, Bell, FileText, ClipboardList, Landmark, Compass, Network, LayoutGrid, ChartColumn, MapPin, Activity, CircleCheck, CalendarCheck, CalendarDays, ListTodo, Boxes, Banknote, Wallet, Coins, ChartBar, ListTree, ChartPie, Map, Download, RefreshCw, ScanSearch, PenLine, PencilRuler, Layers, Briefcase, HardHat, DraftingCompass, FolderOpen, FilePenLine, Handshake, Play, Eye, Users, Building2, CalendarRange, BookOpen, ScrollText, Folder, ChartSpline, MapPinned, Workflow, CircleAlert, BadgeCheck, ChevronLeft, ChevronRight, Menu, Search } from 'lucide-angular';
import { SidebarComponent } from './sidebar/sidebar.component';
import { HeaderComponent } from './header/header.component';
import { LayoutComponent } from './layout.component';
import { BreadcrumbsComponent } from '../core/components/breadcrumbs/breadcrumbs.component';

@NgModule({
  declarations: [LayoutComponent, SidebarComponent, HeaderComponent, BreadcrumbsComponent],
  imports: [
    CommonModule,
    RouterModule,
    LucideAngularModule.pick({
      Home, Gauge, Bell, FileText, ClipboardList, Landmark, Compass, Network, LayoutGrid,
      ChartColumn, MapPin, Activity, CircleCheck, CalendarCheck, CalendarDays, ListTodo, Boxes, Banknote,
      Wallet, Coins, ChartBar, ListTree, ChartPie, Map, Download, RefreshCw, ScanSearch,
      PenLine, PencilRuler, Layers, Briefcase, HardHat, DraftingCompass, FolderOpen,
      FilePenLine, Handshake, Play, Eye, Users, Building2, CalendarRange, BookOpen,
      ScrollText, Folder, ChartSpline, MapPinned, Workflow, CircleAlert, BadgeCheck,
      ChevronLeft, ChevronRight, Menu, Search,
    }),
  ],
  exports: [LayoutComponent, SidebarComponent, HeaderComponent, BreadcrumbsComponent],
})
export class LayoutModule {}
