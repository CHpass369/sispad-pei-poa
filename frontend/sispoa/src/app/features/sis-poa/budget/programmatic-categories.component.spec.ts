import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { ProgrammaticCategoriesComponent } from './programmatic-categories.component';
import { BudgetService, ProgrammaticCategory } from './budget.service';

describe('ProgrammaticCategoriesComponent', () => {
  let component: ProgrammaticCategoriesComponent;
  let fixture: ComponentFixture<ProgrammaticCategoriesComponent>;
  let serviceSpy: jasmine.SpyObj<BudgetService>;

  const cat: ProgrammaticCategory = {
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
      providers: [{ provide: BudgetService, useValue: serviceSpy }],
    }).compileComponents();

    fixture = TestBed.createComponent(ProgrammaticCategoriesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load fiscal years and categories on init', () => {
    expect(serviceSpy.listar).toHaveBeenCalled();
    expect(serviceSpy.listarCategorias).toHaveBeenCalledWith({ gestion: 2027 });
    expect(component.categorias.length).toBe(1);
  });

  it('should create a category and reload', () => {
    component.gestionSeleccionada = 2027;
    component.nueva = { codigo: '098', denominacion: 'Educación', nivel: 'PROGRAMA', parent: null };
    component.crear();
    expect(serviceSpy.crearCategoria).toHaveBeenCalledWith({
      gestion: 2027, codigo: '098', denominacion: 'Educación', nivel: 'PROGRAMA', parent: null,
    });
    expect(component.mostrarFormulario).toBeFalse();
  });

  it('should show error when create fails', () => {
    serviceSpy.crearCategoria.and.returnValue(throwError(() => ({
      error: { error: { detail: 'No se puede crear' } },
    })));
    component.gestionSeleccionada = 2027;
    component.nueva = { codigo: '099', denominacion: 'X', nivel: 'PROGRAMA', parent: null };
    component.crear();
    expect(component.error).toContain('No se puede crear');
  });
});
