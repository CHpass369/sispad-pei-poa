import { Component } from '@angular/core';
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { LoginComponent } from './login.component';

@Component({ standalone: false, template: '' })
class RegisterStubComponent {}

describe('LoginComponent', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let router: Router;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [LoginComponent, RegisterStubComponent],
      imports: [
        ReactiveFormsModule,
        RouterModule.forRoot([
          { path: 'auth/register', component: RegisterStubComponent },
        ]),
      ],
      providers: [{
        provide: AuthService,
        useValue: jasmine.createSpyObj<AuthService>('AuthService', ['login']),
      }],
    }).compileComponents();

    router = TestBed.inject(Router);
    fixture = TestBed.createComponent(LoginComponent);
    fixture.detectChanges();
  });

  it('shows the public registration link', () => {
    const text = fixture.nativeElement.textContent as string;
    const link = fixture.debugElement.query(By.css('a[href="/auth/register"]'));

    expect(text).toContain('¿No tienes una cuenta?');
    expect(link.nativeElement.textContent.trim()).toBe('Crear cuenta');
  });

  it('navigates to registration from the public link', fakeAsync(() => {
    const link = fixture.debugElement.query(By.css('a[href="/auth/register"]'));

    link.nativeElement.click();
    tick();

    expect(router.url).toBe('/auth/register');
  }));
});
