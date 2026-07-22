import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { ApiService } from '../../core/services/api.service';

@Component({
  selector: 'app-articulador',
  standalone: false,
  template: `
    <div class="art-full">
      <div class="art-header">
        <h1>ARTICULADOR PAD — GUÍA OFICIAL</h1>
        <p>Construcción jerárquica PGDESA → PDESA → PDS → PAD → PEI → POA</p>
      </div>

      <!-- BARRA DE PROGRESO (10 pasos) -->
      <div class="progress-bar-horizontal">
        <div *ngFor="let nv of niveles; let i = index" class="progress-step"
             [class.completed]="paso > i" [class.active]="paso === i" (click)="irAPaso(i)">
          <div class="step-circle">{{ paso > i ? '✓' : i + 1 }}</div>
          <div class="step-label">{{ nv.sigla }}</div>
        </div>
      </div>

      <!-- PASO 0: PGDESA -->
      <div *ngIf="paso === 0" class="step-content card">
        <h3>Paso 1: Eje PGDESA — Impacto Nacional</h3>
        <p>Seleccione el Eje del Plan General de Desarrollo Económico y Social</p>
        <div class="select-cards">
          <div *ngFor="let eje of ejesPgdesa" class="select-card"
               [class.selected]="m.pgdesa?.codigo === eje.codigo" (click)="selPgdesa(eje)">
            <div class="card-cod">Eje {{ eje.codigo }}</div>
            <div class="card-nombre">{{ eje.nombre }}</div>
            <div class="card-desc">{{ eje.descripcion }}</div>
          </div>
        </div>
        <div class="field"><label>Objetivo de Impacto PGDESA</label>
          <textarea [(ngModel)]="m.pgdesa_objetivo" class="form-control" rows="2" placeholder="Copie el objetivo de impacto del PGDESA..."></textarea>
        </div>
        <div class="step-nav"><button class="btn btn-primary" [disabled]="!m.pgdesa" (click)="paso=1">Siguiente</button></div>
      </div>

      <!-- PASO 1: PDESA -->
      <div *ngIf="paso === 1" class="step-content card">
        <h3>Paso 2: Componente PDESA — Efecto Nacional</h3>
        <p>Eje: <strong>{{ m.pgdesa?.nombre }}</strong></p>
        <div class="select-cards">
          <div *ngFor="let c of m.pgdesa?.componentes || []" class="select-card"
               [class.selected]="m.pdesa?.codigo === c.codigo" (click)="selPdesa(c)">
            <div class="card-cod">{{ c.codigo }}</div>
            <div class="card-nombre">{{ c.nombre }}</div>
          </div>
        </div>
        <div class="field"><label>Objetivo de Efecto PDESA</label>
          <textarea [(ngModel)]="m.pdesa_objetivo" class="form-control" rows="2"></textarea>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=0">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!m.pdesa" (click)="paso=2">Siguiente</button>
        </div>
      </div>

      <!-- PASO 2: ACUERDOS INTERNACIONALES (ODS + NDC + NDT + 30/30) -->
      <div *ngIf="paso === 2" class="step-content card">
        <h3>Paso 3: Acuerdos Internacionales</h3>
        <p>Articule con ODS, NDC, NDT y Compromisos 30/30</p>
        <div class="form-3col">
          <div class="field"><label>ODS (Objetivo Desarrollo Sostenible)</label>
            <select [(ngModel)]="m.ods" class="form-control">
              <option value="">Seleccione ODS...</option>
              <option *ngFor="let o of odsList" [value]="o.cod+'. '+o.nombre">{{ o.cod }} — {{ o.nombre }}</option>
            </select>
          </div>
          <div class="field"><label>Meta NDC (Cambio Climático)</label>
            <input [(ngModel)]="m.ndc" class="form-control" placeholder="Ej: 6 — Alumbrado LED">
          </div>
          <div class="field"><label>Principio NDT (Degradación Tierras)</label>
            <input [(ngModel)]="m.ndt" class="form-control" placeholder="Ej: 4 — Agricultura climáticamente inteligente">
          </div>
        </div>
        <div class="field"><label>Compromisos 30/30</label>
          <textarea [(ngModel)]="m.comp3030" class="form-control" rows="2" placeholder="Describa el compromiso..."></textarea>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=1">← Anterior</button>
          <button class="btn btn-primary" (click)="paso=3">Siguiente → PDS</button>
        </div>
      </div>

      <!-- PASO 3: PDS (Sectorial) -->
      <div *ngIf="paso === 3" class="step-content card">
        <h3>Paso 4: Resultado Sectorial — PDS</h3>
        <div class="form-2col">
          <div class="field"><label>Código Sector</label>
            <select [(ngModel)]="m.sector_cod" class="form-control" (change)="onSectorChange()">
              <option value="">Seleccione...</option>
              <option *ngFor="let s of sectores" [value]="s.codigo">{{ s.codigo }} — {{ s.nombre }}</option>
            </select>
          </div>
          <div class="field"><label>Nombre del Sector</label><input [(ngModel)]="m.sector_nombre" class="form-control" readonly></div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Código Resultado PDS</label><input [(ngModel)]="m.pds_cod" class="form-control" placeholder="Ej: 5.1"></div>
          <div class="field"><label>Resultado Sectorial PDS</label>
            <textarea [(ngModel)]="m.pds_resultado" class="form-control" rows="2" placeholder="Describa el resultado sectorial..."></textarea>
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=2">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!m.sector_cod" (click)="paso=4">Siguiente → PAD</button>
        </div>
      </div>

      <!-- PASO 4: PAD - DATOS GENERALES (Código Geográfico + ETA) -->
      <div *ngIf="paso === 4" class="step-content card">
        <h3>Paso 5: Datos Generales del PAD</h3>
        <div class="form-2col">
          <div class="field"><label>Código Geográfico</label>
            <input [(ngModel)]="m.cod_geografico" class="form-control" placeholder="Ej: 1102">
            <small>Según clasificador presupuestario</small>
          </div>
          <div class="field"><label>Denominación ETA</label>
            <input [(ngModel)]="m.denominacion_eta" class="form-control" value="Gobierno Autónomo Municipal de Sacaba">
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=3">← Anterior</button>
          <button class="btn btn-primary" (click)="paso=5">Siguiente → Política</button>
        </div>
      </div>

      <!-- PASO 5: PAD - POLÍTICA -->
      <div *ngIf="paso === 5" class="step-content card">
        <h3>Paso 6: Política del PAD</h3>
        <div class="inline-actions"><button class="btn btn-accent btn-sm" (click)="crearPolitica()">+ Nueva Política</button></div>
        <div class="select-cards">
          <div *ngFor="let p of politicas" class="select-card"
               [class.selected]="m.politica?.id === p.id" (click)="selPolitica(p)">
            <div class="card-cod">{{ p.codigo }}</div>
            <div class="card-nombre">{{ p.nombre }}</div>
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=4">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!m.politica" (click)="paso=6">Siguiente</button>
        </div>
      </div>

      <!-- PASO 6: PAD - LINEAMIENTO -->
      <div *ngIf="paso === 6" class="step-content card">
        <h3>Paso 7: Lineamiento Estratégico</h3>
        <p>Política: <strong>{{ m.politica?.nombre }}</strong></p>
        <div class="inline-actions"><button class="btn btn-accent btn-sm" (click)="crearLineamiento()">+ Nuevo Lineamiento</button></div>
        <div class="select-cards">
          <div *ngFor="let l of lineamientosFiltrados" class="select-card"
               [class.selected]="m.lineamiento?.id === l.id" (click)="selLineamiento(l)">
            <div class="card-cod">{{ l.codigo }}</div>
            <div class="card-nombre">{{ l.nombre }}</div>
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=5">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!m.lineamiento" (click)="paso=7">Siguiente</button>
        </div>
      </div>

      <!-- PASO 7: PAD - RESULTADO TERRITORIAL (MATRIZ A COMPLETA) -->
      <div *ngIf="paso === 7" class="step-content card">
        <h3>Paso 8: Resultado Territorial — Matriz A</h3>
        <div class="form-2col">
          <div class="field"><label>Código Resultado PAD</label>
            <input [(ngModel)]="form.cod_res" class="form-control" placeholder="1102.1.1"></div>
          <div class="field"><label>Sector</label>
            <select [(ngModel)]="form.sector_id" class="form-control">
              <option *ngFor="let s of sectores" [value]="s.id">{{ s.codigo }} — {{ s.nombre }}</option>
            </select>
          </div>
        </div>
        <div class="field"><label>Resultado Territorial</label>
          <textarea [(ngModel)]="form.resultado" class="form-control" rows="2" placeholder="Cambio esperado en el territorio..."></textarea>
        </div>
        <h4>Producto Territorial</h4>
        <div class="form-2col">
          <div class="field"><label>Código Producto</label><input [(ngModel)]="form.prod_cod" class="form-control"></div>
          <div class="field"><label>Producto Territorial (bien/servicio)</label><input [(ngModel)]="form.prod_nom" class="form-control"></div>
        </div>
        <div class="form-2col">
          <div class="field"><label>Territorialización (lugar)</label><input [(ngModel)]="form.territorio" class="form-control" placeholder="Distrito, comunidad, OTB..."></div>
          <div class="field"><label>Responsable</label><input [(ngModel)]="form.responsable" class="form-control" placeholder="Entidad ejecutora"></div>
        </div>
        <h4>Indicador</h4>
        <div class="form-2col">
          <div class="field"><label>Indicador</label><input [(ngModel)]="form.indicador" class="form-control"></div>
          <div class="field"><label>Fórmula</label><input [(ngModel)]="form.formula" class="form-control" placeholder="Ej: (Ejecutado/Programado)*100"></div>
        </div>
        <div class="form-3col">
          <div class="field"><label>Línea Base</label><input [(ngModel)]="form.lb" type="number" class="form-control"></div>
          <div class="field"><label>Meta 2030</label><input [(ngModel)]="form.meta" type="number" class="form-control"></div>
          <div class="field"><label>Unidad Medida</label><input [(ngModel)]="form.unidad" class="form-control" placeholder="% / Nro / etc."></div>
        </div>
        <h4>Programación Quinquenal</h4>
        <div class="prog-grid">
          <div *ngFor="let a of anos" class="field">
            <label>{{ a }}</label>
            <input [(ngModel)]="form.prog_fis[a]" class="form-control" placeholder="Física">
            <input [(ngModel)]="form.prog_fin[a]" class="form-control" placeholder="Bs">
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=6">← Anterior</button>
          <button class="btn btn-primary" [disabled]="!form.cod_res" (click)="guardarResultado()">Guardar y continuar</button>
        </div>
        <div *ngIf="msg" class="msg-box" [class.error]="msgClass==='error'" [class.exito]="msgClass==='exito'">{{ msg }}</div>
      </div>

      <!-- PASO 8: PEI -->
      <div *ngIf="paso === 8" class="step-content card">
        <h3>Paso 9: Articular con el PEI</h3>
        <div class="bifurcacion">
          <div class="bif-card">
            <h4>Usar AMP existente</h4>
            <select [(ngModel)]="ampSel" class="form-control" size="3" *ngIf="amps.length>0">
              <option *ngFor="let a of amps" [value]="a.id">{{ a.codigo }}</option>
            </select>
            <button class="btn btn-primary btn-sm" (click)="vincularAmp(ampSel)">Vincular</button>
          </div>
          <div class="bif-card" (click)="crearAmp()">
            <h4>+ Crear nueva AMP</h4>
            <p>Nueva Acción de Mediano Plazo</p>
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=7">← Anterior</button>
          <button class="btn btn-primary" (click)="paso=9">Siguiente → POA</button>
        </div>
      </div>

      <!-- PASO 9: POA -->
      <div *ngIf="paso === 9" class="step-content card">
        <h3>Paso 10: Articular con el POA</h3>
        <div class="bifurcacion">
          <div class="bif-card">
            <h4>Vincular ACP existente</h4>
            <select [(ngModel)]="acpSel" class="form-control" size="3" *ngIf="acps.length>0">
              <option *ngFor="let a of acps" [value]="a.id">{{ a.codigo }} ({{ a.gestion }})</option>
            </select>
            <button class="btn btn-primary btn-sm" (click)="vincularAcp(acpSel)">Vincular</button>
          </div>
          <div class="bif-card" (click)="crearAcp()">
            <h4>+ Crear nueva ACP</h4>
            <p>Nueva Acción de Corto Plazo</p>
          </div>
        </div>
        <div class="step-nav">
          <button class="btn btn-outline" (click)="paso=8">← Anterior</button>
          <button class="btn btn-success" (click)="finalizar()">✓ Finalizar Articulación</button>
        </div>
      </div>

      <!-- VISTA PREVIA: MATRIZ A (formato oficial) -->
      <div class="matriz-vista card" *ngIf="paso >= 0">
        <div class="matriz-tabs">
          <button class="btn" [class.btn-primary]="vistaMatriz==='a'" (click)="vistaMatriz='a'">MATRIZ A</button>
          <button class="btn" [class.btn-primary]="vistaMatriz==='b'" (click)="vistaMatriz='b'">MATRIZ B</button>
        </div>

        <!-- MATRIZ A -->
        <div *ngIf="vistaMatriz==='a'" class="matriz-scroll">
          <h3>MATRIZ A — Planificación PAD</h3>
          <table class="mz">
            <thead>
              <tr>
                <th>SECTOR</th><th>CÓD. GEOGR.</th><th>POLÍTICA</th><th>CÓD. LIN.</th><th>LINEAMIENTO ESTRATÉGICO</th>
                <th>CÓD. RES. TERR.</th><th>RESULTADO TERRITORIAL</th><th>CÓD. PROD.</th><th>PRODUCTO</th>
                <th>TERRITORIALIZACIÓN</th><th>RESPONSABLE</th><th>INDICADOR</th><th>FÓRMULA</th>
                <th>L. BASE</th><th>META 2030</th>
                <th *ngFor="let a of anos">PROG. FÍS. {{a}}</th>
                <th *ngFor="let a of anos">PROG. FIN. {{a}}</th>
                <th>FINANCIAMIENTO</th>
                <th>PRESUP. TOTAL</th>
              </tr>
            </thead>
            <tbody>
              <!-- Fila Resultado -->
              <tr class="fila-resultado" *ngIf="form.resultado">
                <td>{{ sectorNombre }}</td><td>{{ m.cod_geografico }}</td>
                <td>{{ m.politica?.nombre||'-' }}</td><td>{{ m.lineamiento?.codigo||'-' }}</td>
                <td>{{ m.lineamiento?.nombre||'-' }}</td>
                <td><strong>{{ form.cod_res||'-' }}</strong></td>
                <td>{{ form.resultado }}</td>
                <td>—</td><td>—</td><td>—</td><td>{{ form.responsable||'-' }}</td>
                <td>{{ form.indicador||'-' }}</td><td>{{ form.formula||'-' }}</td>
                <td>{{ form.lb }}</td><td>{{ form.meta }}</td>
                <td *ngFor="let a of anos">{{ form.prog_fis[a]||'-' }}</td>
                <td *ngFor="let a of anos">{{ form.prog_fin[a]||'-' }}</td>
                <td>{{ tieneFinanciamiento() }}</td>
                <td>{{ presupuestoTotal() }}</td>
              </tr>
              <!-- Fila Producto -->
              <tr class="fila-producto" *ngIf="form.prod_nom">
                <td>{{ sectorNombre }}</td><td>{{ m.cod_geografico }}</td>
                <td>{{ m.politica?.nombre||'-' }}</td><td>{{ m.lineamiento?.codigo||'-' }}</td>
                <td>{{ m.lineamiento?.nombre||'-' }}</td>
                <td>—</td><td>—</td>
                <td><strong>{{ form.prod_cod||'-' }}</strong></td>
                <td>{{ form.prod_nom }}</td>
                <td>{{ form.territorio||'-' }}</td><td>{{ form.responsable||'-' }}</td>
                <td>{{ form.indicador||'-' }}</td><td>{{ form.formula||'-' }}</td>
                <td>—</td><td>{{ form.meta||'-' }}</td>
                <td *ngFor="let a of anos">{{ form.prog_fis[a]||'-' }}</td>
                <td *ngFor="let a of anos">{{ form.prog_fin[a]||'-' }}</td>
                <td>{{ tieneFinanciamiento() }}</td>
                <td>{{ presupuestoTotal() }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- MATRIZ B -->
        <div *ngIf="vistaMatriz==='b'" class="matriz-scroll">
          <h3>MATRIZ B — Articulación SIPEB</h3>
          <table class="mz">
            <thead>
              <tr>
                <th colspan="4">PLANIFICACIÓN NACIONAL</th>
                <th colspan="4">ACUERDOS INTERNACIONALES</th>
                <th colspan="4">PLANIFICACIÓN SECTORIAL</th>
                <th colspan="14">PLANIFICACIÓN TERRITORIAL</th>
              </tr>
              <tr>
                <th>CÓD. EJE PGDESA</th><th>OBJETIVO IMPACTO</th><th>CÓD. COMP. PDESA</th><th>OBJETIVO EFECTO</th>
                <th>ODS</th><th>NDC</th><th>NDT</th><th>30/30</th>
                <th>CÓD. SECTOR</th><th>SECTOR</th><th>CÓD. RES. PDS</th><th>RESULTADO PDS</th>
                <th>CÓD. GEOGR.</th><th>ETA</th><th>CÓD. LIN.</th><th>LINEAMIENTO</th>
                <th>CÓD. RES. TERR.</th><th>RESULTADO TERRITORIAL</th>
                <th>INDICADOR</th><th>FÓRMULA</th><th>L. BASE</th><th>META 2030</th>
                <th *ngFor="let a of anos">PROG. {{a}}</th>
                <th>PRESUP. REF.</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngIf="m.pgdesa || form.resultado">
                <td>{{ m.pgdesa?.codigo||'-' }}</td>
                <td>{{ m.pgdesa_objetivo||m.pgdesa?.nombre||'-' }}</td>
                <td>{{ m.pdesa?.codigo||'-' }}</td>
                <td>{{ m.pdesa_objetivo||m.pdesa?.nombre||'-' }}</td>
                <td>{{ m.ods||'-' }}</td>
                <td>{{ m.ndc||'-' }}</td>
                <td>{{ m.ndt||'-' }}</td>
                <td>{{ m.comp3030||'-' }}</td>
                <td>{{ m.sector_cod||'-' }}</td>
                <td>{{ m.sector_nombre||'-' }}</td>
                <td>{{ m.pds_cod||'-' }}</td>
                <td>{{ m.pds_resultado||'-' }}</td>
                <td>{{ m.cod_geografico||'-' }}</td>
                <td>{{ m.denominacion_eta||'-' }}</td>
                <td>{{ m.lineamiento?.codigo||'-' }}</td>
                <td>{{ m.lineamiento?.nombre||'-' }}</td>
                <td><strong>{{ form.cod_res||'-' }}</strong></td>
                <td>{{ form.resultado||'-' }}</td>
                <td>{{ form.indicador||'-' }}</td>
                <td>{{ form.formula||'-' }}</td>
                <td>{{ form.lb||'-' }}</td>
                <td>{{ form.meta||'-' }}</td>
                <td *ngFor="let a of anos">{{ form.prog_fis[a]||'-' }}</td>
                <td>{{ presupuestoReferencial() }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .art-full { max-width: 1200px; margin:0 auto; padding-bottom:2rem; }
    .art-header h1 { font-size:1.35rem; color:var(--primary); }
    .art-header p { color:var(--text-secondary); font-size:0.8125rem; margin-bottom:1rem; }

    .progress-bar-horizontal { display:flex; gap:0; margin-bottom:1.5rem; overflow-x:auto; }
    .progress-step { flex:1; text-align:center; padding:0.5rem 0.25rem; cursor:pointer; position:relative; min-width:60px; }
    .progress-step::after { content:''; position:absolute; top:50%; right:-50%; width:100%; height:2px; background:var(--border); z-index:0; }
    .progress-step:last-child::after { display:none; }
    .step-circle { width:28px; height:28px; border-radius:50%; margin:0 auto 0.25rem; display:flex; align-items:center; justify-content:center; font-weight:700; font-size:0.75rem; background:var(--border); color:var(--text-secondary); position:relative; z-index:1; }
    .progress-step.active .step-circle { background:var(--primary); color:white; }
    .progress-step.completed .step-circle { background:var(--success); color:white; }
    .step-label { font-weight:700; font-size:0.6875rem; }

    .step-content { padding:1.5rem; min-height:300px; }
    .step-content h3 { font-size:1.1rem; margin-bottom:0.5rem; }
    .step-content h4 { font-size:0.9rem; margin:1rem 0 0.5rem; color:var(--text-secondary); }
    .step-content p { color:var(--text-secondary); margin-bottom:0.75rem; font-size:0.8125rem; }
    .select-cards { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:0.5rem; margin-bottom:0.75rem; }
    .select-card { padding:0.75rem; border:2px solid var(--border); border-radius:6px; cursor:pointer; }
    .select-card:hover { border-color:var(--primary); background:#F0F7F3; }
    .select-card.selected { border-color:var(--primary); background:#E8F5E9; }
    .card-cod { font-weight:800; font-size:0.7rem; color:var(--primary); }
    .card-nombre { font-size:0.8125rem; font-weight:600; }
    .card-desc { font-size:0.7rem; color:var(--text-secondary); margin-top:0.25rem; }
    .form-2col,.form-3col { display:grid; gap:0.75rem; margin-bottom:0.5rem; }
    .form-2col { grid-template-columns:1fr 1fr; }
    .form-3col { grid-template-columns:1fr 1fr 1fr; }
    .field { margin-bottom:0.5rem; }
    .field label { display:block; font-size:0.6875rem; font-weight:500; color:var(--text-secondary); margin-bottom:0.2rem; }
    .field small { font-size:0.625rem; color:var(--text-secondary); }
    .inline-actions { margin-bottom:0.5rem; }
    .step-nav { display:flex; justify-content:space-between; margin-top:1.25rem; padding-top:0.75rem; border-top:1px solid var(--border); }
    .bifurcacion { display:grid; grid-template-columns:1fr 1fr; gap:1rem; }
    .bif-card { padding:1rem; border:2px dashed var(--border); border-radius:8px; cursor:pointer; }
    .bif-card:hover { border-color:var(--primary); background:#F0F7F3; }
    .bif-card h4 { font-size:0.875rem; }
    .bif-card p { font-size:0.75rem; }
    .bif-card select { font-size:0.75rem; margin-bottom:0.5rem; }
    .prog-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:0.5rem; }
    .prog-grid input { font-size:0.75rem; padding:0.25rem 0.375rem; margin-bottom:0.25rem; }

    .matriz-vista { margin-top:1.5rem; padding:1.25rem; border:2px solid var(--primary); }
    .matriz-vista h3 { font-size:0.9rem; margin-bottom:0.75rem; color:var(--primary); }
    .matriz-tabs { display:flex; gap:0.5rem; margin-bottom:1rem; }
    .matriz-tabs .btn { font-size:0.75rem; padding:0.375rem 0.75rem; }
    .matriz-scroll { overflow-x:auto; }
    .mz { border-collapse:collapse; font-size:0.65rem; width:100%; }
    .mz th { background:var(--primary); color:white; padding:0.3rem 0.4rem; text-transform:uppercase; white-space:nowrap; border:1px solid rgba(255,255,255,0.2); font-weight:600; }
    .mz td { padding:0.25rem 0.4rem; border:1px solid var(--border); vertical-align:top; }
    .mz .fila-resultado td { background:#E8F5E9; font-weight:500; }
    .mz .fila-producto td { background:#fff; }
    .mz tr:hover td { background:#F0F7F3; }
    .msg-box { margin-top:0.75rem; padding:0.5rem 0.75rem; border-radius:6px; font-size:0.8125rem; }
    .msg-box.error { background:#FFEBEE; color:var(--warn); }
    .msg-box.exito { background:#E8F5E9; color:var(--success); }

    @media (max-width:768px) { .form-2col,.form-3col,.prog-grid { grid-template-columns:1fr; } }
  `]
})
export class ArticuladorComponent implements OnInit {
  paso = 0;
  anos = ['2026','2027','2028','2029','2030'];

