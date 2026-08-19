import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BudgetService } from './budget.service';

describe('BudgetService fiscal years', () => {
  let service: BudgetService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [BudgetService],
    });
    service = TestBed.inject(BudgetService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('sends fiscal-year creation as multipart when a document is present', () => {
    const document = new File(['fiscal authorization'], 'habilitacion.pdf', {
      type: 'application/pdf',
    });

    service.crear({ anio: 2027, documento_habilitacion: document }).subscribe();

    const request = http.expectOne(request => request.url.endsWith('/fiscal-years/'));
    expect(request.request.body).toEqual(jasmine.any(FormData));
    const body = request.request.body as FormData;
    expect(body.get('anio')).toBe('2027');
    expect(body.get('documento_habilitacion')).toBe(document);
    request.flush({});
  });

  it('keeps JSON creation when no document is present', () => {
    service.crear({ anio: 2027 }).subscribe();

    const request = http.expectOne(request => request.url.endsWith('/fiscal-years/'));
    expect(request.request.body).toEqual({ anio: 2027 });
    request.flush({});
  });
});
