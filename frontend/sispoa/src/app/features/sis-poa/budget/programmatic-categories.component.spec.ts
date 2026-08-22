import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { ProgrammaticCategoriesComponent } from './programmatic-categories.component';
import { BudgetService, CategoriaProgramaticaTecho } from './budget.service';
import { GestionHabilitadaService } from '../../../core/services/gestion-habilitada.service';
import { gestionHabilitadaStub } from '../../../core/testing/gestion-habilitada.stub';

describe('ProgrammaticCategoriesComponent', () => {
  let component: ProgrammaticCategoriesComponent;
  let fixture: ComponentFixture<ProgrammaticCategoriesComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const cat: CategoriaProgramaticaTecho = {
    id: 1, gestion: 2027, codigo: '097', denominacion: 'Salud',
    nivel: 'PROGRAMA', nivel_display: 'Programa', parent: null,
    estado: 'ACTIVA', codigo_compuesto: '097',
  };

  beforeEach(async () => {
    serviceSpy = jasmine.createSpyObj('BudgetService', [
      'listar', 'listarCategorias', 'crearCategoria', 'duplicarCategoria',
    ]);
    serviceSpy.listar.and.returnValue(of({ count: 1, results: [{ id: '2027', anio: 2027 }] } as never));
    serviceSpy.listarCategorias.and.returnValue(of({ count: 1, results: [cat] } as never));
    serviceSpy.crearCategoria.and.returnValue(of(cat as never));
    serviceSpy.duplicarCategoria.and.returnValue(of({ detail: 'ok' } as never));

    await TestBed.configureTestingModule({
      declarations: [ProgrammaticCategoriesComponent],
      imports: [HttpClientTestingModule, FormsModule],
      providers: [
        { provide: BudgetService, useValue: serviceSpy },
        { provide: GestionHabilitadaService, useValue: gestionHabilitadaStub(2027) },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ProgrammaticCategoriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('carga las categorías de la gestión del candado, sin listar gestiones', () => {
    // El desplegable anterior hacía `Number(g.id)` sobre un UUID y mandaba
    // NaN; ahora el id sale del candado y viaja tal cual.
    expect(serviceSpy.listar).not.toHaveBeenCalled();
    expect(serviceSpy.listarCategorias).toHaveBeenCalledWith({
      gestion: 'gestion-habilitada-stub',
    });
    expect(component.categorias.length).toBe(1);
  });

  it('should create a category and reload', () => {
    component.gestionSeleccionada = 'gestion-habilitada-stub';
    component.nueva = { codigo: '098', denominacion: 'Educación', nivel: 'PROGRAMA', parent: null };
    component.crear();
    expect(serviceSpy.crearCategoria).toHaveBeenCalledWith({
      gestion: 'gestion-habilitada-stub', codigo: '098',
      denominacion: 'Educación', nivel: 'PROGRAMA', parent: null,
    });
    expect(component.mostrarFormulario).toBeFalse();
  });

  it('should show error when create fails', () => {
    serviceSpy.crearCategoria.and.returnValue(throwError(() => ({
      error: { error: { detail: 'No se puede crear' } },
    })));
    component.gestionSeleccionada = 'gestion-habilitada-stub';
    component.nueva = { codigo: '099', denominacion: 'X', nivel: 'PROGRAMA', parent: null };
    component.crear();
    expect(component.error).toContain('No se puede crear');
  });
});