  m: any = {
    pgdesa: null, pgdesa_objetivo: '',
    pdesa: null, pdesa_objetivo: '',
    ods: '', ndc: '', ndt: '', comp3030: '',
    sector_cod: '', sector_nombre: '', pds_cod: '', pds_resultado: '',
    cod_geografico: '1102', denominacion_eta: 'Gobierno Autónomo Municipal de Sacaba',
    politica: null, lineamiento: null,
  };

  form: any = {
    cod_res: '', resultado: '', sector_id: '',
    prod_cod: '', prod_nom: '', territorio: '', responsable: '',
    indicador: '', formula: '', lb: 0, meta: 0, unidad: '',
    prog_fis: {} as any, prog_fin: {} as any,
  };

  ultimoResultado: any = null;
  ampVinculadas: any[] = [];
  acpVinculadas: any[] = [];
  ampSel = ''; acpSel = '';
  vistaMatriz = 'a';

  get sectorNombre(): string {
    const s = this.sectores.find((x: any) => x.id === this.form.sector_id);
    return s?.nombre || this.m.sector_nombre || '-';
  }

  msg = '';
  msgClass = '';
  tieneFinanciamiento(): string { return this.form.cuenta_con_financiamiento || (this.form.prog_fin?.['2026'] ? 'SÍ' : 'NO'); }
  presupuestoTotal(): string {
    const total = Object.values(this.form.prog_fin || {}).reduce((s: any, v: any) => s + (Number(v) || 0), 0);
    return total ? total.toLocaleString() : '-';
  }
  presupuestoReferencial(): string { return this.presupuestoTotal(); }

