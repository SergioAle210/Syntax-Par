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

## Estructura del Proyecto

El proyecto se compone de varios módulos que implementan la funcionalidad completa:

- **lexer.py:**  
  Implementa la función `lex` que, a partir de un AFD (Autómata Finito Determinista) generado, analiza un texto de entrada y produce una lista de tokens. Incluye funciones auxiliares (por ejemplo, `custom_trim`, `custom_to_int`, etc.) y maneja errores léxicos.

- **regexpToAFD.py:**  
  Realiza la construcción directa de un AFD a partir de una expresión regular. Entre sus funciones se incluyen:

  - Tokenización de la expresión regular.
  - Inserción de operadores de concatenación.
  - Conversión a notación postfix.
  - Construcción del árbol de sintaxis.
  - Cálculo de transiciones y followpos para la construcción del AFD.

- **yalex_parser.py:**  
  Se encarga de parsear el archivo YALex (.yal) extrayendo:

  - Secciones de header y trailer.
  - Definiciones de expresiones regulares.
  - Reglas y acciones asociadas.  
    Integra además la expansión y transformación de expresiones regulares, y coordina la generación del árbol de sintaxis y del AFD. También cuenta con funciones para visualizar el árbol y el autómata utilizando Graphviz.

- **yalex_utils.py:**  
  Contiene funciones auxiliares para el manejo y parseo de archivos YALex, tales como:

  - Eliminación de comentarios.
  - Extracción de definiciones y reglas.
  - Expansión de rangos en conjuntos.
  - Conversión de literales a sus valores ASCII.

- **Archivos de AFD (lexer-0.json, lexer-1.json):**  
  Ejemplos de autómatas serializados en formato JSON, utilizados para probar o almacenar la configuración del analizador léxico.

- **input.txt:**  
  Archivo de ejemplo que contiene datos de entrada para el análisis léxico.

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
