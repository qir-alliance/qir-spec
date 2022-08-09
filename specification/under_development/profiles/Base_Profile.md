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
3. It produces one of the specified [output schemas](../output_schemas/).

These functionalities are necessary and sufficient for computations that
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
[quantum instruction set](#quantum-instruction-set) below defines the
requirements for a QIS to be compatible with the Base Profile. More information
about the role of the QIS, recommendations for front- and backend providers, as
well as the distinction between runtime functions and quantum instructions can
be found in [this document](../Instruction_Set.md).

**Bullet 2: Measurements** <br/>

The second requirement should be taken to mean that a Base Profile compliant
program does *not* apply instructions to a qubit after it has been measured; all
instructions to transform the quantum state must be applied before performing
any measurements. It specifically also implies the following:

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
reflected in the produced output schema. A suitable output schema can be
generated in a post-processing step after the computation on the quantum
processor itself has completed; customization of the program output hence does
not require support on the QPU itself.

The defined [output schemas](../output_schemas/) provide different options for
how a backend may express the computed value(s). The exact schema can be freely
chosen by the backend and is identified by a string label in the produced
schema. Each output schema contains sufficient information to allow quantum
programming frameworks to generate a user-friendly presentation of the returned
values in the requested order, such as, e.g., a histogram of all results when
running the program multiple times.

## Program Structure

A Base Profile compliant program is defined in the form of a single LLVM bitcode
file that contains the following:

- the definitions of the opaque `Qubit` and `Result` types
- global constants that store [string labels](#output-recording) needed for
  certain output formats that may be ignored if the [output
  schema](../output_schemas/) does not make use of them
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
These differences are irrelevant when using standard tools to load, manipulate,
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
  tail call void @__quantum__qis__mz__body(%Qubit* null, writeonly %Result* null)
  tail call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), writeonly %Result* inttoptr (i64 1 to %Result*))
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

declare void @__quantum__qis__mz__body(%Qubit*, writeonly %Result*)

; declarations of functions used for output recording