  niveles = [
    {sigla:'PGDESA'},{sigla:'PDESA'},{sigla:'ODS/NDC'},{sigla:'PDS'},
    {sigla:'PAD'},{sigla:'Política'},{sigla:'Lineam.'},{sigla:'Resultado'},
    {sigla:'PEI'},{sigla:'POA'}
  ];

  politicas: any[] = [];
  lineamientos: any[] = [];
  sectores: any[] = [];
  amps: any[] = [];
  acps: any[] = [];

  ejesPgdesa = [
    {codigo:'1', nombre:'Bolivia Libre y Soberana', descripcion:'Defensa de la soberanía y autodeterminación', componentes:[
      {codigo:'1.1', nombre:'Gestión soberana de recursos'},{codigo:'1.2', nombre:'Relaciones internacionales'}]},
    {codigo:'2', nombre:'Bolivia Social y Comunitaria', descripcion:'Erradicación de la pobreza y desigualdades', componentes:[
      {codigo:'2.1', nombre:'Desarrollo social'},{codigo:'2.2', nombre:'Protección social'}]},
    {codigo:'3', nombre:'Bolivia Salud, Educación y Deporte', descripcion:'Acceso universal a servicios sociales', componentes:[
      {codigo:'3.1', nombre:'Salud universal'},{codigo:'3.2', nombre:'Educación inclusiva'},{codigo:'3.3', nombre:'Deporte'}]},
    {codigo:'4', nombre:'Bolivia Productiva', descripcion:'Transformación productiva con soberanía', componentes:[
      {codigo:'4.1', nombre:'Desarrollo agropecuario'},{codigo:'4.2', nombre:'Industrialización'}]},
    {codigo:'5', nombre:'Bolivia Verde y Sostenible', descripcion:'Gestión ambiental y cambio climático', componentes:[
      {codigo:'5.1', nombre:'Gestión ambiental'},{codigo:'5.2', nombre:'Recursos hídricos'}]},
    {codigo:'6', nombre:'Bolivia Democrática', descripcion:'Descentralización y autonomías', componentes:[
      {codigo:'6.1', nombre:'Fortalecimiento autonómico'}]},
    {codigo:'7', nombre:'Bolivia Digital', descripcion:'Tecnología e innovación', componentes:[
      {codigo:'7.1', nombre:'Gobierno digital'}]},
  ];

