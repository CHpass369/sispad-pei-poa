declare function describe(description: string, specDefinitions: () => void): void;
declare function beforeEach(specDefinitions: () => void | Promise<void>): void;
declare function it(description: string, testFunction: () => void): void;
declare function expect(actual: unknown): any;
declare function spyOn(target: object, method: string): any;

declare namespace jasmine {
  interface SpyObj<T = any> {
    [method: string]: any;
  }

  function createSpyObj<T = any>(
    baseName: string,
    methodNames: string[],
  ): SpyObj<T>;

  function createSpy(name: string): any;
}
