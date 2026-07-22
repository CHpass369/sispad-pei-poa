import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { AuthService } from './core/services/auth.service';

@Component({
  standalone: false,
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `<router-outlet></router-outlet>`,
})
export class AppComponent implements OnInit {
  constructor(private auth: AuthService) {}
  ngOnInit(): void { this.auth.init(); }
}