  odsList = [
    {cod:'1',nombre:'Fin de la pobreza'},{cod:'2',nombre:'Hambre cero'},{cod:'3',nombre:'Salud y bienestar'},
    {cod:'4',nombre:'Educación de calidad'},{cod:'5',nombre:'Igualdad de género'},{cod:'6',nombre:'Agua limpia y saneamiento'},
    {cod:'7',nombre:'Energía asequible'},{cod:'8',nombre:'Trabajo decente'},{cod:'9',nombre:'Industria e innovación'},
    {cod:'10',nombre:'Reducción de desigualdades'},{cod:'11',nombre:'Ciudades sostenibles'},{cod:'12',nombre:'Producción responsable'},
    {cod:'13',nombre:'Acción climática'},{cod:'14',nombre:'Vida submarina'},{cod:'15',nombre:'Vida terrestre'},
    {cod:'16',nombre:'Paz y justicia'},{cod:'17',nombre:'Alianzas globales'},
  ];

  constructor(private api: ApiService, private cdr: ChangeDetectorRef) {}

  ngOnInit(): void {
    this.cargarSectores(); this.cargarPoliticas(); this.cargarLineamientos();
    this.cargarAmps(); this.cargarAcps();
  }

  get lineamientosFiltrados(): any[] {
    return this.lineamientos.filter((l:any)=>l.politica===this.m.politica?.id);
  }

