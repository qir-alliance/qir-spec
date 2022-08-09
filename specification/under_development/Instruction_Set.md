# Instruction Set

A backend that supports quantum computations is composed of multiple processing
units that include one or more quantum chips as well as classic computing
resources. A quantum program is a combination of instructions that execute on a
quantum processor, instructions that execute on an adjacent classical processor,
and data transfer between processors.

The QIR profile defines which instructions are used/supported for classical
computations and data transfer, while the Quantum Instruction Set (QIS) defines
which instructions are supported by the quantum processor. The profile and QIS
can be defined/chosen mostly independently, with the caveat that a profile
specification may contain restrictions that need to be satisfied for an QIS to
be compatible (compliant) with that profile. To target a program to a specific
backend hence requires selecting both a profiles and QIS that is supported by
that backend, see also [Compilation and
Targeting](Compilation_And_Targeting.md).

## Runtime Functions

Instructions that execute on a classical processor or serve data transfer are
expressed as LLVM instructions, including calls to `__quantum__rt__*` functions.
These functions are forward declared in the IR and defined by the executing
runtime. Which LLVM instructions and runtime functions are used/supported is
captured in the QIR profile specification. The complete list of all runtime
functions that are needed for executing QIR programs independent on which
profile they have been compiled for is given in the [Library_Reference.md]().
Most backends do not support the full set of runtime functions but merely a
subset that is sufficient for the supported QIR profile(s). The [Base
Profile](profiles/Base_Profile.md) defines the minimal set of runtime functions
that need to be supported for by a backend to permit computations that make use
of qubits and measurements of qubits. Additional functions may be needed to
support the use of data types beyond those for qubit and measurement result
values.

## Quantum Instruction Set (QIS)

The table below lists known quantum instructions along with their signatures and
a description of their functionality. Backends are **not** required to support
all of these. Instead, each backend will declare which of these instructions it
supports. We encourage to make instructions that are supported by a context
independent implementation in terms of other instructions as a library rather
than listing them as part of the backend specification. A library provided
either in the form of a bitcode file can be linked in as part of a QIR
compilation stage.

QIR does not specify the contents of the quantum instruction set. However, in
order to ensure some amount of uniformity, implementations that provide any of
the following quantum instructions must match the specified definition:

Who should add a function to the list of qis naming conventions and when?
-> backend providers, asap; meaning even speculative ones should be added.

| Operation Name | LLVM Function Declaration  | Description | Matrix |
|----------------|----------------------------|-------------|--------|
| CCx, CCNOT, Toffoli | `__quantum__qis__ccx__body (%Qubit* control1, %Qubit* control1, %Qubit* target)` | Toffoli or doubly-controlled X | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+1+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+1+%26+0+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+1+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+0+%26+1+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+0+%26+0+%26+1+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+1+%5C%5C+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+1+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Cx, CNOT | `__quantum__qis__cx__body (%Qubit* control, %Qubit* target)` | CNOT or singly-controlled X | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%26+0+%26+0+%5C%5C+0+%26+1+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+1+%5C%5C+0+%26+0+%26+1+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Cz | `__quantum__qis__cz__body (%Qubit* control, %Qubit* target)` | Singly-controlled Z | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%26+0+%26+0+%5C%5C+0+%26+1+%26+0+%26+0+%5C%5C+0+%26+0+%26+1+%26+0+%5C%5C+0+%26+0+%26+0+%26+-1+%5C%5C+%5Cend%7Bbmatrix%7D) |
| H | `__quantum__qis__h__body (%Qubit* target)` | Hadamard | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cfrac%7B1%7D%7B%5Csqrt%7B2%7D%7D%5Cbegin%7Bbmatrix%7D+1+%26+1+%5C%5C+1+%26+-1+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Mz or Measure | `__quantum__qis__mz__body (%Qubit* target, %Result* result)` | Measure a qubit along the the Pauli Z axis |
| Reset | `__quantum__qis__reset__body (%Qubit* target)` | Prepare a qubit in the \|0⟩ state |
| Rx | `__quantum__qis__rx__body (%Qubit* target, double theta)` | Rotate a qubit around the Pauli X axis | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+-i%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+-i%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Ry | `__quantum__qis__ry__body (%Qubit* target, double theta)` | Rotate a qubit around the Pauli Y axis | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+-%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Rz | `__quantum__qis__rz__body (%Qubit* target, double theta)` | Rotate a qubit around the Pauli Z axis | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+e%5E%7B-i+%5Ctheta%2F2%7D+%26+0+%5C%5C+0+%26+e%5E%7Bi+%5Ctheta%2F2%7D+%5C%5C+%5Cend%7Bbmatrix%7D) | |
| S | `__quantum__qis__s__body (%Qubit* target)` | S (phase gate)  | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+i+%5C%5C+%5Cend%7Bbmatrix%7D) |
| S&dagger; | `__quantum__qis__s_adj (%Qubit* target)` | The adjoint of S | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+-i+%5C%5C+%5Cend%7Bbmatrix%7D) |
| T | `__quantum__qis__t__body (%Qubit* target)` | T | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+e%5E%7Bi%5Cpi%2F4%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| T&dagger; | `__quantum__qis__t__adj (%Qubit* target)` | The adjoint of T operation | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+e%5E%7B-i%5Cpi%2F4%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| X | `__quantum__qis__x__body (%Qubit* target)` | Pauli X | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+0+%26+1+%5C%5C+1+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Y | `__quantum__qis__y__body (%Qubit* target)` | Pauli Y | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+0+%26+-i+%5C%5C+i+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Z | `__quantum__qis__z__body (%Qubit* target)` | Pauli Z | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+-1+%5C%5C+%5Cend%7Bbmatrix%7D) |
