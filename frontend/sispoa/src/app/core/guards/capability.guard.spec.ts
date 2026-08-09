import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { ActivatedRouteSnapshot } from '@angular/router';
import { CapabilityGuard } from './capability.guard';
import { PermissionsService } from '../services/permissions.service';

describe('CapabilityGuard', () => {
  let guard: CapabilityGuard;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    permissionsSpy = jasmine.createSpyObj('PermissionsService', ['hasAnyCapability']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);
    TestBed.configureTestingModule({
      providers: [
        CapabilityGuard,
        { provide: PermissionsService, useValue: permissionsSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
    guard = TestBed.inject(CapabilityGuard);
  });

  function snapshot(capacidades?: string[]): ActivatedRouteSnapshot {
    return { data: capacidades ? { capacidades } : {} } as ActivatedRouteSnapshot;
  }

  it('allows access without declared capabilities', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(true);
    expect(guard.canActivate(snapshot())).toBeTrue();
  });

  it('allows access when the user has the required capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(true);
    expect(
      guard.canActivate(snapshot(['sis_pe.instrumento.read'])),
    ).toBeTrue();
    expect(permissionsSpy.hasAnyCapability).toHaveBeenCalledWith([
      'sis_pe.instrumento.read',
    ]);
  });

  it('redirects to dashboard when the user lacks the capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    expect(
      guard.canActivate(snapshot(['sis_pe.pad.edit'])),
    ).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/dashboard']);
  });
});