  irAPaso(p:number): void { if(p<=this.paso) this.paso=p; }
  selPgdesa(e:any): void { this.m.pgdesa=e; this.m.pdesa=null; }
  selPdesa(c:any): void { this.m.pdesa=c; }
  onSectorChange(): void {
    const s=this.sectores.find((x:any)=>x.codigo===this.m.sector_cod);
    if(s){this.m.sector_nombre=s.nombre; this.m.pds_cod=s.codigo+'.1';}
  }
  selPolitica(p:any): void { this.m.politica=p; this.m.lineamiento=null; this.cargarLineamientos(); }
  selLineamiento(l:any): void { this.m.lineamiento=l; }

  crearPolitica(): void {
    const c=prompt('Código de la política:'); if(!c)return;
    const n=prompt('Nombre:'); if(!n)return;
    this.api.post('/pad/politicas-pad/', {codigo:c,nombre:n,gestion:2026}).subscribe({next:()=>this.cargarPoliticas()});
  }

  crearLineamiento(): void {
    if(!this.m.politica)return;
    const c=prompt('Código del lineamiento:'); if(!c)return;
    const n=prompt('Nombre:'); if(!n)return;
    this.api.post('/pad/lineamientos/', {codigo:c,nombre:n,politica:this.m.politica.id,gestion:2026}).subscribe({next:()=>this.cargarLineamientos()});
  }

