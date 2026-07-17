import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { UsuariosListaComponent } from './usuarios-lista.component';
import { AdminUsuariosService } from './admin-usuarios.service';
import { Router } from '@angular/router';

describe('UsuariosListaComponent', () => {
  let component: UsuariosListaComponent;
  let fixture: ComponentFixture<UsuariosListaComponent>;
  let adminServiceSpy: jasmine.SpyObj<AdminUsuariosService>;
  let routerSpy: jasmine.SpyObj<Router>;

  const mockUsuarios = [
    { id: 1, email: 'user1@test.com', first_name: 'User', last_name: 'One', is_active: true, rol_nombre: ['Admin'], date_joined: '2024-01-01' },
    { id: 2, email: 'user2@test.com', first_name: 'User', last_name: 'Two', is_active: false, rol_nombre: ['Técnico'], date_joined: '2024-02-01' },
  ];

  beforeEach(async () => {
    adminServiceSpy = jasmine.createSpyObj('AdminUsuariosService', ['listarUsuarios', 'eliminarUsuario']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    adminServiceSpy.listarUsuarios.and.returnValue(of(mockUsuarios as any));
    adminServiceSpy.eliminarUsuario.and.returnValue(of(void 0));

    await TestBed.configureTestingModule({
      declarations: [UsuariosListaComponent],
      imports: [HttpClientTestingModule, RouterTestingModule],
      providers: [
        { provide: AdminUsuariosService, useValue: adminServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UsuariosListaComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should load users on init', () => {
    fixture.detectChanges();

    expect(adminServiceSpy.listarUsuarios).toHaveBeenCalled();
    expect(component.usuarios.length).toBe(2);
    expect(component.cargando).toBeFalse();
  });

  it('should display empty message when no users found', () => {
    adminServiceSpy.listarUsuarios.and.returnValue(of([] as any));

    fixture.detectChanges();

    expect(component.usuarios.length).toBe(0);
    expect(component.cargando).toBeFalse();
  });

  it('should handle error when loading users', () => {
    adminServiceSpy.listarUsuarios.and.returnValue(throwError(() => new Error('Error')));

    fixture.detectChanges();

    expect(component.error).toBe('Error al cargar usuarios');
    expect(component.cargando).toBeFalse();
  });

  it('should filter users when searching', () => {
    fixture.detectChanges();
    expect(component.usuarios.length).toBe(2);

    component.busqueda = 'user1';
    adminServiceSpy.listarUsuarios.and.returnValue(of([mockUsuarios[0]] as any));

    component.cargar();

    expect(adminServiceSpy.listarUsuarios).toHaveBeenCalledWith({ search: 'user1' });
    expect(component.usuarios.length).toBe(1);
  });

  it('should navigate to create user page', () => {
    component.nuevo();

    expect(routerSpy.navigate).toHaveBeenCalledWith(['admin-usuarios/nuevo']);
  });

  it('should navigate to edit user page', () => {
    component.editar(mockUsuarios[0] as any);

    expect(routerSpy.navigate).toHaveBeenCalledWith(['admin-usuarios', 1]);
  });

  it('should not delete user when confirm is cancelled', () => {
    spyOn(window, 'confirm').and.returnValue(false);

    component.eliminar(mockUsuarios[0] as any);

    expect(adminServiceSpy.eliminarUsuario).not.toHaveBeenCalled();
  });

  it('should delete user and reload when confirm is accepted', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    adminServiceSpy.listarUsuarios.and.returnValue(of(mockUsuarios as any));

    component.eliminar(mockUsuarios[0] as any);

    expect(adminServiceSpy.eliminarUsuario).toHaveBeenCalledWith(1);
  });
});
