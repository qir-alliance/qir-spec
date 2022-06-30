# Base Profile

This profile defines a subset of the QIR specification to support a coherent set of functionalities and capabilities that might be offered by a system. The Base Profile specifies the minimal requirements for executing quantum programs. Execution of a Base Profile compliant program does, for instance, not require support executing quantum instructions dependent on measurement outcomes. The only requirements for a backend are to be able to perform unitary transformations on the quantum state, as well as measurements at the end of the program.

The intention is for frontends to emit programs that comply with the QIR specification, and for a compilation stage to then target this QIR to comply with the Base Profile specification. This targeting is possible in principle if the program doesn't make use of any features that would require hardware support. 

To support execution of Base Profile compliant programs, a QPU must have the following fundamental capabilities:
1. It supports executing a sequence of quantum instructions that transforms the quantum state.
2. It supports measuring the state of each qubit at the end of a computation.
3. It must be able to return the measured value for each qubit in the order requested by the program. This can be done in software as a post processing step after all quantum instructions and the final measurements have been performed; it does not require hardware or runtime support.

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

; entry point definition

define void @EntryPointName() #0 {
entry:

  ; calls to QIS functions  
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), %Result* inttoptr (i64 1 to %Result*))

  ; calls to record the program output
  tail call void @__quantum__rt__tuple_start_record_output()
  tail call void @__quantum__rt__result_record_output(%Result* null)
  tail call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*))
  tail call void @__quantum__rt__tuple_end_record_output()

  ret void
}

; declarations of QIS functions

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result*)

; declarations of functions used for output recording

declare void @__quantum__rt__tuple_start_record_output()

declare void @__quantum__rt__result_record_output(%Result*)

declare void @__quantum__rt__tuple_end_record_output()

; attributes

attributes #0 = { "EntryPoint" "requiredQubits"="2" "requiredResults"="2" }
```

TODO: a profile identifier and version number within the IR would be good to have (may be needed for correct usage of qubit and result pointers)   
-> look into custom target triples

TODO: update output recording function signature

## Entry Point Definition

The bitcode contains the definition of the LLVM function that should be invoked when the program is executed, 
refered to as entry point in the rest of this profile specification. 
The name of this function may be chosen freely, as long as it is a valid 
[global identifier](https://llvm.org/docs/LangRef.html#identifiers) by LLVM standard. 

The entry point may not take any parameters and must return void. 

### Attributes

The following custom attributes must be attached to the entry point function:

- An attribute named "EntryPoint" that does not 
- An attribute indicating the total number of qubits used by the program
- An attribute indicating the total number of classical bits required throughout the program to store measurement outcomes

These attributes will show up as an [attribute group](https://releases.llvm.org/13.0.1/docs/LangRef.html#attrgrp) in the IR.
Attribute groups are numbered such that they can be easily referenced by multiple function definitions or global variables. 
Arbitrary custom attributes may be optionally attached to any of the declared functions to convey additional information about that function. Consumers of Base Profile compliant programs should hence not rely on the numbering of the entry point attribute group, but instead look for function to which an attribute with the name `EntryPoint` is attached to determine which one to invoke when the program is launched.

To indicate the total number of qubits required to execute the program, a custom attribute with the name `requiredQubits` is defined and attached to the entry point. To indicate the number of registers/bits needed to store measurement results during program execution, a custom attribute with the name `requiredResults` is defined and attached to the entry point. The value of both of these attributes is the string representation of a 64-bit integer constant.

TODO: why the string value, and not an integer?   
TODO: align naming...

### Function Body

The function body consists of a single block named `entry`. This implies in particular that no branching is permitted inside a function's body.
In the `entry` block, any number of calls to QIS functions may be performed.
To be compatible with the Base Profile these functions must return void. 
Any arguments to invoke them must be inlined into the call itself; 
they hence must be constants or a pointer to a [qubit or result]()
The result of the program execution should be logged using output recording functions.

The following instructions are the *only* LLVM instructions that are permitted within a Base Profile compliant program:

| LLVM Instruction                  | Context and Purpose         | Restrictions for Usage |
|---------------------------|-------------------|-------------|
| call    | Used within a function block to invoke any one of the declared QIS functions and the output recording functions. | (none) |
| ret | ... | ... |
| inttoptr | ... | ... |

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

The QIR specification contains a [table]() of commonly used instructions along with their signatures and a description of their functionality.
Backends are **not** required to support all of these. Instead, each backend will declare which of these instructions it supports. We encourage to make instructions that are supported by a context independent implementation in terms of other instructions as a library rather than listing them as part of the backend specification. A library provided either in the form of a bitcode file or as a C library can be linked in as part of a QIR compilation stage. 

## Output Recording

The following functions are declared and used to record the program output: 
| Function                  | Signature         | Description |
|---------------------------|-------------------|-------------|
| __quantum__rt__tuple_start_record_output    | `void()`  | Inserts a marker in the output log that indicates the start of a tuple. |
| __quantum__rt__tuple_end_record_output    | `void()`  | Inserts a marker in the output log that indicates the end of a tuple. |
| __quantum__rt__array_start_record_output    | `void()`  | Inserts a marker in the output log that indicates the start of an array. |
| __quantum__rt__array_end_record_output    | `void()`  | Inserts a marker in the output log that indicates the end of an array. |
| __quantum__rt__result_record_output   | `void(%Result*)`  | Adds a measurement result to the output log. |

TODO: output format that also reflects job info like nr shots?