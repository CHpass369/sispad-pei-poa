import { CommonModule } from '@angular/common';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { LucideAngularModule, Menu, Search } from 'lucide-angular';
import { of } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Usuario } from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import { GestionHabilitadaService } from '../../core/services/gestion-habilitada.service';
import { HeaderComponent } from './header.component';

describe('HeaderComponent', () => {
  let fixture: ComponentFixture<HeaderComponent>;
  let auth: AuthService;
  let httpMock: HttpTestingController;
  let router: Router;

  const user: Usuario = {
    id: '1',
    email: 'test@example.com',
    first_name: 'Test',
    last_name: 'User',
    cargo: 'Technician',
    telefono: '',
    roles: [],
    roles_detalle: [],
    activo: true,
    is_staff: false,
    is_superuser: false,
    debe_cambiar_password: false,
    last_login: null,
    date_joined: '2026-01-01',
  };

  beforeEach(async () => {
    localStorage.setItem(environment.tokenKey, JSON.stringify({
      access: 'access-token',
      refresh: 'refresh-token',
    }));

    await TestBed.configureTestingModule({
      declarations: [HeaderComponent],
      imports: [
        CommonModule,
        RouterTestingModule,
        LucideAngularModule.pick({ Menu, Search }),
      ],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        {
          provide: GestionHabilitadaService,
          useValue: {
            cargada$: of(true),
            gestion: () => null,
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(HeaderComponent);
    auth = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);

    auth.loadUser();
    httpMock.expectOne(`${environment.apiUrl}/auth/usuarios/me/`).flush(user);
    fixture.detectChanges();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.removeItem(environment.tokenKey);
  });

  it('logs out and returns to login without preserving authenticated history', () => {
    const navigation = spyOn(router, 'navigateByUrl').and.resolveTo(true);
    const logoutButton = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    ).find(button => button.textContent?.trim() === 'Salir');

    expect(logoutButton).toBeDefined();
    logoutButton!.click();

    expect(auth.getToken()).toBeNull();
    expect(navigation).toHaveBeenCalledOnceWith('/auth/login', { replaceUrl: true });
  });
});
