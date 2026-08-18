/**
 * Marco de articulación con la planificación nacional 2026-2030.
 *
 * Fuente: Guía Metodológica PEI 2026-2030, acápite IV "Estructura de
 * articulación con la planificación nacional" (Tabla 1), y Guía Metodológica
 * PAD 2026-2030 §4.5.2. El PAD y el PEI articulan al MISMO marco nacional:
 * este catálogo es la única fuente de verdad para ambos.
 */

/** Gestiones del quinquenio de planificación. */
export const GESTIONES_QUINQUENIO = ['2026', '2027', '2028', '2029', '2030'] as const;

export type GestionQuinquenio = (typeof GESTIONES_QUINQUENIO)[number];

export interface ComponentePdesa {
  codigo: string;
  objetivoEfecto: string;
}

export interface EjePgdesa {
  codigo: string;
  titulo: string;
  objetivoImpacto: string;
  componentes: ComponentePdesa[];
}

/** Tabla 1: ejes PGDESA (objetivo de impacto) y componentes PDESA (objetivo de efecto). */
export const EJES_PGDESA: EjePgdesa[] = [
  {
    codigo: '1',
    titulo: 'Economía para la gente',
    objetivoImpacto:
      'Economía para la gente: La economía nacional ha registrado un crecimiento sostenido y más diversificado sustentado en la expansión de la actividad productiva y un entorno de mayor certidumbre.',
    componentes: [
      {
        codigo: '1.1',
        objetivoEfecto:
          'Estabilidad macroeconómica: Se mantiene un entorno macroeconómico estable y predecible, con inflación controlada, finanzas públicas sostenibles, estabilidad financiera y fortalecimiento del sector externo.',
      },
      {
        codigo: '1.2',
        objetivoEfecto:
          'Diversificación productiva: La estructura productiva nacional se ha diversificado sectorial y territorialmente con orientación hacia la generación de valor agregado y fortalecimiento de encadenamientos productivos y cadenas de valor competitivas.',
      },
      {
        codigo: '1.3',
        objetivoEfecto:
          'Tecnología e innovación para la productividad: Han aumentado los niveles de productividad.',
      },
      {
        codigo: '1.4',
        objetivoEfecto:
          'Trabajo decente: Ha aumentado el número de trabajadores que tiene un trabajo decente con ingresos dignos, mayor estabilidad laboral y cobertura de la protección social.',
      },
      {
        codigo: '1.5',
        objetivoEfecto:
          'Seguridad y diversificación energética: Se ha avanzado en la diversificación y sostenibilidad de la matriz energética orientada a la seguridad energética.',
      },
      {
        codigo: '1.6',
        objetivoEfecto:
          'Economía basada en el conocimiento: Se ha consolidado una economía basada en el conocimiento y la información, donde la producción material, intelectual, tecnológica y cultural de los agentes económicos constituye el motor para la inversión y el crecimiento inclusivo.',
      },
    ],
  },
  {
    codigo: '2',
    titulo: 'Bolivia al mundo y el mundo a Bolivia',
    objetivoImpacto:
      'Bolivia al mundo y el mundo a Bolivia: Bolivia ha consolidado su posicionamiento como actor estratégico geoeconómico y geopolítico en el sistema internacional.',
    componentes: [
      {
        codigo: '2.1',
        objetivoEfecto:
          'Posicionamiento estratégico: Bolivia ha posicionado estratégicamente sus potencialidades en el ámbito internacional, convirtiéndose en un país atractivo para el turismo sostenible y cultural.',
      },
      {
        codigo: '2.2',
        objetivoEfecto:
          'Inserción externa y comercio internacional: Se ha consolidado una inserción externa activa y diversificada, de bienes y servicios con mayor valor agregado.',
      },
      {
        codigo: '2.3',
        objetivoEfecto:
          'Inversión extranjera: Se ha incrementado la inversión extranjera en el país.',
      },
      {
        codigo: '2.4',
        objetivoEfecto:
          'Integración regional: Se ha avanzado en la integración regional como plataforma para el desarrollo económico, territorial y el fortalecimiento de la gestión de fronteras y la movilidad humana.',
      },
    ],
  },
  {
    codigo: '3',
    titulo: 'Bolivia 50/50',
    objetivoImpacto:
      'Bolivia 50/50: Se ha consolidado un modelo de Estado con autonomías efectivas, corresponsabilidad fiscal y coordinación intergubernativa, orientado a reducir las brechas territoriales y mejorar la provisión de servicios y oportunidades para la población del país.',
    componentes: [
      {
        codigo: '3.1',
        objetivoEfecto:
          'Consolidación del régimen autonómico: Se ha avanzado en la distribución clara y equilibrada de competencias, responsabilidades y recursos entre los diferentes niveles de gobierno.',
      },
      {
        codigo: '3.2',
        objetivoEfecto:
          'Gobernanza y gestión pública por resultados: Se han desarrollado capacidades en los gobiernos subnacionales para mejorar el desempeño de la gestión pública en materia de eficiencia, transparencia, generación y administración de recursos y gestión por resultados orientada al bienestar de la población.',
      },
      {
        codigo: '3.3',
        objetivoEfecto:
          'Gestión y organización territorial: Se ha ordenado y articulado el territorio nacional mediante un sistema de asentamientos humanos y planificación territorial.',
      },
      {
        codigo: '3.4',
        objetivoEfecto:
          'Articulación y coordinación multinivel: Se ha logrado una articulación y coordinación efectivas entre niveles de gobierno, para la implementación de políticas públicas.',
      },
    ],
  },
  {
    codigo: '4',
    titulo: 'Bolivia Moderna y Eficiente',
    objetivoImpacto:
      'Bolivia Moderna y Eficiente: Se han fortalecido las instituciones del Estado y modernizado sus servicios para hacerlos más eficientes y eficaces.',
    componentes: [
      {
        codigo: '4.1',
        objetivoEfecto:
          'Servicios públicos centrados en las personas: Se ha reducido el tiempo, recursos y esfuerzo para la población y las empresas al realizar trámites.',
      },
      {
        codigo: '4.2',
        objetivoEfecto:
          'Gobierno electrónico y transformación digital: Se han automatizado y articulado procesos y servicios sensibles para la población.',
      },
      {
        codigo: '4.3',
        objetivoEfecto:
          'Servicio público competente: Se ha cualificado el capital humano que presta servicios en el Estado, con meritocracia y gestión por resultados.',
      },
      {
        codigo: '4.4',
        objetivoEfecto:
          'Gestión de la información: Se ha institucionalizado la gestión integrada y soberana de datos orientada a que las decisiones se tomen con base en evidencia.',
      },
    ],
  },
  {
    codigo: '5',
    titulo: 'Bolivia transparente',
    objetivoImpacto:
      'Bolivia transparente: Se han recuperado las bases del Estado democrático y social de derecho.',
    componentes: [
      {
        codigo: '5.1',
        objetivoEfecto:
          'Acceso a una justicia independiente, plural y oportuna: Se ha consolidado un sistema de justicia accesible, oportuno, gratuito y culturalmente pertinente con controles que velan por su independencia, imparcialidad, pluralismo y el respeto efectivo de los derechos humanos.',
      },
      {
        codigo: '5.2',
        objetivoEfecto:
          'Reforma normativa para la seguridad jurídica: Se ha actualizado, armonizado y depurado el ordenamiento jurídico nacional.',
      },
      {
        codigo: '5.3',
        objetivoEfecto:
          'Transparencia institucional y cultura de integridad: Se ha implementado una cultura de integridad en la gestión pública, a partir de la participación ciudadana y garantía del derecho ciudadano al acceso a la información pública, reducción de la discrecionalidad y rendición de cuentas del Estado.',
      },
      {
        codigo: '5.4',
        objetivoEfecto:
          'Política criminal, seguridad ciudadana y lucha contra el crimen: Se ha logrado reducir la criminalidad y mejorar la seguridad ciudadana con la implementación de una política criminal integral, democrática y con enfoque de derechos humanos.',
      },
      {
        codigo: '5.5',
        objetivoEfecto:
          'Seguridad integral y defensa del Estado: Se han generado condiciones de seguridad para el Estado Boliviano que otorgan las garantías necesarias para el desenvolvimiento armónico y pacífico de sus actividades económicas, políticas, científicas tecnológicas y culturales.',
      },
      {
        codigo: '5.6',
        objetivoEfecto:
          'Democracia y participación ciudadana: Las personas y sus organizaciones cuentan con mecanismos mejorados de participación en las decisiones de la gestión pública en el marco de la Constitución y las Leyes.',
      },
    ],
  },
  {
    codigo: '6',
    titulo: 'Bolivia, bienestar para todas y todos',
    objetivoImpacto:
      'Bolivia, bienestar para todas y todos: Se ha mejorado el bienestar integral de la población en materia de fortalecimiento de sus capacidades, mejora de sus condiciones de vida y avance en la reducción de las desigualdades.',
    componentes: [
      {
        codigo: '6.1',
        objetivoEfecto:
          'Desarrollo del capital humano: Se ha mejorado de manera sostenida el capital humano (salud y educación) a lo largo del ciclo de vida, como base para el bienestar y el desarrollo productivo.',
      },
      {
        codigo: '6.2',
        objetivoEfecto:
          'Corresponsabilidad en los trabajos de cuidado: Se ha incrementado la corresponsabilidad social, familiar, estatal y del sector privado, en los trabajos de cuidado.',
      },
      {
        codigo: '6.3',
        objetivoEfecto:
          'Hábitat digno con servicios básicos universales: Se han mejorado las condiciones de habitabilidad y la conectividad de los servicios de comunicación para la población.',
      },
      {
        codigo: '6.4',
        objetivoEfecto:
          'Reducción de la exposición a riesgos económicos: Se ha reducido la exposición de la población a riesgos económicos y sociales, con énfasis en los grupos en mayor situación de vulnerabilidad.',
      },
      {
        codigo: '6.5',
        objetivoEfecto:
          'Reducción de la violencia: Se han reducido, de manera integral, todas las formas de violencia.',
      },
      {
        codigo: '6.6',
        objetivoEfecto:
          'Inclusión social: Se ha incrementado la inclusión y reducido la discriminación de toda la población, en particular la que está en situación de vulnerabilidad.',
      },
      {
        codigo: '6.7',
        objetivoEfecto:
          'Desarrollo integral de la niñez y adolescencia: Se ha avanzado en el desarrollo integral y adecuado de niñas, niños y adolescentes.',
      },
    ],
  },
  {
    codigo: '7',
    titulo: 'Bolivia Verde y Sostenible',
    objetivoImpacto:
      'Bolivia Verde y Sostenible: Se ha reducido la degradación ambiental y la vulnerabilidad climática del país, mejorando la calidad de vida de la población y la sostenibilidad de los sistemas productivos mediante la gestión integral y el uso sostenible de los recursos naturales.',
    componentes: [
      {
        codigo: '7.1',
        objetivoEfecto:
          'Gestión sostenible de bosques, tierras forestales, ecosistemas y biodiversidad: Se ha fortalecido la gestión integral de bosques, tierras forestales y ecosistemas impulsando la conservación y uso sostenible de la biodiversidad, la valoración de servicios ecosistémicos y la reducción de la contaminación, como bases de la producción, la resiliencia climática y el desarrollo sostenible.',
      },
      {
        codigo: '7.2',
        objetivoEfecto:
          'Gestión integral y uso sostenible de los recursos hídricos y suelo: Se ha mejorado la seguridad hídrica y la sostenibilidad del uso del suelo, reduciendo la degradación y mejorando la disponibilidad y uso eficiente del agua.',
      },
      {
        codigo: '7.3',
        objetivoEfecto:
          'Cambio climático: Se ha reducido la vulnerabilidad climática y las emisiones de gases de efecto invernadero.',
      },
      {
        codigo: '7.4',
        objetivoEfecto:
          'Gestión integral de riesgos: Se ha reducido el impacto de los desastres naturales en la población y la economía mediante una gestión del riesgo que contempla la prevención, reducción, preparación y respuesta frente a amenazas, integrada en la planificación territorial.',
      },
      {
        codigo: '7.5',
        objetivoEfecto:
          'Calidad ambiental y transición hacia economía circular: Se ha mejorado la calidad ambiental del aire, agua y suelo, reduciendo la contaminación bajo principios de la economía circular.',
      },
      {
        codigo: '7.6',
        objetivoEfecto:
          'Gobernanza, marco normativo y financiamiento para la transición verde: Se ha fortalecido la institucionalidad ambiental y climática, mejorando la coordinación, el cumplimiento normativo y el acceso a financiamiento para la sostenibilidad.',
      },
      {
        codigo: '7.7',
        objetivoEfecto:
          'Gestión del conocimiento, innovación y desarrollo de capacidades para la sostenibilidad: Se ha fortalecido la base científica, tecnológica y talento humano del país en materia ambiental y climática, para la transición hacia un desarrollo sostenible, impulsando investigación básica y aplicada, innovación tecnológica, educación ambiental y formación técnica como soporte del desarrollo resiliente y bajo en carbono.',
      },
    ],
  },
];