  _num(val: any): any { const n = Number(val); return isNaN(n) ? val : n; }

  guardarResultado(): void {
    if(!this.m.lineamiento?.id) { this.msg='Seleccione un lineamiento primero'; this.msgClass='error'; return; }
    if(!this.form.cod_res) { this.msg='Ingrese el código del resultado'; this.msgClass='error'; return; }
    this.msg='Guardando...'; this.msgClass='';
    const body: any = {
      codigo: this.form.cod_res, nombre: this.form.resultado || 'Resultado ' + this.form.cod_res,
      lineamiento: this.m.lineamiento.id, gestion: 2026,
    };
    if(this.m.cod_geografico) body.cod_geografico = this.m.cod_geografico;
    if(this.form.sector_id) body.sector_id = this.form.sector_id;
    if(this.form.indicador) body.indicador = this.form.indicador;
    if(this.form.formula) body.formula = this.form.formula;
    if(this.form.lb) body.linea_base = this._num(this.form.lb);
    if(this.form.meta) body.meta_2030 = this._num(this.form.meta);
    // Convertir programaciones a array normalizado
    const programaciones: any[] = [];
    if(this.form.prog_fis) {
      for(const k of Object.keys(this.form.prog_fis)) {
        const v = this.form.prog_fis[k];
        if(v !== '' && v !== null && v !== undefined) {
          programaciones.push({ anio: parseInt(k), tipo: 'fisica', valor: this._num(v) });
        }
      }
    }
    if(this.form.prog_fin) {
      for(const k of Object.keys(this.form.prog_fin)) {
        const v = this.form.prog_fin[k];
        if(v !== '' && v !== null && v !== undefined) {
          programaciones.push({ anio: parseInt(k), tipo: 'financiera', valor: this._num(v) });
        }
      }
    }
    if(programaciones.length) body.programaciones = programaciones;
    this.api.post('/pad/resultados-territoriales/', body).subscribe({
      next: (r: any) => {
        this.ultimoResultado = r;
        this.msg = '✅ Resultado guardado correctamente';
        this.msgClass = 'exito';
        setTimeout(() => { this.paso = 8; }, 800);
      },
      error: (e: any) => {
        console.error('Error guardando resultado:', e);
        const errBody = e.error || e;
        const detail = errBody?.error ? (typeof errBody.error === 'object' ? Object.values(errBody.error).flat().join('; ') : String(errBody.error)) : (e.message || 'Error desconocido');
        this.msg = '❌ ' + detail;
        this.msgClass = 'error';
        this.cdr.markForCheck();
      }
    });
  }

