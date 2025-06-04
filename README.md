# YALex

**YALex (Yet Another Lex)** es un generador de analizadores léxicos inspirado en Lex y en la herramienta ocamllex para OCaml. Su principal objetivo es generar, a partir de una definición de expresiones regulares escrita en un archivo con extensión `.yal`, un analizador léxico que pueda integrarse fácilmente con un parser (por ejemplo, YAPar) para construir módulos completos de análisis sintáctico o de traducción.

---

## Descripción

YALex permite definir la especificación léxica en un archivo `.yal` que puede contener:

- **Sección de Header (opcional):** Código que se copia al inicio del archivo generado.
- **Definiciones:** Declaraciones de expresiones regulares frecuentes usando la sintaxis `let ident = regexp`.
- **Regla de Entrada:** Se define una función (entrypoint) mediante la instrucción `rule`, la cual especifica los patrones (expresiones regulares) y las acciones asociadas que se deben ejecutar al reconocer un token.
- **Sección de Trailer (opcional):** Código que se adjunta al final del archivo generado.

La idea es que el analizador léxico resultante procese un buffer de entrada, reconociendo el lexema más largo que coincida con alguna de las expresiones definidas, y ejecute la acción correspondiente a ese patrón.

La llamada esperada para generar el analizador es:
yalex lexer.yal -o thelexer

donde `lexer.yal` es el archivo de especificación y `thelexer` es el archivo generado con el código del analizador.

---

## Características

- **Compatibilidad con Lex:** La sintaxis y el comportamiento se inspiran en Lex, facilitando la transición o integración en proyectos existentes.
- **Soporte para Comentarios:** Los comentarios se delimitan mediante `(*` y `*)`.
- **Secciones Opcionales:** Permite incluir secciones de header y trailer, cuyo contenido se inserta respectivamente al inicio y al final del archivo generado.
- **Definiciones de Expresiones Regulares:** Se pueden definir identificadores para expresiones regulares comunes mediante sentencias del tipo `let ident = regexp`.
- **Operadores y Sintaxis Extendida:**
  - Literales (caracteres y cadenas) y secuencias de escape.
  - Metacaracter `_` para denotar cualquier símbolo.
  - Conjuntos de caracteres mediante corchetes, con soporte para rangos y complementos (`[^...]`).
  - Operadores como cerradura de Kleene (`*`), cerradura positiva (`+`), operador opcional (`?`), alternancia (`|`), concatenación implícita y el operador `#` para la diferencia de conjuntos.
- **Resolución de Ambigüedades:** Se selecciona el lexema más largo; en caso de empate, se prioriza por el orden de definición.
- **Acciones Asociadas:** Cada patrón puede tener una acción en código (del lenguaje de destino) que se ejecuta al reconocer el token.

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
  | id        { return ID }               (* Cambie por una acción válida, que devuelva el token *)
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

(* Introducir cualquier trailer aqui *)
```

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