/** Objetivos de Desarrollo Sostenible — Sección II de la matriz. */
export const CATALOGO_ODS: { codigo: string; nombre: string }[] = [
  { codigo: '1', nombre: 'Fin de la pobreza' },
  { codigo: '2', nombre: 'Hambre cero' },
  { codigo: '3', nombre: 'Salud y bienestar' },
  { codigo: '4', nombre: 'Educación de calidad' },
  { codigo: '5', nombre: 'Igualdad de género' },
  { codigo: '6', nombre: 'Agua limpia y saneamiento' },
  { codigo: '7', nombre: 'Energía asequible y no contaminante' },
  { codigo: '8', nombre: 'Trabajo decente y crecimiento económico' },
  { codigo: '9', nombre: 'Industria, innovación e infraestructura' },
  { codigo: '10', nombre: 'Reducción de las desigualdades' },
  { codigo: '11', nombre: 'Ciudades y comunidades sostenibles' },
  { codigo: '12', nombre: 'Producción y consumo responsables' },
  { codigo: '13', nombre: 'Acción por el clima' },
  { codigo: '14', nombre: 'Vida submarina' },
  { codigo: '15', nombre: 'Vida de ecosistemas terrestres' },
  { codigo: '16', nombre: 'Paz, justicia e instituciones sólidas' },
  { codigo: '17', nombre: 'Alianzas para lograr los objetivos' },
];
