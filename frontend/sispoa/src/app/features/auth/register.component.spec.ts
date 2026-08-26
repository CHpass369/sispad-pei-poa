import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';
import {
  MatAutocompleteModule,
  MatAutocompleteTrigger,
} from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { RouterModule } from '@angular/router';
import { Subject, of, throwError } from 'rxjs';
import {
  PublicOrganizationalUnit,
  RegistrationResponse,
} from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';
import { RegisterComponent } from './register.component';

describe('RegisterComponent', () => {
  let fixture: ComponentFixture<RegisterComponent>;
  let component: RegisterComponent;
  let auth: jasmine.SpyObj<AuthService>;

  const unit: PublicOrganizationalUnit = {
    id: 'b41aec54-c047-438c-b5df-a32d47f0ee65',
    codigo: 'DIR-PLA',
    nombre: 'Dirección de Planificación',
    sigla: 'DPLA',
    padre: null,
  };

  beforeEach(async () => {
    auth = jasmine.createSpyObj<AuthService>('AuthService', [
      'register',
      'listPublicOrganizationalUnits',
    ]);
    auth.listPublicOrganizationalUnits.and.returnValue(of([unit]));

    await TestBed.configureTestingModule({
      declarations: [RegisterComponent],
      imports: [
        NoopAnimationsModule,
        ReactiveFormsModule,
        MatAutocompleteModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatProgressSpinnerModule,
        RouterModule.forRoot([]),
      ],
      providers: [{ provide: AuthService, useValue: auth }],
    }).compileComponents();

    fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => localStorage.clear());

  function completeForm(): void {
    component.registerForm.setValue({
      first_name: 'Ana',
      last_name: 'Pérez',
      email: 'ana.perez@sacaba.gob.bo',
      cargo: 'Analista',
      unidad_organizacional_id: unit.id,
      password: 'Clave.Segura.2026',
      password_confirm: 'Clave.Segura.2026',
    });
    component.selectOrganizationalUnit(unit);
  }

  it('blocks submission when passwords do not match', () => {
    completeForm();
    component.registerForm.controls.password_confirm.setValue('Otra.Clave.2026');

    component.onSubmit();

    expect(component.registerForm.hasError('passwordMismatch')).toBeTrue();
    expect(auth.register).not.toHaveBeenCalled();
  });

  it('sends only public registration fields', () => {
    auth.register.and.returnValue(of({ detail: component.successMessage }));
    completeForm();

    component.onSubmit();

    const payload = auth.register.calls.mostRecent().args[0];
    expect(Object.keys(payload).sort()).toEqual([
      'cargo',
      'email',
      'first_name',
      'last_name',
      'password',
      'password_confirm',
      'unidad_organizacional_id',
    ]);
    expect('rol' in payload).toBeFalse();
    expect('sistema' in payload).toBeFalse();
    expect('permisos' in payload).toBeFalse();
    expect('scope' in payload).toBeFalse();
  });

  it('shows success without storing a token', () => {
    auth.register.and.returnValue(of({ detail: component.successMessage }));
    completeForm();

    component.onSubmit();

    expect(component.submittedSuccessfully).toBeTrue();
    expect(localStorage.length).toBe(0);
  });

  it('shows a clear API error and enables submission again', () => {
    auth.register.and.returnValue(throwError(() => ({
      message: 'Ya existe una cuenta registrada con este correo.',
    })));
    completeForm();

    component.onSubmit();

    expect(component.error).toBe('Ya existe una cuenta registrada con este correo.');
    expect(component.submitting).toBeFalse();
  });

  it('keeps submission disabled while the request is pending', () => {
    const response = new Subject<RegistrationResponse>();
    auth.register.and.returnValue(response);
    completeForm();

    component.onSubmit();
    fixture.detectChanges();

    const submit = fixture.nativeElement.querySelector('button[type="submit"]') as HTMLButtonElement;
    expect(component.submitting).toBeTrue();
    expect(submit.disabled).toBeTrue();
    response.complete();
  });

  it('requests organizational units after the search debounce', done => {
    auth.listPublicOrganizationalUnits.calls.reset();

    component.searchOrganizationalUnits('planificación');

    setTimeout(() => {
      expect(auth.listPublicOrganizationalUnits).toHaveBeenCalledWith('planificación');
      done();
    }, 350);
  });

  it('opens an opaque, feature-scoped organizational unit autocomplete', () => {
    component.organizationalUnits = [unit];
    fixture.detectChanges();

    const trigger = fixture.debugElement
      .query(By.directive(MatAutocompleteTrigger))
      .injector.get(MatAutocompleteTrigger);
    trigger.openPanel();
    fixture.detectChanges();

    const panel = document.querySelector<HTMLElement>(
      'div.register-unit-autocomplete-panel.mat-mdc-autocomplete-panel',
    );
    expect(panel).not.toBeNull();
    expect(getComputedStyle(panel!).backgroundColor).toBe('rgb(255, 255, 255)');
    expect(getComputedStyle(panel!).color).toBe('rgb(19, 32, 25)');
    expect(getComputedStyle(panel!).boxShadow).not.toBe('none');

    const overlayPane = panel!.closest<HTMLElement>('.cdk-overlay-pane');
    expect(overlayPane).not.toBeNull();
    expect(Number(getComputedStyle(overlayPane!).zIndex)).toBeGreaterThan(0);

    trigger.closePanel();
  });

  it('keeps input values, autocomplete text, and labels away from the field edge', () => {
    const registerForm = fixture.nativeElement.querySelector('.register-form') as HTMLElement;
    const inputs = Array.from(
      registerForm.querySelectorAll<HTMLInputElement>('input[matInput]'),
    );
    const labels = Array.from(
      registerForm.querySelectorAll<HTMLElement>('mat-label'),
    );

    expect(inputs.length).toBe(7);
    expect(labels.length).toBe(7);
    for (const element of [...inputs, ...labels]) {
      expect(parseFloat(getComputedStyle(element).paddingInlineStart)).toBe(4);
    }
  });
});
