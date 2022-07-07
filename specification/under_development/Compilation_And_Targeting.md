# Compilation Stages

- Language specific compilation: Compilation of source code to QIR bitcode
- General optimizations: Optimizations that map QIR -> QIR and that do not limit compatibility in any way
- General linking: Combines bitcode from different sources and libraries according to [standard linking practices]()
- QIS resolution: Links a library (bitcode) giving strict precedence to the definitions in that library over definitions in the source code, unless otherwise indicated by a function attribute, and resolves precision if needed.

TODO: "Automatic weak attribute" for `__quantum__qis__` functions?  
-> probably better to just require that `__quantum__qis__` function either are declaration only, or are weak definitions. 
-> Or allow for front end specific names with an attribute marking the compiled name that follows naming convention?

Considerations:
- Each frontend tends to have its own naming conventions. Either we assume we can reasonably achieve alignment on naming conventions across all functions used, or we carve out naming conventions for a subset of names (qis and rt functions) to be able to give clear guideance for target packages.
- How much value is there in keeping front end specific names up to a certain stage, and only then switch naming conventions? -> avoids naming conflicts in general libraries and sources? -> also avoids that each front end needs to implement the name replacement? -> should qis functions always be public?
- Target package: signatures must match for replacement, failure upon name match but signature mismatch *up to precision resolution* - one direction only; i.e. we can go from unspecified precision to specified precision -> does that work at the IR level? How do I even know precision is unspecified? -> attribute to force exact data type match?

- Who should add a function to the list of qis naming conventions and when? -> backend providers, asap; meaning even speculative ones should be added

## Targeting

The QIR specification defines which instructions, including runtime functions and QIS functions, are sufficient to support arbitrary computations that make use of both quantum and classical resources, and gives recommendations for how to leverage and combine these building blocks in a way that ensures maximal compatibility with different backends. Most or possibly all backends today do not support arbitrary computations. A common requirement for a program to be executable on a quantum backend is, for example, that it is possible to ensure during compilation that the quantum computation terminates. Such requirements poses fundamental limitations for which programs can or cannot be executed on a specific backend. Compiling a program in a way that maximizes compatibility with different backends means that the program representation facilitates that further compilation steps can largely eliminate constructs that are not supported by the backend. This targeting process to meet backend requirements compiles QIR into a QIR profile. It may result in a compilation failure if certain constructs are not supported by the backend and cannot reasonably be eliminated/replaced as part of targeting. For example, suppose the targeted backend requires measurements to be performed only as a final instruction on a QPU, i.e. all quantum resources are released after measurement. If the program contains branching based on measurements, i.e. subsequent quantum computations depend on a prior measurement result, then this construct (meaning the branching) can be eliminate by replacing it with a coherent version according to the [Deferred Measurement Principle](https://en.wikipedia.org/wiki/Deferred_Measurement_Principle). However, this may be impractical since it may require a (potentially significantly) larger number of qubits to perform the computation, such that the targeting stage may choose to fail compilation instead.

The QIR specification outlines how to ensure that certain data structures, control flow structures, and classical computations can be eliminated during targeting. It is up to each front end to determine the implications for when source code can be successfully compiled and executed and whether or not to give early feedback during development. 

The profile validation stage ...
