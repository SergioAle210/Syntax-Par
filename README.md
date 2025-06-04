

## Características

- **Compatibilidad con Lex:** La sintaxis de las expresiones regulares, las convenciones de rule, let y la semántica de selección de lexemas están inspiradas en Lex (o flex). Esto permite migrar especificaciones existentes con cambios mínimos, facilitando la adopción de YALex en proyectos que anteriormente utilizaban herramientas tradicionales de Unix. Al mantener la lógica de “preferir el lexema más largo” y “priorizar el orden de aparición en caso de empate”, se asegura un comportamiento equivalente al de Lex, reduciendo la curva de aprendizaje.
- **Soporte para Comentarios:** Los comentarios en un archivo .yal se delimitan con (* al inicio y *) al final, de forma similar a OCaml. YALex elimina completamente estos comentarios antes de procesar el contenido, garantizando que ni el header, ni las definiciones de expresiones regulares, ni las reglas de tokens se vean afectadas. Esto ofrece al usuario libertad para documentar internamente su especificación léxica sin alterar el comportamiento del analizador.
- **Secciones Opcionales:** Tanto la sección de header (al principio) como la de trailer (al final) son completamente opcionales. Si no se incluyen, YALex simplemente no genera código adicional en esas zonas. Si el usuario necesita agregar dependencias o inicializaciones previas al autómata, basta con incluirlas dentro de { ... } en la parte superior del .yal. Asimismo, para agregar rutinas o definiciones después de las reglas, se usa el trailer.
- **Definiciones de Expresiones Regulares:**Gracias a la sintaxis let ident = regexp, es posible factorizar expresiones repetidas o complejas en un solo identificador. Por ejemplo, let letter = ['A'-'Z''a'-'z'] puede reutilizarse en múltiples reglas. Durante el parseo, YALex expande recursivamente cada referencia a ident por su patrón original, envolviendo el resultado entre paréntesis para preservar la precedencia. Esto simplifica el mantenimiento y hace que los archivos .yal sean más legibles.
- **Operadores y Sintaxis Extendida:**
  - Literales (caracteres y cadenas): Pueden indicarse con comillas simples o dobles. Por ejemplo, '+', ";=", "while". Internamente se convierten en valores ASCII separados por espacio para constituir transiciones concretas en el autómata.
  - Secuencias de escape: Para representar saltos de línea (\n), tabulaciones (\t) u otros, se admite la sintaxis habitual de cadenas. Estas secuencias se procesan para generar el código ASCII correspondiente.
  - Metacaracter `_` para denotar cualquier símbolo.
  - Conjuntos de caracteres mediante corchetes, con soporte para rangos y complementos (`[^...]`).
  - Operadores como cerradura de Kleene (`*`), cerradura positiva (`+`), operador opcional (`?`), alternancia (`|`), concatenación implícita y el operador `#` para la diferencia de conjuntos.
- **Resolución de Ambigüedades:** YALex aplica la estrategia tradicional de “longest match” (lexema más largo). Durante el escaneo, el autómata lleva un registro del último estado de aceptación alcanzado y retrocede a esa posición cuando no hay transiciones válidas. De esta forma, siempre se elige el lexema de mayor longitud posible. Si dos patrones producen el mismo lexema de longitud máxima, se prioriza el que aparece primero en la definición de la regla rule. Esto garantiza predictibilidad y coincide con el comportamiento de Lex clásico.
- **Acciones Asociadas:** Cada expresión regular en la sección rule lleva un bloque de acción en código. En la mayoría de proyectos educativos, la acción suele ser return TOKEN_NAME, devolviendo un enumerado que representa el tipo de token. Sin embargo, se pueden incluir fragmentos arbitrarios del lenguaje de destino (Python, C, OCaml), permitiendo:
  - Llevar un conteo de líneas o columnas.
  - Construir estructuras de datos (nodos de un árbol, entradas en una tabla de símbolos).
  - Invocar funciones auxiliares para análisis semántico ligero (por ejemplo, conversión de cadenas numéricas a valores enteros).
  - Detener el escaneo con un error léxico personalizado

---

## Estructura del Archivo YALex

Un archivo `.yal` sigue una estructura similar a la siguiente:
{ header } let ident = regexp ... rule entrypoint [arg1 ... argn] = regexp { action } | regexp { action } | ... { trailer }

- **Header y Trailer:** Secciones opcionales para incluir código adicional.
- **Definiciones:** Declaraciones para expresar patrones comunes que se pueden reutilizar.
- **Regla de Entrada:** Define la función que, al ser invocada, procesa el buffer de entrada y utiliza las expresiones regulares y acciones asociadas para reconocer tokens.

---
## Estructura del Archivo YALPar

Un archivo `.yalp` sigue una estructura similar a la siguiente:
{ header } let ident = regexp... rule entrypoint [arg1... argn] = regexp { action } | regexp { action } |... { trailer }

- **Header y Trailer:** Secciones opcionales para incluir código adicional.
- **Definiciones:** Declaraciones para expresar patrones comunes que se pueden reutilizar.
- **Regla de Entrada:** Define la función que, al ser invocada, procesa el buffer de entrada y utiliza las expresiones regulares y acciones asociadas para reconocer tokens.

---
## Ejemplo de Especificación YALex

A modo de ejemplo, se muestra un archivo simplificado `ejemplo.yal`:

```yalex
(* Lexer para Gramática No. 4 *)

(* Introducir cualquier header aqui *)

let delim = [' ''\t''\n']
let ws = delim+
let letter = ['A'-'Z''a'-'z']       
let str = (_)*
let digit = ['0'-'9']
let digits = digit+
let id = letter(letter|str|digit)*
let number = digits(.digits)?('E'['+''-']?digits)?

rule tokens =
    ws
  | id        { return ID }               
  | number    { return NUMBER }
  | ';'       { return SEMICOLON }
  | ":="      { return ASSIGNOP }
  | '<'       { return LT }
  | '='       { return EQ }
  | '+'       { return PLUS }
  | '-'       { return MINUS }
  | '*'       { return TIMES }
  | '/'       { return DIV }
  | '('       { return LPAREN }
  | ')'       { return RPAREN }


```

## Ejecución del proyecto

## Estructura del Proyecto

El proyecto se compone de varios módulos que implementan la funcionalidad completa:

# YALex & YAPar
YALex es un generador de analizadores léxicos inspirado en Lex, mientras que YAPar es el módulo de análisis sintáctico (parser) basado en algoritmos LR(0) y SLR, ambos fundamentales en la construcción de compiladores modernos.

## Descripción General
El proyecto ahora se compone de dos grandes bloques:

- lex/ : Todo lo relacionado con el análisis léxico (YALex).
- yapar/ : Todo lo relacionado con el análisis sintáctico LR (YAPar).
Esta separación sigue la teoría clásica de compiladores, donde el análisis léxico y sintáctico son fases independientes pero complementarias.

## Estructura del Proyecto
```
lex/           # Módulo 
léxico (YALex)
yapar/         # Módulo 
sintáctico (YAPar)
lexers/        # Autómatas y 
pickles generados
output_lexers/ # Salidas del 
lexer
docs/          # 
Documentación y ejemplos
README.md      # Este archivo
```
### lex/
- lexer.py : Implementa el autómata finito determinista (AFD) para el análisis léxico. Utiliza funciones auxiliares manuales para manipulación de cadenas, evitando librerías estándar, lo que refuerza el aprendizaje de algoritmos básicos.
- regexpToAFD.py : Construye el AFD a partir de expresiones regulares, siguiendo el algoritmo de construcción directa (Thompson, subconjuntos, followpos).
- yalex_parser.py : Parsea archivos .yal y coordina la generación del AFD.
- yalex_utils.py : Funciones auxiliares para manejo de cadenas, expansión de rangos, y parseo manual de archivos, alineado con la teoría de autómatas y expresiones regulares.
### yapar/
- parser.py : Orquesta el proceso de análisis sintáctico, integrando el lexer y el parser. Implementa la inferencia dinámica del mapa de tokens y la simulación del parser SLR.
- LR0.py : Implementa el algoritmo de construcción de autómatas LR(0), base teórica para la generación de analizadores sintácticos LR.
- SLR.py : Construye la tabla SLR (Simple LR), aplicando teoría de conjuntos FIRST y FOLLOW, y resuelve acciones de desplazamiento/reducción.
- first_follow.py : Calcula los conjuntos FIRST y FOLLOW, esenciales para la construcción de tablas LR y la detección de ambigüedades.
- sim_slr.py : Simula el parser SLR sobre una secuencia de tokens, mostrando el proceso paso a paso.

---

## Uso del Proyecto

1. **Creación del archivo de especificación:**  
   Escribe un archivo YALex (por ejemplo, `lexer.yal`) siguiendo la estructura y sintaxis descritas.

2. **Generación del analizador léxico:**  
    Ejecuta el siguiente comando en la terminal:
   yalex lexer.yal -o thelexer
   Esto generará el archivo `thelexer`, el cual contendrá el código del analizador léxico basado en la especificación proporcionada.

3. **Integración con el parser:**
   El archivo generado se puede integrar con el parser (como YAPar) para formar un módulo completo de análisis sintáctico o de traducción.

4. **Ejecución de pruebas:**
   Puedes utilizar el módulo `lexer.py` para probar el análisis léxico sobre archivos de entrada (por ejemplo, `input.txt`), y `yalex_parser.py` para el proceso completo de parseo y generación del AFD. 

---

3. **Integración con el parser:**  
   El archivo generado se puede integrar con el parser (como YAPar) para formar un módulo completo de análisis sintáctico o de traducción.

4. **Ejecución de pruebas:**  
   Puedes utilizar el módulo `lexer.py` para probar el análisis léxico sobre archivos de entrada (por ejemplo, `input.txt`), y `yalex_parser.py` para el proceso completo de parseo y generación del AFD.

---

## Ejecución del proyecto

Inicialmente hay que seleccionar que archivo yal vamos a utilizar para construir y generar el .json y pickle para posteriormente pasárselo al lexer. Para esto debemos de ejecutar lo siguiente:

```bash
python ./yalex_parser.py
```

Posteriormeente de esto nos generará una carpeta llamada lexers que esta carpeta contendrá o esta determinada para almacenar todas las instrucciones que generemos para nuestro lexer. Posteriormente le indicamos en el lexer.py que archivo .pickle queremos leer y también indicamos que archivo ".txt" queremos que se lea para hacer el lexer (data_random.txt por ejemplo).

Ya con la dirección y nombre del archivo introducido procedemos a ejecutar:

```bash
python lexer.py
```

Esto ejecutará el lexer en base a las instrucciones que nosotros generamos en el parser del yalex y también en base a la entrada de la data para generar los tokens y sus lexemas. Esto generará un archivo lexer_output en la carpeta output_lexers donde estará el archivo .txt correspondiente que contendrá el token determinado para el lexema encontrado.

Para ejecutar el parser:

```bash
python yapar/parser.py <archivo.yalp> <input.txt> <dfa.pickle>
```
