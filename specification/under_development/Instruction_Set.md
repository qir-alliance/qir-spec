# Instruction Set

A backend that supports quantum computations is composed of multiple processing
units that include one or more quantum processors as well as classic computing
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
profile they have been compiled for is given in Library_Reference.md.
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
than listing them as part of the backend specification.
