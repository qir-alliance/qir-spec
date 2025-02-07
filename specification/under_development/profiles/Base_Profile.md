# Base Profile

This profile defines a subset of the QIR specification to support a coherent set
of functionalities and capabilities that might be offered by a quantum backend.
Like all profile specifications, this document is primarily intended for
[compiler backend](https://en.wikipedia.org/wiki/Compiler#Back_end) authors as
well as contributors to the [targeting
stage](../Compilation_And_Targeting.md#targeting) of the QIR compiler. For the
sake of comprehensiveness, it is written to be largely self-contained. While the
profile-specific restrictions defined in this document limit precisely what can
be used as part of an [entry point function](#entry-point-definition), they do
*not*, for example, limit how to call into such an entry point as part of a
larger [application](#glossary).

The Base Profile specifies the minimal requirements for executing a [quantum
program](#glossary). Specifically, to execute a Base Profile compliant program,
a backend needs to support the following:

1. It can execute a sequence of quantum instructions that transform the quantum
   state.
2. It supports measuring the state of each qubit at the end of the program.
3. It produces one of the specified [output schemas](../output_schemas/).

These functionalities are necessary and sufficient for computations that
fundamentally consist of unitary transformations of the quantum state as well as
measurements at the end of the program. More details about each of the bullets
are outlined below.

## Mandatory Capabilities

### Bullet 1: Quantum transformations

The set of available instructions that transform the quantum state may vary
depending on the targeted backend. The profile specification defines how to
leverage and combine the available instructions to express a program, but does
not dictate which quantum instructions may be used. Targeting a program to a
specific backend requires choosing a suitable profile and quantum instruction
set (QIS). Both can be chosen largely independently, though certain instruction
sets may be incompatible with this (or other) profile(s). The section on the
[quantum instruction set](#quantum-instruction-set) defines the requirements for
a QIS to be compatible with the Base Profile. More information about the role of
the QIS, recommendations for front- and backend providers, as well as the
distinction between runtime functions and quantum instructions can be found in
[this document](../Instruction_Set.md).

### Bullet 2: Measurements

The second requirement should be taken to mean that a Base Profile compliant
program does *not* apply instructions to a qubit after it has been measured;
instructions that result in a unitary transformation of the quantum state must
be applied before performing any irreversible actions such as measurements. It
specifically also implies the following:

- There is no need for the quantum processor ([QPU](../Execution.md)) to be able
to measure only a subset of all available qubits at a time.
- Executing a Base Profile compliant program does not require support for
applying quantum instructions dependent on measurement outcomes.

### Bullet 3: Program output

The QIR specification and its profiles describe a mechanism to accurately
reflect program intent with regard to program output. The Base Profile
specification requires explicitly defining program output by expressing which
values/measurements are returned by the program and in which order. How to
express this is defined in the section on [output recording](#output-recording).

While it is sufficient for the QPU to do a final measurement of all qubits in a
predefined order at the end of the program, only the selected subset will be
reflected in the produced output schema. A suitable output schema can be
generated during execution or in a post-processing step after the computation on
the quantum processor itself has completed; customization of the program output
hence does not require support on the QPU itself.

The defined [output schemas](../output_schemas/) provide different options for
how a backend may express the computed value(s). The exact schema can be freely
chosen by the backend and is identified by a string label in the produced
schema. Each output schema contains sufficient information to allow quantum
programming frameworks to generate a user-friendly presentation of the returned
values in the requested order, such as, e.g., a histogram of all results when
running the program multiple times.

## Program Structure

A Base Profile compliant program is defined in an LLVM bitcode file that
contains (at least) the following:

- the definitions of the opaque `Qubit` and `Result` types
- global constants that store [string labels](#output-recording) needed for
  certain output schemas that may be ignored if the [output
  schema](../output_schemas/) does not make use of them
- the [entry point definition](#entry-point-definition) that contains the
  program logic
- declarations of the [QIS functions](#quantum-instruction-set) used by the
  program
- declarations of [runtime functions](#runtime-functions) used for
  initialization and output recording
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
These differences are irrelevant when using standard tools to load, manipulate,
and/or execute bitcode.

The code below illustrates how a simple program looks within a Base Profile
representation:

```llvm
; type definitions

; global constants (labels for output recording)

@0 = internal constant [3 x i8] c"r1\00"
@1 = internal constant [3 x i8] c"r2\00"

; entry point definition

define i64 @Entry_Point_Name() #0 {
entry:
  ; calls to initialize the execution environment
  call void @__quantum__rt__initialize(ptr null)
  br label %body

body:                                     ; preds = %entry
  ; calls to QIS functions that are not irreversible
  call void @__quantum__qis__h__body(ptr null)
  call void @__quantum__qis__cnot__body(ptr null, ptr inttoptr (i64 1 to ptr))
  br label %measurements

measurements:                             ; preds = %body
  ; calls to QIS functions that are irreversible
  call void @__quantum__qis__mz__body(ptr null, ptr writeonly null)
  call void @__quantum__qis__mz__body(ptr inttoptr (i64 1 to ptr), ptr writeonly inttoptr (i64 1 to ptr))
  br label %output

output:                                   ; preds = %measurements
  ; calls to record the program output
  call void @__quantum__rt__tuple_record_output(i64 2, ptr null)
  call void @__quantum__rt__result_record_output(ptr null, getelementptr inbounds ([3 x i8], ptr @0, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(ptr inttoptr (i64 1 to ptr), getelementptr inbounds ([3 x i8], ptr @1, i32 0, i32 0))

  ret i64 0
}

; declarations of QIS functions

declare void @__quantum__qis__h__body(ptr)

declare void @__quantum__qis__cnot__body(ptr, ptr)

declare void @__quantum__qis__mz__body(ptr, ptr writeonly) #1

; declarations of runtime functions for initialization and output recording

declare void @__quantum__rt__initialize(ptr)

declare void @__quantum__rt__tuple_record_output(i64, ptr)

declare void @__quantum__rt__result_record_output(ptr, ptr)

; attributes

attributes #0 = { "entry_point" "qir_profiles"="base_profile" "output_labeling_schema"="schema_id" "required_num_qubits"="2" "required_num_results"="2" }

attributes #1 = { "irreversible" }

; module flags

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 2}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
```

The program entangles two qubits, measures them, and records a tuple with the
two measurement results.

For the sake of clarity, the code above does not contain any [debug
symbols](https://releases.llvm.org/13.0.0/docs/tutorial/MyFirstLanguageFrontend/LangImpl09.html?highlight=debug%20symbols).
Debug symbols contain information that is used by a debugger to relate failures
during execution back to the original source code. While we expect this to be
primarily useful for execution on simulators, debug symbols are both easy to
ignore and may be useful to generate helpful error messages for compilation
failures that happen only late in the process. We hence see no reason to
disallow them from occurring in the bitcode but will not detail their use any
further. We defer to existing resources for more information about how to
generate and use debug symbols.

## Entry Point Definition

The bitcode contains the definition of the LLVM function that will be invoked
when a [quantum program](#glossary) is executed, referred to as the module's
"entry point" in the rest of this profile specification. The name of this
function may be chosen freely, as long as it is a valid [global
identifier](https://llvm.org/docs/LangRef.html#identifiers) according to the
LLVM standard. Entry points are identified by a custom function attribute; the
section on [attributes](#attributes) defines which attributes must be attached
to an entry point function.

A Base Profile compliant entry point may not take any parameters and must return
an exit code in the form of a 64-bit integer. The exit code `0` must be used to
indicate a successful execution of the quantum program.

The body of an entry point function consists of four [basic
blocks](https://en.wikipedia.org/wiki/Basic_block), connected by an
unconditional branching that terminates a block and defines the next block to
execute, i.e., its successor. Execution starts at the entry block and follows
the [control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph)
defined by the block terminators. Block names/block identifiers may be chosen
arbitrarily, and the order in which blocks are listed in the function definition
may deviate from the [example above](#program-structure). The final block is
terminated by a `ret` instruction to exit the function and return the exit code.

The entry block contains the necessary call(s) to initialize the execution
environment. In particular, it must ensure that all used qubits are set to a
zero-state. The section on [initialization functions](#initialization) defines
how to do that.

The successor of the entry block continues with the main program logic. This
logic is split into two blocks, separated again by an unconditional branch from
one to the other. Both blocks consist (only) of calls to [QIS
functions](#quantum-instruction-set). Any number of such calls may be performed.
To be compatible with the Base Profile the called functions must return void.
Any arguments to invoke them must be inlined into the call itself; they must be
constants or pointers of type `ptr`.

The only difference between these two blocks is that the first one contains only
calls to functions that are *not* marked as irreversible by an attribute on the
respective function declaration, whereas the second one contains only calls to
functions that perform irreversible actions, i.e. measurements of the quantum
state. The section on the [quantum instruction set](#quantum-instruction-set)
defines the requirement(s) regarding the use of the `irreversible` attribute,
and the section on [qubit and result usage](#qubit-and-result-usage) details
additional restrictions for using qubits and result values.

The final block contains (only) the necessary calls to record the program
output, as well as the `ret` instruction that terminates the block and returns
the exit code. The logic of this block can be done as part of post-processing
after the computation on the QPU has completed, provided the results of the
performed measurements are made available to the processor generating the
requested output. More information about the [output
recording](#output-recording) is detailed in the section about [runtime
functions](#runtime-functions).

## Quantum Instruction Set

For a quantum instruction set to be fully compatible with the Base Profile, it
must satisfy the following three requirements:

- All functions must return `void`; the Base Profile does not permit to call
  functions that return a value. Functions that measure qubits must take the
  qubit pointer(s) as well as the result pointer(s) as arguments.

- Functions that perform a measurement of one or more qubit(s) must be marked
  with an custom function attribute named `irreversible`. The use of
  [attributes](#attributes) in general is outlined in the corresponding section.

- Parameters of type `ptr` identifying results must be `writeonly` parameters;
  only the runtime function `__quantum__rt__result_record_output` used for [output
  recording](#output-recording) may read a measurement result.

For more information about the relation between a profile specification and the
quantum instruction set we refer to the paragraph on [Bullet 1](#base-profile)
in the introduction of this document. For more information about how and when
the QIS is resolved, as well as recommendations for front- and backend
developers, we refer to the document on [compilation stages and
targeting](../Compilation_And_Targeting.md).

## Classical Instructions

The following instructions are the *only* LLVM instructions that are permitted
within a Base Profile compliant program:

| LLVM Instruction         | Context and Purpose                                                                              | Rules for Usage                                                                                             |
| :----------------------- | :----------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a basic block to invoke any one of the declared QIS functions and runtime functions. | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction).       |
| `br`                     | Used to branch from one basic block to another.                                                  | The branching must be unconditional and occurs as the final instruction of a block to jump to the next one. |
| `ret`                    | Used to return the exit code of the program.                                                     | Must occur (only) as the last instruction of the final block in an entry point.                             |
| `inttoptr`               | Used to cast an `i64` integer value to a `ptr`.                                                  | May be used as part of a function call only.                                                                |
| `getelementptr inbounds` | Used to create a `ptr` to pass a constant string for the purpose of labeling an output value.    | May be used as part of a call to an output recording function only.                                         |

See also the section on [data types and values](#data-types-and-values) for more
information about the creation and usage of LLVM values.

## Runtime Functions

The following runtime functions must be supported by all backends, and are the
only runtime functions that may be used as part of a Base Profile compliant
program:

| Function                            | Signature            | Description                                                                                                                                                                                                                                                  |
| :---------------------------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__initialize           | `void(ptr)`          | Initializes the execution environment. Sets all qubits to a zero-state if they are not dynamically managed.                                                                                                                                                  |
| __quantum__rt__tuple_record_output  | `void(i64,ptr)`      | Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.  |
| __quantum__rt__array_record_output  | `void(i64,ptr)`      | Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__result_record_output | `void(ptr,ptr)` | Adds a measurement result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |

### Initialization

*A [workstream](https://github.com/qir-alliance/qir-spec/issues/11) to specify
how to initialize the execution environment is currently in progress. As part of
that workstream, this paragraph and the listed initialization function(s) will
be updated.*

### Output Recording

The output of a quantum program is defined by a sequence of calls to runtime
functions that record the values produced by the computation, specifically calls
to the runtime functions ending in `record_output` listed in the table
[above](#runtime-functions). In the case of the Base Profile, these calls are
contained within the final block of an entry point function, i.e. the block that
terminates in a return instruction.

For all output recording functions, the `ptr` argument must be a non-null
pointer to a global constant that contains a null-terminated string. A unique
string must be used for each call to an output recording function within the
same entry point. A backend may ignore that argument if it guarantees that the
order of the recorded output matches the order defined by the quantum program.
Conversely, certain output schemas do not require the recorded output to be
listed in a particular order. For those schemas, the `ptr` argument serves as a
label that permits the compiler or tool that generated the labels to reconstruct
the order intended by the program. [Compiler
frontends](https://en.wikipedia.org/wiki/Compiler#Front_end) must always
generate these labels in such a way that the bitcode does not depend on the
output schema; while choosing how to best label the program output is up to the
frontend, the choice of output schema on the other hand is up to the backend. A
backend may reject a program as invalid or fail execution if a label is missing.

Both the labeling schema and the output schema are identified by a metadata
entry in the produced output. For the [output schema](../output_schemas/), that
identifier matches the one listed in the corresponding specification. The
identifier for the labeling schema, on the other hand, is defined by the value
of the `"output_labeling_schema"` attribute attached to the entry point.

## Data Types and Values

Within the Base Profile, defining local variables is not supported; instructions
cannot be nested and constant expressions are fully evaluated. This implies the
following:

- Call arguments must be constant values, and `inttoptr` casts as well as
  `getelementptr` instructions must be inlined into a call instruction.
- It is not possible to express classical computations, such as adding two
  double values, as part of a Base Profile compliant program.

Constants of any type are permitted as part of a function call. What data types
occur in the program hence depends on what QIS functions are used in addition to
the runtime functions for initialization and output recording. Constant values
of type `i64` in particular may be used as part of calls to output recording
functions; see the section on [output recording](#output-recording) for more
details.

The `ptr` data types must be supported by all backends.
Qubits and results can occur only as arguments in function calls and are
represented as a pointer type, where
the pointer itself identifies the qubit or result value rather than a memory
location where the value is stored: a 64-bit integer constant is cast to the
appropriate pointer type. A more detailed elaboration on the purpose of this
representation is given in the next subsection. The integer constant that is
cast must be in the interval `[0, numQubits)` for qubits and `[0,
numResults)` for results, where `numQubits` and `numResults` are the required
number of qubits and results defined by the corresponding [entry point
attributes](#attributes). Since backends may look at the values of the
`required_num_qubits` and `required_num_results` attributes to determine whether
a program can be executed, it is recommended to index qubits and results
consecutively so that there are no unused values within these ranges.

### Qubit and Result Usage

Qubits and result values are represented as opaque pointers in the bitcode,
which may only ever be dereferenced as part a runtime function implementation.
In general, the QIR specification distinguishes between two kinds of pointers
for representing a qubit or result value, as explained in more detail
[here](../Execution.md), and either one, though not both, may be used throughout
a bitcode file. A [module flag](#module-flags-metadata) in the bitcode indicates
which kinds of pointers are used to represent qubits and result values.

The first kind of pointer points to a valid memory location that is managed
dynamically during program execution, meaning the necessary memory is allocated
and freed by the runtime. The second kind of pointer merely identifies a qubit
or result value by a constant integer encoded in the pointer itself. To be
compliant with the Base Profile specification, the program must not make use of
dynamic qubit or result management, meaning it must use only the second kind of
pointer; qubits and results must be identified by a constant integer value that
is bitcast to a pointer to match the expected type. How such an integer value is
interpreted and specifically how it relates to hardware resources is ultimately
up to the executing backend.

Additionally, the Base Profile imposes the following restrictions on qubit and
result usage:

- Qubits must not be used after they have been passed as arguments to a function
  that performs an irreversible action. Such functions are marked with the
  `irreversible` attribute in their declaration.

- Results can only be used either as `writeonly` arguments, or as arguments to
  [output recording functions](#output-recording). We refer to the [LLVM
  documentation](https://llvm.org/docs/LangRef.html#function-attributes)
  regarding how to use the `writeonly` attribute.

## Attributes

The following custom attributes must be attached to an entry point function:

- An attribute named `"entry_point"` identifying the function as the starting
  point of a quantum program
- An attribute named `"qir_profiles"` with the value `"base_profile"`
  identifying the profile the entry point has been compiled for
- An attribute named `"output_labeling_schema"` with an arbitrary string value
  that identifies the schema used by a [compiler
  frontend](https://en.wikipedia.org/wiki/Compiler#Front_end) that produced the
  IR to label the recorded output
- An attribute named `"required_num_qubits"` indicating the number of qubits
  used by the entry point
- An attribute named `"required_num_results"` indicating the maximal number of
  measurement results that need to be stored while executing the entry point
  function

Optionally, additional attributes may be attached to the entry point. Any custom
function attributes attached to an entry point should be reflected as metadata
in the program output; this includes both mandatory and optional attributes but
not parameter attributes or return value attributes. This in particular implies
that the [labeling schema](#output-recording) used in the recorded output can be
identified by looking at the metadata in the produced output. See the
specification of the [output schemas](../output_schemas/) for more information
about how metadata is represented in the output schema.

Custom function attributes will show up as part of an [attribute
group](https://releases.llvm.org/13.0.1/docs/LangRef.html#attrgrp) in the IR.
Attribute groups are numbered in such a way that they can be easily referenced
by multiple function definitions or global variables. Consumers of Base Profile
compliant programs must not rely on a particular numbering, but instead look for
functions to which an attribute with the name `"entry_point"` is attached to
determine which function to invoke to execute a quantum program.

Both the `"entry_point"` attribute and the `"output_labeling_schema"` attribute
can only be attached to a function definition; they are invalid on a function
that is declared but not defined.

Within the restrictions imposed by the Base Profile, the number of qubits that
are needed to execute a quantum program must be known at compile time. This
number is captured in the form of the `"required_num_qubits"` attribute attached
to the entry point. The value of the attribute must be the string representation
of a non-negative 64-bit integer constant.

Similarly, the number of measurement results that need to be stored when
executing the entry point function is captured by the `"required_num_results"`
attribute. Since qubits cannot be used after measurement in the case of the Base
Profile, this value is usually equal to the number of measurement results in the
program output.

Beyond the entry point specific requirements related to attributes, custom
attributes may optionally be attached to any of the declared functions. The
`irreversible` attribute in particular impacts how the program logic in a Base
Profile compliant entry point is structured, as described in the section about
the [entry point definition](#entry-point-definition). Furthermore, the
following [LLVM
attributes](https://llvm.org/docs/LangRef.html#function-attributes) may be used
according to their intended purpose on function declarations and call sites:
`inlinehint`, `nofree`, `norecurse`, `readnone`, `readonly`, `writeonly`, and
`argmemonly`.

## Module Flags Metadata

The following [module
flags](https://llvm.org/docs/LangRef.html#module-flags-metadata) must be present
within the QIR bitcode:

- a flag with the string identifier `"qir_major_version"` that contains a
  constant value of type `i32`
- a flag with the string identifier `"qir_minor_version"` that contains a
  constant value of type `i32`
- a flag with the string identifier `"dynamic_qubit_management"` that contains a
  constant `true` or `false` value of type `i1`
- a flag with the string identifier `"dynamic_result_management"` that contains
  a constant `true` or `false` value of type `i1`

These flags are attached as `llvm.module.flags` metadata to the module. They can
be queried using the standard LLVM tools and follow the LLVM specification in
behavior and purpose. Since module flags impact whether different modules can be
merged and how, additional module flags may be added to the bitcode only if
their behavior is set to `Warning`, `Append`, `AppendUnique`, or `Max`. It is at
the discretion of the maintainers for various components in the QIR stack to
discard module flags that are not explicitly required or listed as optional
flags in the QIR specification.

### Specification Version

The required flags `"qir_major_version"` and `"qir_minor_version"` identify the
major and minor version of the specification that the QIR bitcode adheres to.

- Since the QIR specification may introduce breaking changes when updating to a
  new major version, the behavior of the `"qir_major_version"` flag must be set
  to `Error`; merging two modules that adhere to different major versions must
  fail.

- The QIR specification is intended to be backward compatible within the same
  major version, but may introduce additional features as part of newer minor
  versions. The behavior of the `"qir_minor_version"` flag must hence be `Max`,
  so that merging two modules compiled for different minor versions results in a
  module that adheres to the newer of the two versions.

### Memory Management

Each bitcode file contains the information whether instances of `ptr` used for
qubits and results point to a valid memory location, or whether a pointer merely
encodes an integer constant that identifies which qubit or result the value
refers to. This information is represented in the form of the two module flags
named `"dynamic_qubit_management"` and `"dynamic_result_management"`. Within the
same bitcode module, there can never be a mixture of the two different kinds of
pointers. The behavior of both module flags correspondingly must be set to
`Error`. As detailed in the section on [qubit and result
usage](#qubit-and-result-usage), a Base Profile compliant program must not make
use of dynamic qubit or result management. The value of both module flags hence
must be set to `false`.

## Glossary

**Quantum application:** <br/>
A piece of software that performs a specific task and/or solves a specific
problem using both quantum and classical resources to do so. Executing a quantum
application usually involves accessing quantum resources via a cloud service,
and quantum resources are generally available only for parts of the computation;
a QPU does not retain its state for the entirety of the application execution.

**Quantum program:** <br/>
A computation that includes both quantum and (potentially limited) classical
logic. The program logic is defined in the form of an LLVM function marked as
[entry point](https://en.wikipedia.org/wiki/Entry_point) by an attribute. Both
classical and quantum processors executing the program retain their state
throughout its execution, such that it is possible to access and (repeatedly)
transfer values/data between different processors as part of the computation.
