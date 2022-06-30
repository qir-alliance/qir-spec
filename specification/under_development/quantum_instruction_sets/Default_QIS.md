# Default Quantum Instruction Set

The QIR specification contains a [table](../QuantumInstructions.md) of commonly used instructions along with their signatures and a description of their functionality.
Backends are **not** required to support all of these. Instead, each backend will declare which of these instructions it supports. We encourage to make instructions that are supported by a context independent implementation in terms of other instructions as a library rather than listing them as part of the backend specification. A library provided either in the form of a bitcode file can be linked in as part of a QIR compilation stage. 

TODO: It may also be possible to give sufficient guidance such that target packages can be defined in Rust and distributed via cargo. 
