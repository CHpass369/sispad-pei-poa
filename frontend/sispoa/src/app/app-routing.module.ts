import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: '/dashboard', pathMatch: 'full' },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.module').then(m => m.AuthModule),
  },
  {
    path: '',
    loadChildren: () => import('./main/main.module').then(m => m.MainModule),
  },
  {
    path: 'portal',
    loadChildren: () => import('./features/portal-publico/portal-publico.module').then(m => m.PortalPublicoModule),
  },
  { path: '**', redirectTo: '/dashboard' },
];
