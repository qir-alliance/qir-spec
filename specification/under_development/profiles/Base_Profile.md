# Base Profile

This profile defines a subset of the QIR specification to support a coherent set of functionalities and capabilities that might be offered by a system. The Base Profile specifies the minimal requirements for executing quantum programs. Execution of a Base Profile compliant program does not, for instance, require supporting quantum instructions dependent on measurement outcomes. The only requirements for a backend are to be able to perform unitary transformations on the quantum state, as well as measurements at the end of the program.

The intention is for frontends to emit programs that comply with the QIR specification, and for a compilation stage to then target this QIR to comply with the Base Profile specification. This targeting is possible in principle if the program doesn't make use of any features that would require hardware support. 

To support execution of Base Profile compliant programs, a backend must have the following fundamental capabilities:
1. It supports executing a sequence of quantum instructions that transforms the quantum state.
2. It supports measuring the state of each qubit at the end of a computation.
3. It must be able to return the measured value for each qubit in the order requested by the program. This can be done in software as a post processing step after all quantum instructions and the final measurements have been performed; it does not require hardware or runtime support.

TODO: edit the third bullet to just say that it needs to be able to produce one of the define output formats? Are all output formats equivalent (I think so, *if* the labeling scheme is defined)?  
-> "the order requested by the program" may be somewhat ambiguous in any case, if we want to allow for parallelism/async execution

The second requirement should be taken to mean that a Base Profile compilant program does *not* apply instructions to a qubit after it has been measured; all instructions to transform the quantum state can be applied before performing any measurements. It specifically also means that there is no need for the QPU to be able to measure only a subset of all available qubits at a time.

## Program Structure

