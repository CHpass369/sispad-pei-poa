import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, UrlTree } from '@angular/router';
import { BehaviorSubject, Observable } from 'rxjs';
import { CapabilityGuard } from './capability.guard';
import { CapabilitiesService } from '../services/capabilities.service';
import { PermissionsService } from '../services/permissions.service';

describe('CapabilityGuard', () => {
  let guard: CapabilityGuard;
  let permissionsSpy: jasmine.SpyObj<PermissionsService>;
  let routerSpy: jasmine.SpyObj<Router>;
  let capabilitiesSpy: Pick<CapabilitiesService, 'cargadas$'>;
  let dashboardUrl: UrlTree;

  beforeEach(() => {
    permissionsSpy = jasmine.createSpyObj('PermissionsService', ['hasAnyCapability']);
    routerSpy = jasmine.createSpyObj('Router', ['parseUrl']);
    dashboardUrl = {} as UrlTree;
    routerSpy.parseUrl.and.returnValue(dashboardUrl);
    capabilitiesSpy = { cargadas$: new BehaviorSubject<boolean>(false) };
    TestBed.configureTestingModule({
      providers: [
        CapabilityGuard,
        { provide: PermissionsService, useValue: permissionsSpy },
        { provide: CapabilitiesService, useValue: capabilitiesSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
    guard = TestBed.inject(CapabilityGuard);
  });

  function snapshot(capacidades?: string[]): ActivatedRouteSnapshot {
    return { data: capacidades ? { capacidades } : {} } as ActivatedRouteSnapshot;
  }

  it('allows access without declared capabilities', () => {
    expect(guard.canActivate(snapshot())).toBeTrue();
  });

  it('allows access when the user has the required capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(true);
    capabilitiesSpy.cargadas$.next(true);

    let result: boolean | UrlTree;
    (guard.canActivate(snapshot(['sis_pe.instrumento.read'])) as Observable<boolean | UrlTree>)
      .subscribe(value => result = value);

    expect(result).toBeTrue();
    expect(permissionsSpy.hasAnyCapability).toHaveBeenCalledWith([
      'sis_pe.instrumento.read',
    ]);
  });

  it('redirects to dashboard when the user lacks the capability', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    capabilitiesSpy.cargadas$.next(true);

    let result: boolean | UrlTree;
    (guard.canActivate(snapshot(['sis_pe.pad.edit'])) as Observable<boolean | UrlTree>)
      .subscribe(value => result = value);

    expect(result).toBe(dashboardUrl);
    expect(routerSpy.parseUrl).toHaveBeenCalledWith('/dashboard');
  });

  it('waits for pending capabilities before authorizing', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(true);
    let result: boolean | UrlTree;
    const decision = guard.canActivate(snapshot(['sis_poa.formulate'])) as Observable<boolean | UrlTree>;

    decision.subscribe(value => result = value);
    expect(permissionsSpy.hasAnyCapability).not.toHaveBeenCalled();

    capabilitiesSpy.cargadas$.next(true);

    expect(result).toBeTrue();
  });

  it('waits for pending capabilities before rejecting', () => {
    permissionsSpy.hasAnyCapability.and.returnValue(false);
    let result: boolean | UrlTree;
    const decision = guard.canActivate(snapshot(['sis_poa.formulate'])) as Observable<boolean | UrlTree>;

    decision.subscribe(value => result = value);
    expect(permissionsSpy.hasAnyCapability).not.toHaveBeenCalled();

    capabilitiesSpy.cargadas$.next(true);

    expect(result).toBe(dashboardUrl);
  });

  it('redirects safely when the capabilities signal fails', () => {
    let result: boolean | UrlTree;
    const decision = guard.canActivate(snapshot(['sis_poa.formulate'])) as Observable<boolean | UrlTree>;

    decision.subscribe(value => result = value);
    capabilitiesSpy.cargadas$.error(new Error('capabilities unavailable'));

    expect(result).toBe(dashboardUrl);
    expect(permissionsSpy.hasAnyCapability).not.toHaveBeenCalled();
  });
});
