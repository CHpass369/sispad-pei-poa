import { MAIN_ROUTES } from './main.module';

describe('MainModule routing', () => {
  const shell = MAIN_ROUTES.find(route => route.path === '' && route.children);
  const children = shell?.children ?? [];

  it('keeps SIS-PE and SIS-POA as lazy systems', () => {
    expect(children.find(route => route.path === 'sis-pe')?.loadChildren).toBeDefined();
    expect(children.find(route => route.path === 'sis-poa')?.loadChildren).toBeDefined();
  });

  it('does not register SIS-PRO or its legacy investment route', () => {
    expect(children.some(route => route.path === 'sis-pro')).toBeFalse();
    expect(children.some(route => route.path === 'inversion')).toBeFalse();
  });
});