  vincularAmp(id:string): void {
    if(!id)return;
    this.ampVinculadas.push(this.amps.find((a:any)=>a.id===id));
  }

  crearAmp(): void {
    const c=prompt('Código AMP:'); if(!c)return;
    const n=prompt('Nombre:'); if(!n)return;
    this.api.post('/acciones-mediano-plazo/', {codigo:c,nombre:n,gestion_inicio:2026,gestion_fin:2030})
      .subscribe({next:(r:any)=>{this.ampVinculadas.push(r); this.cargarAmps();}});
  }

  vincularAcp(id:string): void {
    if(!id)return;
    this.acpVinculadas.push(this.acps.find((a:any)=>a.id===id));
  }

  crearAcp(): void {
    const c=prompt('Código ACP:'); if(!c)return;
    const n=prompt('Nombre:'); if(!n)return;
    this.api.post('/acciones-corto-plazo/', {codigo:c,nombre:n,gestion:2026})
      .subscribe({next:(r:any)=>{this.acpVinculadas.push(r); this.cargarAcps();}});
  }

  finalizar(): void {
    alert('✓ Articulación completada. Revise la Matriz de Articulación Completa abajo.');
  }

  mostrarMatriz(): boolean {
    return !!this.m.pgdesa || !!this.m.politica || !!this.ultimoResultado;
  }

