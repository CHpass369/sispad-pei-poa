import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';
import { BudgetService, FiscalYear } from './budget.service';
import { PermissionsService } from '../../../core/services/permissions.service';
import { FiscalYearComponent } from './fiscal-year.component';

describe('FiscalYearComponent', () => {
  let component: FiscalYearComponent;
  let fixture: ComponentFixture<FiscalYearComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;

  const mockGestiones: FiscalYear[] = [
    {
      id: 'a1',
      anio: 2026,
      estado: 'HABILITADA',
      estado_display: 'Habilitada',
      descripcion: '',
      anio_inicio_plurianual: null,
      anio_fin_plurianual: null,
      fecha_apertura: '2026-01-05T12:00:00Z',
      fecha_cierre: null,
      activa: true,
      gestion_anterior: null,
    },
    {
      id: 'a2',
      anio: 2027,
      estado: 'preparacion',
      estado_display: 'Preparación',
      descripcion: '',
      anio_inicio_plurianual: null,
      anio_fin_plurianual: null,
      fecha_apertura: null,
      fecha_cierre: null,
      activa: true,
      gestion_anterior: 2026,
    },
  ];

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', ['listar', 'crear', 'habilitar', 'cerrar']);
    serviceSpy.listar.and.returnValue(of({ count: 2, results: mockGestiones }));
    serviceSpy.crear.and.returnValue(of(mockGestiones[0]));
    serviceSpy.habilitar.and.returnValue(of(mockGestiones[0]));
    serviceSpy.cerrar.and.returnValue(of(mockGestiones[0]));

    permissionsSpy = jasmine.createSpyObj('PermissionsService', ['hasAnyCapability']);
    permissionsSpy.hasAnyCapability.and.returnValue(true);

    await TestBed.configureTestingModule({
      declarations: [FiscalYearComponent],
      imports: [FormsModule, HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: BudgetService, useValue: serviceSpy },
        { provide: PermissionsService, useValue: permissionsSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(FiscalYearComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should list fiscal years on init', () => {
    fixture.detectChanges();
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(component.gestiones.length).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('should render rows with estado badge', () => {
    fixture.detectChanges();
    const filas = fixture.nativeElement.querySelectorAll('tbody tr');
    expect(filas.length).toBe(2);
    const badges = fixture.nativeElement.querySelectorAll('.badge');
    expect(badges.length).toBe(2);
    expect(badges[0].textContent).toContain('Habilitada');
    expect(badges[0].className).toContain('badge-success');
  });

  it('should call habilitar service on button click', () => {
    fixture.detectChanges();
    const botones = fixture.nativeElement.querySelectorAll('button');
    const habilitarBtn = Array.from(botones).find(
      (b: HTMLButtonElement) => b.textContent?.trim() === 'Habilitar',
    ) as HTMLButtonElement;
    expect(habilitarBtn).toBeTruthy();
    habilitarBtn.click();
    expect(serviceSpy.habilitar).toHaveBeenCalledWith('a2');
  });

  it('should show empty state when no fiscal years', () => {
    serviceSpy.listar.and.returnValue(of({ count: 0, results: [] }));
    fixture.detectChanges();
    const empty = fixture.nativeElement.querySelector('.empty');
    expect(empty).toBeTruthy();
    expect(empty.textContent).toContain('Sin gestiones');
  });

  it('should hide action buttons without budget.manage capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    fixture.detectChanges();
    expect(component.puedeGestionar).toBeFalse();
    expect(fixture.nativeElement.querySelectorAll('tbody tr button').length).toBe(0);
  });
});
