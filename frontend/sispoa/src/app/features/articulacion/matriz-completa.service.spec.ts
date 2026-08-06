import { of } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { MatrizCompletaService } from './matriz-completa.service';

describe('MatrizCompletaService', () => {
  let service: MatrizCompletaService;
  let apiSpy: jasmine.SpyObj<ApiService>;

  beforeEach(() => {
    apiSpy = jasmine.createSpyObj<ApiService>('ApiService', ['get', 'patch']);
    apiSpy.get.and.returnValue(of({} as any));
    apiSpy.patch.and.returnValue(of({}));
    service = new MatrizCompletaService(apiSpy as unknown as ApiService);
  });

  it('requests the complete tree with management and expansion filters', () => {
    service.getArbol(2026, 'eje', 'parent-1').subscribe();

    expect(apiSpy.get).toHaveBeenCalledWith(
      '/planificacion/matriz-completa/',
      { gestion: 2026, nivel: 'eje', padre_id: 'parent-1' },
    );
  });

  it('requests PAD results for the selected management', () => {
    service.getResultadosPAD(2026).subscribe();

    expect(apiSpy.get).toHaveBeenCalledWith(
      '/articulacion/resultados-pad/',
      { gestion: 2026 },
    );
  });

  it('patches the PAD bridge with the selected PDESA node', () => {
    service.updateBridgePAD('pad-1', 'pdesa-action-1').subscribe();

    expect(apiSpy.patch).toHaveBeenCalledWith(
      '/articulacion/resultados-pad/pad-1/',
      { nodo_pdesa: 'pdesa-action-1' },
    );
  });

  it('opens the management-specific XLSX export URL', () => {
    spyOn(window, 'open').and.stub();

    service.exportXLSX(2026);

    expect(window.open).toHaveBeenCalledWith(
      '/api/v1/reportes/matriz_completa_xlsx/?gestion=2026',
      '_blank',
    );
  });
});
