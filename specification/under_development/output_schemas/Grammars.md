# ABNF Grammars For Schema Definitions

The ABNF grammars for the [Labeled](./Labeled.md) and [Ordered](./Ordered.md)
define the technical content of the files. The details of the QIR calls and how
they map to the input is covered in the associated specifications. Type
consistency cannot be defined for array elements and is a validation concern
when consuming output.

A _prototype_ parser for this grammar that can validate examples in this specification
is included in the form of [a Python script](./qir-output.py).

## Grammars

### Shared Top Level

The grammars share a basic structure and only vary in their definition of
values, tuples, and arrays. The top level definitions are the same:

```abnf
file = header-schema-id EOL header-schema-version *(EOL header) 1*(EOL shot) [EOL]

header-schema-id = HEADER-LIT TAB SCHEMA-ID-LIT TAB (ORDERED-SCHEMA-LIT / LABELED-SCHEMA-LIT)

header-schema-version = HEADER-LIT TAB SCHEMA-VERSION-LIT TAB field

header = HEADER-LIT TAB field TAB field

shot = start *(EOL record) EOL end

record = metadata / output

metadata = METADATA-LIT TAB field [TAB field]

output = (container / value)

container = (tuple / array)
```

### Labeled

```abnf
value = output-start (result / bool / int / double) TAB label

tuple = output-start TUPLE-LIT TAB 1*DIGIT TAB label

array = output-start ARRAY-LIT TAB 1*DIGIT TAB label
```

### No Labels and Ordered

```abnf
value = output-start (result / bool / int / double)

tuple = output-start tuple-start 1*collection-items

tuple-start = TUPLE-LIT TAB 1*DIGIT

array = output-start array-start collection-items

array-start = ARRAY-LIT TAB 1*DIGIT

collection-items = array-items / tuple-items / value-items

value-items = 1*(EOL value)

array-items = 1*(EOL array)

tuple-items = 1*(EOL tuple)
```

### Shared Core Definitions

```abnf
output-start = OUTPUT-LIT TAB

result = RESULT-LIT TAB BIT

bool = BOOL-LIT TAB (TRUE-LIT / FALSE-LIT)

int = INT_LIT TAB [sign] 1*DIGIT

double = DOUBLE-LIT TAB DOUBLE-VALUE

DOUBLE-VALUE = [sign] (inf / nan / float)

inf = INF-LIT / INFINITY-LIT

nan = NAN-LIT

float = ( 1*DIGIT / (*DIGIT "." 1*DIGIT) ) [exponent]

exponent = "e" [sign] 1*DIGIT

sign = "+" / "-"

field = (escaped / non-escaped)

label = (escaped / non-escaped)

escaped = DQUOTE non-escaped DQUOTE

non-escaped = *TEXTDATA

TAB = %x09

LF = %x0A

CR = %x0D

CRLF = CR LF

EOL = (LF / CR / CRLF)

DQUOTE = %x22

; Codes %x20 to %x7E are known as the ASCII printable characters
; %x22, DQUOTE ("), is omitted here so that it can be the
; used to define escaped text.
TEXTDATA = %x20-21 / %x23-7E

DIGIT = %x30-39

BIT = "0" / "1"

start = START-LIT

end = END-LIT TAB "0"

TRUE-LIT = "t" "r" "u" "e"

FALSE-LIT = "f" "a" "l" "s" "e"

INF-LIT = "I" "N" "F"

INFINITY-LIT = "I" "N" "F" "I" "N" "I" "T" "Y"

NAN-LIT = "N" "A" "N"

HEADER-LIT = "H" "E" "A" "D" "E" "R"

SCHEMA-ID-LIT = "s" "c" "h" "e" "m" "a" "_" "i" "d"

SCHEMA-VERSION-LIT = "s" "c" "h" "e" "m" "a" "_" "v" "e" "r" "s" "i" "o" "n"

ORDERED-SCHEMA-LIT = "o" "r" "d" "e" "r" "e" "d"

LABELED-SCHEMA-LIT = "l" "a" "b" "e" "l" "e" "d"

START-LIT = "S" "T" "A" "R" "T"

METADATA-LIT = "M" "E" "T" "A" "D" "A" "T" "A"

OUTPUT-LIT = "O" "U" "T" "P" "U" "T"

BOOL-LIT = "B" "O" "O" "L"

INT-LIT = "I" "N" "T"

DOUBLE-LIT = "D" "O" "U" "B" "L" "E"

RESULT-LIT = "R" "E" "S" "U" "L" "T"

END-LIT = "E" "N" "D"
```