A Base Profile compliant program is defined in the form of a single LLVM bitcode file that consists of the following:
- definition of the opaque `Qubit` and `Result` types
- [entry point definition](#entry-point-definition)
- declarations of [QIS functions](#quantum-instruction-set)
- declarations of functions used for [output recording](#output-recording)
- [attributes](#attributes)

The human readable LLVM IR for the bitcode can be obtained using standard 
[LLVM tools](https://llvm.org/docs/CommandGuide/llvm-dis.html). For the purpose of clarity, this specification contains examples of the human readable IR emitted by [LLVM 13](https://releases.llvm.org/13.0.1/docs/LangRef.html). While the bitcode reprentation is portable and usually backward compatible, there may be visual differences in the human readable format depending on the LLVM version. This differences are irrelevant when using standard tools to load, manipulate, and/or execute bitcode.

The code below illustrates how a simple program looks like within a Base Profile representation:

```llvm
; type definitions

%Result = type opaque
%Qubit = type opaque

; global constants (labels for output recording)

@0 = internal constant [16 x i8] c"label_schema_id\00"
@1 = internal constant [3 x i8] c"r1\00"
@2 = internal constant [3 x i8] c"r2\00"

; entry point definition

define i64 @Entry_Point_Name() #0 {
entry:

  ; calls to QIS functions  
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))

  ; calls to record the program output
  tail call void @__quantum__rt__initialize_record_output(i8* getelementptr inbounds ([16 x i8], [16 x i8]* @0, i32 0, i32 0))  
  tail call void @__quantum__rt__tuple_record_output(i64 2, i8* null)
  tail call void @__quantum__rt__result_record_output(%Result* null, i8* getelementptr inbounds ([3 x i8], [3 x i8]* @1, i32 0, i32 0))
  tail call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* getelementptr inbounds ([3 x i8], [3 x i8]* @2, i32 0, i32 0))

  ret i64 0
}

; declarations of QIS functions

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result*)

; declarations of functions used for output recording

declare void @__quantum__rt__initialize_record_output(i8*)

declare void @__quantum__rt__tuple_record_output(i64, i8*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

; attributes

attributes #0 = { "entry_point" "required_qubits"="2" "required_results"="2" }
```

TODO: do we need additional restrictions for output recording? Like e.g. it needs to be a dedicated block, or output recording functions can only occur in the last block of the entry point?

TODO: do we need a __quantum__rt__initialize and __quantum__rt__finalize?
TODO: do we need __quantum__rt__read_result and __quantum__rt__write_result?

TODO: a profile identifier and version number within the IR would be good to have (may be needed for correct usage of qubit and result pointers)   
-> look into custom target triples

## Entry Point Definition

The bitcode contains the definition of the LLVM function that should be invoked when the program is executed, 
refered to as entry point in the rest of this profile specification. 
The name of this function may be chosen freely, as long as it is a valid 
[global identifier](https://llvm.org/docs/LangRef.html#identifiers) by LLVM standard. 

The entry point may not take any parameters and must return an exit code in the form of a 64-bit integer. The exit code 0 must be used to indicate a successful execution of the program. 

### Attributes

The following custom attributes must be attached to the entry point function:

- An attribute named "EntryPoint" that does not 
- An attribute indicating the total number of qubits used by the program
- An attribute indicating the total number of classical bits required throughout the program to store measurement outcomes

These attributes will show up as an [attribute group](https://releases.llvm.org/13.0.1/docs/LangRef.html#attrgrp) in the IR.
Attribute groups are numbered such that they can be easily referenced by multiple function definitions or global variables. 
Arbitrary custom attributes may be optionally attached to any of the declared functions to convey additional information about that function. Consumers of Base Profile compliant programs should hence not rely on the numbering of the entry point attribute group, but instead look for function to which an attribute with the name `entry_point` is attached to determine which one to invoke when the program is launched.

To indicate the total number of qubits required to execute the program, a custom attribute with the name `required_qubits` is defined and attached to the entry point. To indicate the number of registers/bits needed to store measurement results during program execution, a custom attribute with the name `required_results` is defined and attached to the entry point. The value of both of these attributes is the string representation of a 64-bit integer constant.

TODO: why the string value, and not an integer?   
TODO: no double underscore guard for attributes likely makes sense

### Function Body

The function body consists of a single block named `entry`. This implies in particular that no branching is permitted inside a function's body.
In the `entry` block, any number of calls to QIS functions may be performed.
To be compatible with the Base Profile these functions must return void. 
Any arguments to invoke them must be inlined into the call itself; 
they hence must be constants or a pointer to a [qubit or result]()
The result of the program execution should be logged using output recording functions.

The following instructions are the *only* LLVM instructions that are permitted within a Base Profile compliant program:

| LLVM Instruction                  | Context and Purpose         | Rules for Usage |
|---------------------------|-------------------|-------------|
| `call`    | Used within a function block to invoke any one of the declared QIS functions and the output recording functions. | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction). |
| `ret` | Used to return the exit code of the program. | Must occur (only) as the final instruction of the `entry` block. |
| `inttoptr` | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`. | May be used as part of a function call only. |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value. | May be used as part of call to an output recording function only. |

## Data Types and Values

Within the base profile, defining local variables is not supported. Arguments to calls correspondingly are expected to be constant values. 

Qubits and results are passes as a pointer of type `%Qubit*` and `%Result*` respectively, where the pointer itself rather than the memory location identifies the qubit or result: For the purpose of passing them as arguments in function calls, a 64-bit signed integer value is cast to the appropriate pointer type. The signed integer that is case must be in the interval `[0, nrQubits)` for `%Qubit*` and `[0, nrResults)` for `%Result*`, where `nrQubits` and `nrResults` are the required number of qubits and results defined by entry point attributes.

Only the `%Qubit` and `%Result` data types are required to be supported by all backends. 

Integers and double-precision floating point numbers are available as in full QIR;
however, computations using these numeric types are not available.

### Qubit and Result Usage

runtime has autonomoie over how to represent qubits. also for base profile, the runtime is the only entity that needs to know how to interprete the opaque pointers (deref or not). that info is captured in the target triple/duo.

Qubits may not be used after they have been measured. 
Qubits and results need to be numbered consecutively, starting at 0.
No qpu support needed for measuring individual qubits, but backend would support output selection?

## Quantum Instruction Set

For a Quantum Instruction Set to be compatible with the Base Profile, it needs to satisfy the following requirements:

- Since the Base Profile doesn't permit to define local variables, all instructions are required to return void. 

## Output Recording

Log format is a separate spec. What the i8* can be is a separate spec. Default spec for front-ends to compile into.
TODO: do string labels need to be zero terminated?

The following functions are declared and used to record the program output: 
| Function                  | Signature         | Description |
|---------------------------|-------------------|-------------|
| __quantum__rt__initialize_record_output    | `void(i8*)`  | Inserts a marker in the output log that contains an identifier for the used labeling scheme. The backend may choose which output format to use, and the label identifier is omitted for output formats that do not support labeling. |
| __quantum__rt__tuple_record_output    | `void(i64, i8*)`  | Inserts a marker in the output log that indicates the start of a tuple and how many tuple elements are going to be logged. The second parameter reflects an label for the tuple. The backend may choose which output format to use. Depending on the used format, the label will be logged or omitted. |
| __quantum__rt__array_record_output    | `void(i64, i8*)`  | Inserts a marker in the output log that indicates the start of an array and how many array elements are going to be logged. The second parameter reflects an label for the array. The backend may choose which output format to use. Depending on the used format, the label will be logged or omitted. |
| __quantum__rt__result_record_output   | `void(%Result*, i8*)`  | Adds a measurement result to the output log. The second parameter reflects an label for the result value. The backend may choose which output format to use. Depending on the used format, the label will be logged or omitted. |

TODO: It is sufficient to use the same functions for output recording independent on the output format; i.e. the output format does not need to be reflected in the IR, and it is sufficient to label the format it in the output itself. The output itself then needs to contain both the output format identifier (defined by the backend), as well as an identifier for the labeling scheme (as defined in the program IR itself).  
-> for base profile, no computations (classical or quantum, including calls to rt functions other than record_output* functions) can be performed after the call to __quantum__rt__initialize_record_output
