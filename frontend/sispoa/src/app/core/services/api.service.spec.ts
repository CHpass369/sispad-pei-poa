import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../../environments/environment';

describe('ApiService', () => {
  let service: ApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ApiService],
    });
    service = TestBed.inject(ApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  describe('get', () => {
    it('should send GET request with correct URL', () => {
      const mockData = { id: 1, name: 'Test' };

      service.get('/test/').subscribe(data => {
        expect(data).toEqual(mockData);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/test/`);
      expect(req.request.method).toBe('GET');
      req.flush(mockData);
    });

    it('should append query params to URL', () => {
      service.get('/test/', { search: 'hello', page: 1 }).subscribe();

      const req = httpMock.expectOne(r =>
        r.url === `${environment.apiUrl}/test/` &&
        r.params.get('search') === 'hello' &&
        r.params.get('page') === '1',
      );
      expect(req.request.method).toBe('GET');
      req.flush([]);
    });

    it('should skip undefined and null params', () => {
      service.get('/test/', { search: 'test', page: undefined as any, size: null as any }).subscribe();

      const req = httpMock.expectOne(r =>
        r.url === `${environment.apiUrl}/test/` &&
        r.params.has('search') &&
        !r.params.has('page') &&
        !r.params.has('size'),
      );
      req.flush([]);
    });

    it('should handle boolean params', () => {
      service.get('/test/', { active: true }).subscribe();

      const req = httpMock.expectOne(r =>
        r.params.get('active') === 'true',
      );
      req.flush([]);
    });
  });

  describe('post', () => {
    it('should send POST request with body', () => {
      const sendData = { name: 'New Item' };
      const mockResponse = { id: 1, ...sendData };

      service.post('/test/', sendData).subscribe(data => {
        expect(data).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/test/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(sendData);
      req.flush(mockResponse);
    });

    it('should send POST request without body', () => {
      service.post('/test/').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/test/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toBeNull();
      req.flush({});
    });
  });

  describe('put', () => {
    it('should send PUT request with correct URL and body', () => {
      const sendData = { name: 'Updated' };
      const mockResponse = { id: 1, ...sendData };

      service.put('/test/1/', sendData).subscribe(data => {
        expect(data).toEqual(mockResponse);
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/test/1/`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(sendData);
      req.flush(mockResponse);
    });
  });

  describe('patch', () => {
    it('should send PATCH request with body', () => {
      const sendData = { name: 'Patched' };

      service.patch('/test/1/', sendData).subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/test/1/`);
      expect(req.request.method).toBe('PATCH');
      expect(req.request.body).toEqual(sendData);
      req.flush({});
    });
  });

  describe('delete', () => {
    it('should send DELETE request with correct URL', () => {
      service.delete('/test/1/').subscribe();

      const req = httpMock.expectOne(`${environment.apiUrl}/test/1/`);
      expect(req.request.method).toBe('DELETE');
      req.flush({});
    });
  });

  describe('error handling', () => {
    it('should propagate HTTP errors to subscriber', () => {
      service.get('/test/').subscribe({
        next: () => fail('Expected an error'),
        error: (error) => {
          expect(error.status).toBe(404);
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/test/`);
      req.flush('Not Found', { status: 404, statusText: 'Not Found' });
    });

    it('should propagate server errors', () => {
      service.post('/test/', {}).subscribe({
        next: () => fail('Expected an error'),
        error: (error) => {
          expect(error.status).toBe(500);
        },
      });

      const req = httpMock.expectOne(`${environment.apiUrl}/test/`);
      req.flush('Server Error', { status: 500, statusText: 'Internal Server Error' });
    });
  });
});
