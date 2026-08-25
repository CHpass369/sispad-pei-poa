import { BreadcrumbsComponent } from './breadcrumbs.component';

describe('BreadcrumbsComponent', () => {
  it('labels the administrative feature as Usuarios y permisos', () => {
    const component = new BreadcrumbsComponent({} as never, {} as never);

    expect(component['getDefaultLabel']('admin-usuarios')).toBe('Usuarios y permisos');
  });
});