  exportarMatriz(): void {
    let txt='=== MATRIZ DE ARTICULACIÓN PAD ===\n';
    txt+=`PGDESA: ${this.m.pgdesa?.codigo||'-'} - ${this.m.pgdesa?.nombre||'-'}\n`;
    txt+=`Objetivo: ${this.m.pgdesa_objetivo||'-'}\n`;
    txt+=`PDESA: ${this.m.pdesa?.codigo||'-'} - ${this.m.pdesa?.nombre||'-'}\n`;
    txt+=`ODS: ${this.m.ods||'-'} | NDC: ${this.m.ndc||'-'} | NDT: ${this.m.ndt||'-'}\n`;
    txt+=`PDS: ${this.m.sector_cod||'-'}.${this.m.pds_cod||'-'} - ${this.m.pds_resultado||'-'}\n`;
    txt+=`PAD: ${this.m.cod_geografico||'-'} - ${this.m.denominacion_eta||'-'}\n`;
    txt+=`Política: ${this.m.politica?.codigo||'-'} - ${this.m.politica?.nombre||'-'}\n`;
    txt+=`Lineamiento: ${this.m.lineamiento?.codigo||'-'} - ${this.m.lineamiento?.nombre||'-'}\n`;
    txt+=`Resultado: ${this.ultimoResultado?.codigo||'-'} - ${(this.ultimoResultado?.nombre||'').slice(0,80)}\n`;
    txt+=`Producto: ${this.form.prod_cod||'-'} - ${this.form.prod_nom||'-'}\n`;
    alert(txt);
  }

  reiniciar(): void {
    if(!confirm('¿Reiniciar la articulación?'))return;
    this.paso=0; this.m={pgdesa:null,pgdesa_objetivo:'',pdesa:null,pdesa_objetivo:'',ods:'',ndc:'',ndt:'',comp3030:'',sector_cod:'',sector_nombre:'',pds_cod:'',pds_resultado:'',cod_geografico:'1102',denominacion_eta:'Gobierno Autónomo Municipal de Sacaba',politica:null,lineamiento:null};
    this.form={cod_res:'',resultado:'',sector_id:'',prod_cod:'',prod_nom:'',territorio:'',responsable:'',indicador:'',formula:'',lb:0,meta:0,unidad:'',prog_fis:{},prog_fin:{},cuenta_con_financiamiento:'NO',presupuesto_total_pad:null};
    this.ultimoResultado=null; this.ampVinculadas=[]; this.acpVinculadas=[];
  }

  cargarSectores(): void { this.api.get<any>('/pad/sectores-pad/').subscribe({next:(r:any)=>this.sectores=r.results||r}); }
  cargarPoliticas(): void { this.api.get<any>('/pad/politicas-pad/',{gestion:2026}).subscribe({next:(r:any)=>this.politicas=r.results||r}); }
  cargarLineamientos(): void { this.api.get<any>('/pad/lineamientos/').subscribe({next:(r:any)=>this.lineamientos=r.results||r}); }
  cargarAmps(): void { this.api.get<any>('/acciones-mediano-plazo/').subscribe({next:(r:any)=>this.amps=r.results||r}); }
  cargarAcps(): void { this.api.get<any>('/acciones-corto-plazo/',{gestion:2026}).subscribe({next:(r:any)=>this.acps=r.results||r}); }
}