declare void @__quantum__rt__tuple_record_output(i64, i8*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

; attributes

attributes #0 = { "entry_point" "qir_profile"="base_profile" "output_labels"="schema_id" "required_qubits"="2" "required_results"="2" }

; module flags

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
```

The program entangles two qubits, measures them, and returns a tuple with the
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

The bitcode contains the definition of the LLVM function that should be invoked
when the program is executed, referred to as "entry point" in the rest of this
profile specification. The name of this function may be chosen freely, as long
as it is a valid [global
identifier](https://llvm.org/docs/LangRef.html#identifiers) by LLVM standard.

The entry point may not take any parameters and must return an exit code in the
form of a 64-bit integer. The exit code `0` must be used to indicate a
successful execution of the program.

### Attributes

The following custom attributes must be attached to the entry point function:

- An attribute named `"entry_point"` identifying the function as the starting
  point of a quantum program
- An attribute named `"qir_profile"` with the value `"base_profile"` identifying
  the profile the entry point has been compiled for
- An attribute named `"output_labels"` with an arbitrary string value that
  identifies the schema used by a [compiler
  frontend](https://en.wikipedia.org/wiki/Compiler#Front_end) that produced the
  IR to label the recorded output
- An attribute named `"required_qubits"` indicating the number of qubits used by
  the entry point
- An attribute named `"required_results"` indicating the maximal number of
  measurement results that need to be stored while executing the entry point
  function

Optionally, additional attributes may be attached to the entry point. Any custom
function attributes attached to the entry point will be reflected as metadata in
the program output; this includes both mandatory and optional attributes but not
parameter attributes or return value attributes. This in particular implies that
the [labeling schema](#output-recording) used in the recorded output can be
identified by looking at the metadata in the produced output. See the
specification of the [output schemas](../output_schemas/) for more information
about how metadata is represented in the output schema.

Custom function attributes will show up as part of an [attribute
group](https://releases.llvm.org/13.0.1/docs/LangRef.html#attrgrp) in the IR.
Attribute groups are numbered such that they can be easily referenced by
multiple function definitions or global variables. Consumers of Base Profile
compliant programs must not rely on a particular numbering, but instead look for
the function to which an attribute with the name `"entry_point"` is attached to
determine which one to invoke when the program is launched.

Within the restrictions imposed by the Base Profile, the number of qubits that
are needed to execute the quantum program must be known at compile time. This
number is captured in the form of the `"required_qubits"` attribute attached to
the entry point. The value of the attribute must be the string representation of
a 64-bit integer constant.

Similarly, the number of measurement results that need to be stored when
executing the entry point function is captured by the `"required_results"`
attribute. Since qubits cannot be used after measurement, in the case of the
Base Profile, this value is equal to the number of measurement results in the
program output.

For a program to be valid, both the number of qubits used and the number of
measurements to store must be strictly positive. More details on the usage of
[qubits and results](#qubit-and-result-usage) in general can be found in the
sections below.

Beyond the entry point specific requirements related to attributes, custom
attributes may optionally be attached to any of the declared functions.
Furthermore, the following [LLVM
attributes](https://llvm.org/docs/LangRef.html#function-attributes) may be used
according to their intended purpose on function declarations and call sites:
`inlinehint`, `nofree`, `norecurse`, `readnone`, `readonly`, `writeonly`, and
`argmemonly`.

### Function Body

The function body consists of two blocks, connected by an unconditional
branching into the second block at the end of the first block.

The first block contains only calls to QIS functions. Any number of calls to QIS
functions may be performed. To be compatible with the Base Profile these
functions must return void. Any arguments to invoke them must be inlined into
the call itself; they must be constants or a pointer representing a [qubit or
result](#data-types-and-values) value. All function calls leading to a unitary
transformation of the quantum state must precede any measurements; any calls
that perform a measurement of one or more qubit(s) can only be followed by other
such calls or the block terminating branching into the second block. The section
detailing [qubit and result usage](#qubit-and-result-usage) outlines which
instructions qualify as performing measurements, and defines additional
restrictions for using qubit and result values.

The second and last block contains (only) the necessary calls to record the
program output, as well as the block terminating return instruction that return
the exit code. The logic of the second block can be done as part of
post-processing after the computation on the QPU has completed, provided the
results of the performed measurements is made available to the processor
generating the requested output. More information about the [output
recording](#output-recording) and the corresponding runtime functions is
detailed below.

The following instructions are the *only* LLVM instructions that are permitted
within a Base Profile compliant program:

| LLVM Instruction         | Context and Purpose                                                                                              | Rules for Usage                                                                                             |
| :----------------------- | :--------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a function block to invoke any one of the declared QIS functions and the output recording functions. | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction).       |
| `br`                     | Used to branch from one block to another in the entry point function.                                            | The branching must be unconditional and occurs as the final instruction of a block to jump to the next one. |
| `ret`                    | Used to return the exit code of the program.                                                                     | Must occur (only) as the final instruction of the second (and last) block in the entry point.               |
| `inttoptr`               | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`.                                       | May be used as part of a function call only.                                                                |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value.                   | May be used as part of call to an output recording function only.                                           |

## Data Types and Values

Within the Base Profile, defining local variables is not supported; instructions
cannot be nested and constant expressions are fully evaluated. This implies the
following:

- Call arguments must be constant values, and `inttoptr` casts as well as
  `getelementptr` instructions must be inlined into a call instruction.
- It is not possible to express classical computations, such as, e.g., adding
  two double values, as part of a Base Profile compliant program.

Constants of any type are permitted as part of a function call. What data types
occur in the program hence depends entirely on the used QIS functions, as well
as the runtime functions used for output recording. Constant values of type
`i64` in particular may be used as part of calls to output recording functions;
see the section on [output recording](#output-recording) for more details.

For a program to be considered valid, it must make use of at least one qubit and
perform at least one measurement. The `%Qubit*` and `%Result*` data types hence
must be supported by all backends. Qubits and results can occur only as
arguments in function calls and are represented as a pointer of type `%Qubit*`
and `%Result*` respectively, where the pointer itself identifies the qubit or
result value rather than a memory location where the value is stored: a 64-bit
integer constant is cast to the appropriate pointer type. A more detailed
elaboration on the purpose of this representation is given in the next
subsection. The integer constant that is cast must be in the interval `[0,
nrQubits)` for `%Qubit*` and `[0, nrResults)` for `%Result*`, where `nrQubits`
and `nrResults` are the required number of qubits and results defined by the
corresponding [entry point attributes](#attributes). Since backends may look at
the values of the `required_qubits` and `required_results` attributes to
determine whether a program can be executed, it is recommended to index qubits
and results consecutively such that there are no unused values within these
ranges.

### Qubit and Result Usage

The amount of available memory on a QPU is commonly still fairly limited, with
regards to qubits as well as with regards to classical memory for storing
measurement results before they are read out and transmitted to another
classical processor. Any memory - quantum or classical - that is used during
quantum execution is not usually managed dynamically. Instead, operations are
scheduled and resources are bound as part of compilation. How early in the
process this happens varies, and QIR permits to express programs in a form that
either defers allocation and management of such resources to later stages, or to
directly identify individual qubits and results by a constant integer value as
outlined above. This permits to accurately reflect application intent for a
variety of frontends.

Ultimately, it is up to the executing backend which data structure is associated
with a qubit or result value. This gives a backend the freedom to, e.g., process
measurement results asynchronously, or attach additional device data to qubits.
Qubit and result values are correspondingly represented as opaque pointers in
the bitcode, and a QIR program must not dereference such pointers, independent
on whether they are merely bitcasts of integer constants as they are in the Base
Profile program above, or whether they are created dynamically, meaning the
value is managed by the executing backend.

To execute a given bitcode file, the backend needs to know how to process qubit and
result pointers used by a program. This is achieved by storing metadata in the
form of [module flags](#module-flags-metadata) in the bitcode. QIR does not make
a type distinction for the two kinds of pointers, nor does it use a different
address space for them. This ensures that libraries and optimization passes that
map between different instruction sets do not need to distinguish whether the
compiled application code makes use of dynamic qubit and result management or
not.

To be compliant with the Base Profile specification, the program must not make
use of dynamic qubit or result management; instead, qubits and results must be
identified by a constant integer value that is bitcast to a pointer to match the
expected type. How such an integer value is interpreted and specifically how it
relates to hardware resources is ultimately up to the executing backend.

Additionally, the Base Profile imposes the following restrictions on qubit and
result usage:

- Qubits must not be used after they have been measured. Which quantum
  instructions perform measurements is defined in the specification for known
  [quantum instructions](../Instruction_Set.md). For quantum instructions that
  are not listed there, we refer to the documentation provided by the targeted
  backend that supports them.

- Results can only be used either as `writeonly` arguments, or as arguments to
  [output recording functions](#output-recording). We refer to the [LLVM
  documentation](https://llvm.org/docs/LangRef.html#function-attributes)
  regarding how to use the `writeonly` attribute.

## Quantum Instruction Set

For a quantum instruction set to be fully compatible with the Base Profile, it
must satisfy the following two requirements:

- All functions must return void; the Base Profile does not permit to call
  functions that return a value. Functions that measure qubits must take the
  qubit pointer(s) as well as the result pointer(s) as arguments.

- Parameters of type `%Result*` must be `writeonly` parameters; only the runtime
  function `__quantum__rt__result_record_output` used for [output
  recording](#output-recording) may read a measurement result.

For more information about the relation between a profile specification and the
quantum instruction set we refer to the paragraph on [Bullet 1](#base-profile)
in the introduction of this document. For more information about how and when
the QIS is resolved, as well as recommendations for front- and backend
developers, we refer to the document on [compilation stages and
targeting](../Compilation_And_Targeting.md).

## Output Recording

The program output of a quantum application is defined by a sequence of calls to
runtime functions that return values produced by the computation. In the case of
the Base Profile, these calls are contained within the last block of the entry
point function.

The following functions can be used to record the program output:

| Function                            | Signature             | Description                                                                                                                                                                                                                                                 |
| :---------------------------------- | :-------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__tuple_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.  |
| __quantum__rt__array_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__result_record_output | `void(%Result*,i8*)` | Adds a measurement result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |

For all output recording functions, the `i8*` argument must be a non-null
pointer to a global constant that contains a null-terminated string. A backend
may ignore that argument if it guarantees that the order of the recorded output
matches the order defined by the entry point. Conversely, certain output schemas
do not require the recorded output to be listed in a particular order. For those
schemas, the `i8*` argument serves as a label that permits to reconstruct the
order intended by the program. [Compiler
frontends](https://en.wikipedia.org/wiki/Compiler#Front_end) must always
generate these labels such that the bitcode does not depend on the output
schema; while choosing how to best label the program output is up to the
frontend, the choice of output schema on the other hand is up to the backend. A
backend may reject a program as invalid or fail execution if a label is missing.

Both the labeling schema and the output schema are identified by a metadata
entry in the produced output. For the [output schema](../output_schemas/), that
identifier matches the one listed in the corresponding specification. The
identifier for the labeling schema, on the other hand, is defined by the value
of the `"output_labels"` attribute attached to the entry point.

## Module Flags Metadata

The following [module
flags](https://llvm.org/docs/LangRef.html#module-flags-metadata) must be added
to the QIR bitcode:

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
their behavior is set to `Warning`, `Append`, `AppendUnique`, `Max`, or `Min`.
It is at the discretion of the maintainers for various components in the QIR
stack to discard module flags that are not explicitly required or listed as
optional flags in the QIR specification.

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
  so that merging two modules compiled for different minor versions results in
  a module that adheres to the newer of the two versions.

### Memory Management

Each bitcode file contains the information whether pointers of type `%Qubit*`
and `%Result*` point to a valid memory location, or whether a pointer merely
encodes an integer constant that identifies which qubit or result the value
refers to. This information is represented in the form of the two module flags
named `"dynamic_qubit_management"` and `"dynamic_result_management"`. Within the
same bitcode module, there can never be a mixture of the two different kinds of
pointers. The behavior of both module flags correspondingly must be set to
`Error`. As detailed in the section on [qubit and result
usage](#qubit-and-result-usage), a Base Profile compliant program must not make
use of dynamic qubit or result management. The value of both module flags hence
must be set to `false`.
