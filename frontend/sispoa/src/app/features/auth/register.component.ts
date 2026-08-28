import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormControl,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { Subject, catchError, debounceTime, distinctUntilChanged, of, switchMap, takeUntil } from 'rxjs';
import {
  PublicOrganizationalUnit,
  RegistrationRequest,
} from '../../core/models/usuario.model';
import { AuthService } from '../../core/services/auth.service';

const passwordsMatch: ValidatorFn = (control: AbstractControl): ValidationErrors | null => {
  const password = control.get('password')?.value;
  const confirmation = control.get('password_confirm')?.value;
  return password === confirmation ? null : { passwordMismatch: true };
};

@Component({
  standalone: false,
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrl: './register.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RegisterComponent implements OnInit, OnDestroy {
  readonly successMessage = 'Registro recibido. Un administrador revisará su solicitud.';
  readonly organizationalUnitSearch = new FormControl<PublicOrganizationalUnit | string>('', {
    nonNullable: true,
    validators: [Validators.required],
  });
  readonly registerForm = this.fb.nonNullable.group({
    first_name: ['', Validators.required],
    last_name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    cargo: ['', Validators.required],
    unidad_organizacional_id: ['', Validators.required],
    es_encargado_unidad: [false],
    password: ['', [Validators.required, Validators.minLength(8)]],
    password_confirm: ['', Validators.required],
  }, { validators: passwordsMatch });

  organizationalUnits: PublicOrganizationalUnit[] = [];
  loadingOrganizationalUnits = false;
  submitting = false;
  submittedSuccessfully = false;
  error = '';
  organizationalUnitsError = '';

  private readonly searchTerms = new Subject<string>();
  private readonly destroy$ = new Subject<void>();

  constructor(
    private readonly fb: FormBuilder,
    private readonly auth: AuthService,
    private readonly cdr: ChangeDetectorRef,
  ) {}

  ngOnInit(): void {
    this.searchTerms.pipe(
      debounceTime(250),
      distinctUntilChanged(),
      switchMap(search => {
        this.loadingOrganizationalUnits = true;
        this.organizationalUnitsError = '';
        this.cdr.markForCheck();
        return this.auth.listPublicOrganizationalUnits(search).pipe(
          catchError(() => {
            this.organizationalUnitsError = 'No se pudieron cargar las unidades organizacionales.';
            return of([] as PublicOrganizationalUnit[]);
          }),
        );
      }),
      takeUntil(this.destroy$),
    ).subscribe(units => {
      this.organizationalUnits = units;
      this.loadingOrganizationalUnits = false;
      this.cdr.markForCheck();
    });

    this.searchTerms.next('');
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  searchOrganizationalUnits(value: string): void {
    this.registerForm.controls.unidad_organizacional_id.setValue('');
    this.organizationalUnitSearch.setErrors(
      value.trim() ? { selectionRequired: true } : { required: true },
    );
    this.searchTerms.next(value);
  }

  selectOrganizationalUnit(unit: PublicOrganizationalUnit): void {
    this.registerForm.controls.unidad_organizacional_id.setValue(unit.id);
    this.organizationalUnitSearch.setErrors(null);
  }

  displayOrganizationalUnit(unit: PublicOrganizationalUnit | string): string {
    if (typeof unit === 'string') {
      return unit;
    }
    const label = unit.sigla || unit.codigo;
    return `${label} — ${unit.nombre}`;
  }

  onSubmit(): void {
    if (this.registerForm.invalid || !this.registerForm.controls.unidad_organizacional_id.value) {
      this.registerForm.markAllAsTouched();
      this.organizationalUnitSearch.markAsTouched();
      if (!this.registerForm.controls.unidad_organizacional_id.value) {
        this.organizationalUnitSearch.setErrors({ selectionRequired: true });
      }
      return;
    }

    this.submitting = true;
    this.error = '';
    const payload: RegistrationRequest = this.registerForm.getRawValue();

    this.auth.register(payload).subscribe({
      next: () => {
        this.submitting = false;
        this.submittedSuccessfully = true;
        this.cdr.markForCheck();
      },
      error: (error: unknown) => {
        this.submitting = false;
        this.error = this.errorMessage(error);
        this.cdr.markForCheck();
      },
    });
  }

  private errorMessage(error: unknown): string {
    if (
      typeof error === 'object'
      && error !== null
      && 'message' in error
      && typeof error.message === 'string'
    ) {
      return error.message;
    }
    return 'No se pudo enviar el registro. Revisa los datos e inténtalo nuevamente.';
  }
}
