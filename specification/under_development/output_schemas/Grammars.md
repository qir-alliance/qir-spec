# ABNF Grammars For Schema Definitions

The ABNF grammars for the [Labeled and Async](./Labeled_And_Async.md) and [No Labels and Ordered](./No_Labels_And_Ordered.md) define the technical content of the files. The details of the QIR calls and how they map to the input is coverred in the associated specifications. Type consistency cannot be defined for array elements and is a validation concern when consuming output.

## Grammars

### Shared Top Level

The grammars share a basic structure and only vary in their definition of values, tuples, and arrays. The top level definitions are the same:

```abnf
file = shot *(EOL shot) [EOL]

shot = start *(EOL record) EOL end

record = metadata / output

metadata = METADATA-LIT TAB field [TAB field]

output = (container / value)

container = (tuple / array)
```

### Labeled and Async:

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

TEXTDATA = %x20-21 / %x23-7E

DIGIT = %x30-39

BIT = "0" / "1"

start = START-LIT

end = END-LIT TAB "0"

TRUE-LIT = "T" "R" "U" "E"

FALSE-LIT = "F" "A" "L" "S" "E"

INF-LIT = "I" "N" "F"

INFINITY-LIT = "I" "N" "F" "I" "N" "I" "T" "Y"

NAN-LIT = "N" "A" "N"

START-LIT = "S" "T" "A" "R" "T"

METADATA-LIT = "M" "E" "T" "A" "D" "A" "T" "A"

OUTPUT-LIT = "O" "U" "T" "P" "U" "T"

BOOL-LIT = "B" "O" "O" "L"

INT-LIT = "I" "N" "T"

DOUBLE-LIT = "D" "O" "U" "B" "L" "E"

RESULT-LIT = "R" "E" "S" "U" "L" "T"

END-LIT = "E" "N" "D"
```