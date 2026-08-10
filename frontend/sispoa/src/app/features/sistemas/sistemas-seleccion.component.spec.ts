import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { SistemasSeleccionComponent } from './sistemas-seleccion.component';
import { PermissionsService } from '../../core/services/permissions.service';

describe('SistemasSeleccionComponent', () => {
  let component: SistemasSeleccionComponent;
  let fixture: ComponentFixture<SistemasSeleccionComponent>;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;

  beforeEach(async () => {
    permissionsSpy = jasmine.createSpyObj('PermissionsService', ['hasAnyCapability']);

    await TestBed.configureTestingModule({
      declarations: [SistemasSeleccionComponent],
      imports: [RouterTestingModule],
      providers: [
        { provide: PermissionsService, useValue: permissionsSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SistemasSeleccionComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('shows the three systems when the user has all capabilities', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(true);
    fixture.detectChanges();

    expect(component.sistemas.length).toBe(3);
    const siglas = component.sistemas.map(s => s.sigla);
    expect(siglas).toEqual(['SIS-PE', 'SIS-POA', 'SIS-PRO']);
    expect(component.sinAcceso).toBeFalse();
  });

  it('filters systems by capability', () => {
    permissionsSpy.hasAnyCapability.and.callFake(
      (capacidades: string[]) => capacidades.includes('sis_pro.project.read'),
    );
    fixture.detectChanges();

    expect(component.sistemas.length).toBe(1);
    expect(component.sistemas[0].sigla).toBe('SIS-PRO');
  });

  it('flags no access when the user lacks all capabilities', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    fixture.detectChanges();

    expect(component.sistemas.length).toBe(0);
    expect(component.sinAcceso).toBeTrue();
  });
});
