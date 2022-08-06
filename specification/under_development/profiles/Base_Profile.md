# Base Profile

This profile defines a subset of the QIR specification to support a coherent set
of functionalities and capabilities that might be offered by a quantum backend.
Like all profile specifications, this document is primarily intended for
[compiler backend](https://en.wikipedia.org/wiki/Compiler#Back_end) authors as
well as contributors to the [targeting
stage](../Compilation_And_Targeting.md#targeting) of the QIR compiler.

The Base Profile specifies the minimal requirements for executing a quantum
program. Specifically, to execute a Base Profile compliant program, a backend
needs to support the following:

1. It can execute a sequence of quantum instructions that transform the quantum
   state.
2. It supports measuring the state of each qubit at the end of the program.
3. It produces one of the specified [output formats](../output_formats/).

These functionalities are both necessary and sufficient for computations that
fundamentally consist of unitary transformations of the quantum state as well as
measurements at the end of the program. More details about each of the bullets
are outlined below.

**Bullet 1: Quantum transformations** <br/>

The set of available instructions that transform the quantum state may vary
depending on the targeted backend. The profile specification defines how to
leverage and combine the available instructions to express a program, but does
not dictate which quantum instructions may be used. Targeting a program to a
specific backend requires choosing a suitable profile and quantum instruction
set (QIS). Both can be chosen largely independently, though certain instruction
sets may be incompatible with this (or other) profile(s). The section on the
[quantum instruction set](#quantum-instruction-set) below defines the criterion
for a QIS to be compatible with the Base Profile. More information about the
role of the QIS, recommendations for front- and backend providers, as well as
the distinction between runtime functions and quantum instructions can be found
in [Instruction_Set.md](../Instruction_Set.md).

**Bullet 2: Measurements** <br/>

The second requirement should be taken to mean that a Base Profile compliant
program does *not* apply instructions to a qubit after it has been measured; all
instructions to transform the quantum state can be applied before performing any
measurements. It specifically also implies the following:

- There is no need for the quantum processor ([QPU](../Execution.md)) to be able
to measure only a subset of all available qubits at a time.
- Executing a Base Profile compliant program does not require support for
applying quantum instructions dependent on measurement outcomes.

**Bullet 3: Program output** <br />

The specification of QIR and all its profiles needs to permit to accurately
reflect the program intent. This includes being able to define and customize the
program output. The Base Profile specification hence requires explicitly
expressing which values/measurements are returned by the program and in which
order. How to express this is defined in the section on [output
recording](#output-recording).

While it is sufficient for the QPU to do a final measurement of all qubits in a
predefined order at the end of the program, only the selected subset will be
reflected in the produced output format. A suitable output format can be
generated in a post-processing step after the computation on the quantum
processor itself has completed; customization of the program output hence does
not require support on the QPU itself.

The defined [output formats](../output_formats/) provide different options for
how a backend may express the computed value(s). The exact format can be freely
chosen by the backend and is identified by a string label in the produced
format. Each output format contains sufficient information to allow quantum
programming frameworks to generate a user friendly presentation of the returned
values in the requested order, such as, e.g., a histogram of all results when
running the program multiple times.

## Program Structure

A Base Profile compliant program is defined in the form of a single LLVM bitcode
file that contains the following:

- the definitions of the opaque `Qubit` and `Result` types
- global constants that store [string
  labels](#string-labels-for-output-recording) needed for certain output formats
  that may be ignored if the [output format](../output_formats/) does not make
  use of them
- the [entry point definition](#entry-point-definition) that contains the
  program logic
- declarations of the [QIS functions](#quantum-instruction-set) used by the
  program
- declarations of functions used for [output recording](#output-recording)
- one or more [attribute groups](#attributes) used to store information about
  the entry point, and optionally additional information about other function
  declarations
- [module flags](#module-flags-metadata) that contain information that a
  compiler or backend may need to process the bitcode.

The human readable LLVM IR for the bitcode can be obtained using standard [LLVM
tools](https://llvm.org/docs/CommandGuide/llvm-dis.html). For the purpose of
clarity, this specification contains examples of the human readable IR emitted
by [LLVM 13](https://releases.llvm.org/13.0.1/docs/LangRef.html). While the
bitcode representation is portable and usually backward compatible, there may be
visual differences in the human readable format depending on the LLVM version.
This differences are irrelevant when using standard tools to load, manipulate,
and/or execute bitcode.

The code below illustrates how a simple program looks like within a Base Profile
representation:

```llvm
; type definitions

%Result = type opaque
%Qubit = type opaque

; global constants (labels for output recording)

@0 = internal constant [3 x i8] c"r1\00"
@1 = internal constant [3 x i8] c"r2\00"

; entry point definition

define i64 @Entry_Point_Name() #0 {
entry:

  ; calls to QIS functions
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))
  br label %output

output:                                   ; preds = %entry
  ; calls to record the program output
  tail call void @__quantum__rt__tuple_record_output(i64 2, i8* null)
  tail call void @__quantum__rt__result_record_output(%Result* null, i8* getelementptr inbounds ([3 x i8], [3 x i8]* @0, i32 0, i32 0))
  tail call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* getelementptr inbounds ([3 x i8], [3 x i8]* @1, i32 0, i32 0))

  ret i64 0
}

; declarations of QIS functions

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result*)

; declarations of functions used for output recording

declare void @__quantum__rt__tuple_record_output(i64, i8*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

; attributes

attributes #0 = { "entry_point" "qir_profile"="base_profile" "output_tags"="schema_id" "required_qubits"="2" "required_results"="2" }

; module flags

!llvm.module.flags = !{!0, !1, !2}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"manage_quantum_memory", i1 false}
```

The program entangles two qubits, measures them, and returns a tuple with the
two measurement results.

For the sake of clarity, the code above does not contain any [debug
symbols](https://releases.llvm.org/13.0.0/docs/tutorial/MyFirstLanguageFrontend/LangImpl09.html?highlight=debug%20symbols).
Debug symbols contain information that is used by a debugger to related failures
during execution back to the original source code. While we expect this to be
primarily useful for execution on simulators, debug symbols are both easy to
ignore and may be useful to generate helpful error messages for compilation
failures that happen only late in the process. We hence see no reason to
explicitly disallow them from occurring in the bitcode but will not detail their
use any further. We defer to existing resources for more information about how
to generate and use debug symbols.

## Entry Point Definition

TODO: adjust text to reflect the split into different blocks

The bitcode contains the definition of the LLVM function that should be invoked
when the program is executed, referred to as entry point in the rest of this
profile specification. The name of this function may be chosen freely, as long
as it is a valid [global
identifier](https://llvm.org/docs/LangRef.html#identifiers) by LLVM standard.

The entry point may not take any parameters and must return an exit code in the
form of a 64-bit integer. The exit code 0 must be used to indicate a successful
execution of the program.

LLVM get blocks with no successors:
<https://llvm.org/docs/ProgrammersManual.html#iterating-over-predecessors-successors-of-blocks>

### Attributes

The following custom attributes must be attached to the entry point function:

- An attribute named "entry_point" that does not
- An attribute indicating the total number of qubits used by the program
- An attribute indicating the total number of classical bits required throughout
  the program to store measurement outcomes

These attributes will show up as an [attribute
group](https://releases.llvm.org/13.0.1/docs/LangRef.html#attrgrp) in the IR.
Attribute groups are numbered such that they can be easily referenced by
multiple function definitions or global variables. Arbitrary custom attributes
may be optionally attached to any of the declared functions to convey additional
information about that function. Consumers of Base Profile compliant programs
should hence not rely on the numbering of the entry point attribute group, but
instead look for function to which an attribute with the name `entry_point` is
attached to determine which one to invoke when the program is launched.

To indicate the total number of qubits required to execute the program, a custom
attribute with the name `required_qubits` is defined and attached to the entry
point. To indicate the number of registers/bits needed to store measurement
results during program execution, a custom attribute with the name
`required_results` is defined and attached to the entry point. The value of both
of these attributes is the string representation of a 64-bit integer constant.

TODO: why the string value, and not an integer? Naming convention for attributes
like for qis?

TODO: profile attribute TODO: output tags schema id

### Function Body

The function body consists of three blocks; ...  Only trivial branching is
permitted inside a function's body. In the `entry` block, any number of calls to
QIS functions may be performed. To be compatible with the Base Profile these
functions must return void. Any arguments to invoke them must be inlined into
the call itself; they hence must be constants or a pointer to a [qubit or
result](#qubit-and-result-usage) The result of the program execution should be
logged using output recording functions.

The following instructions are the *only* LLVM instructions that are permitted
within a Base Profile compliant program:

| LLVM Instruction         | Context and Purpose                                                                                              | Rules for Usage                                                                                       |
| :----------------------- | :--------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a function block to invoke any one of the declared QIS functions and the output recording functions. | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction). |
| `ret`                    | Used to return the exit code of the program.                                                                     | Must occur (only) as the final instruction of the `entry` block.                                      |
| `inttoptr`               | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`.                                       | May be used as part of a function call only.                                                          |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value.                   | May be used as part of call to an output recording function only.                                     |

## Data Types and Values

Within the base profile, defining local variables is not supported. Arguments to
calls correspondingly are expected to be constant values.

Qubits and results are passes as a pointer of type `%Qubit*` and `%Result*`
respectively, where the pointer itself rather than the memory location
identifies the qubit or result: For the purpose of passing them as arguments in
function calls, a 64-bit signed integer value is cast to the appropriate pointer
type. The signed integer that is case must be in the interval `[0, nrQubits)`
for `%Qubit*` and `[0, nrResults)` for `%Result*`, where `nrQubits` and
`nrResults` are the required number of qubits and results defined by entry point
attributes.

Only the `%Qubit` and `%Result` data types are required to be supported by all
backends.

Integers and double-precision floating point numbers are available as in full
QIR; however, computations using these numeric types are not available.

### Qubit and Result Usage

runtime has autonomy over how to represent qubits. also for base profile, the
runtime is the only entity that needs to know how to interpret the opaque
pointers (deref or not). that info is captured in the target triple/duo.

Qubits may not be used after they have been measured. Qubits and results need to
be numbered consecutively, starting at 0. Measurements may only be followed by
other measurements or output recording functions.

## Quantum Instruction Set

For a Quantum Instruction Set to be compatible with the Base Profile, it needs
to satisfy the following requirements:

- Since the Base Profile doesn't permit to define local variables, all
  instructions are required to return void.

## Output Recording

Log format is a separate spec. What the i8* can be is a separate spec. Default
spec for [frontends](https://en.wikipedia.org/wiki/Compiler#Front_end) to
compile into. String labels are zero terminated.

The following functions are declared and used to record the program output:

| Function                            | Signature             | Description                                                                                                                                                                                                                                                                                             |
| :---------------------------------- | :-------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| __quantum__rt__record_output        | `void(i8*)`           | Inserts a marker in the output log that contains an identifier for the used labeling scheme. The backend may choose which output format to use, and the label identifier is omitted for output formats that do not support labeling.                                                                    |
| __quantum__rt__tuple_record_output  | `void(i64, i8*)`      | Inserts a marker in the output log that indicates the start of a tuple and how many tuple elements are going to be logged. The second parameter reflects an label for the tuple. The backend may choose which output format to use. Depending on the used format, the label will be logged or omitted.  |
| __quantum__rt__array_record_output  | `void(i64, i8*)`      | Inserts a marker in the output log that indicates the start of an array and how many array elements are going to be logged. The second parameter reflects an label for the array. The backend may choose which output format to use. Depending on the used format, the label will be logged or omitted. |
| __quantum__rt__result_record_output | `void(%Result*, i8*)` | Adds a measurement result to the output log. The second parameter reflects an label for the result value. The backend may choose which output format to use. Depending on the used format, the label will be logged or omitted.                                                                         |

It is sufficient to use the same functions for output recording independent on
the output format; i.e. the output format does not need to be reflected in the
IR, and it is sufficient to label the format it in the output itself. The output
itself then needs to contain both the output format identifier (defined by the
backend), as well as an identifier for the labeling scheme (as defined in the
program IR itself). -> for base profile, no computations (classical or quantum,
including calls to rt functions other than record_output* functions) can be
performed after the call to __quantum__rt__record_output

record output functions may only occur in the last block of an entry point,
where last here means no successor

### String Labels for Output Recording

## Module Flags Metadata

backends may fail if a label is missing that it needs
major version needs to agree, minor version is taken the max of both

see also <https://llvm.org/docs/LangRef.html#module-flags-metadata>
