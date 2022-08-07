# Compilation Process and Toolchain

QIR serves as an integrating layer on top of which a shared compilation stage is
built to connect a variety of front- and backends. To accelerate progress,
quantum programming frameworks often choose to expose tools and APIs to
facilitate research and development efforts across the entire stack rather than
just at the application level. Efforts to develop and evaluate the performance
of different error correction schemes, for example, illustrate that compilation
logic may initially be expressed as application code before it is automated and
integrated into the compiler toolchain. A high degree of flexibility and
configurability is hence of great importance when conceptualizing different
compilation stages and how front- and backends integrate with the QIR toolchain
and ecosystem. At the same time, a clear understanding of the purpose and
functionality of subsequent stages in the compilation process is absolutely
vital to grow a robust and performant compiler infrastructure over time.

In addition to the [design goals of
QIR](https://github.com/qir-alliance/qir-spec/blob/main/Scope.md) itself, we
hence define the following goals for the compiler infrastructure around it:

- Unify the ecosystem when reasonable; <br/>
  Certain design choices can easily and often unintentionally lead to a
  fragmentation of the ecosystem of quantum application, libraries, and
  compilation tools, making it harder to leverage existing work in a new
  context. For example, requiring application code to be expressed in terms of a
  backend-specific set of quantum instructions impedes portability of that code
  and hampers the development of shared application libraries.

- Allow making use of backend-specific instructions at the application level;
  <br /> Exposing access to backend-specific instructions is a valuable tool for
  research purposes. While we encourage libraries to be built against a hardware
  agnostic default set of instructions ([Default
  QIS](./quantum_instruction_sets/Default_QIS.md)), we aim for a simple
  mechanism for deviating from that default for the purpose of experimenting
  with new hardware intrinsics and developing backend-specific compiler
  optimizations. These development in turn inform what abstractions are
  beneficial to expose in the Default QIS, and permit to ultimately incorporate
  fruitful optimizations into a target specific compilation stage.

- Define (and follow clear) guidance for defining backend-specific instruction
  sets; <br /> ...

TODO: the same as what is mentioned under bullet 1 applies to profiles

## Compilation Stages

- Language specific compilation: Compilation of source code to QIR bitcode
- General optimizations: Optimizations that map QIR -> QIR and that do not limit
  compatibility in any way
- General linking: Combines bitcode from different sources and libraries
  according to [standard linking practices]()
- QIS resolution: Links a library (bitcode) taking naming conventions into
  account and giving strict precedence to the definitions in that library over
  definitions in the source code, unless otherwise indicated by a function
  attribute, and resolves precision if needed.
- Targeting and profile/qis specific optimization: maps QIR -> QIR profile
- Profile Validation: checks whether the compiled code is compliant with the
  specified profile and fails compilation otherwise
- Backend-specific compilation and optimization, resolution of runtime functions
  (possibly object level linking, standard LTO), possibly machine code
  generation

TODO: "Automatic weak attribute" for `__quantum__qis__` functions? -> probably
better to just require that `__quantum__qis__` function either are declaration
only, or are weak definitions. -> Or allow for front end specific names with an
attribute marking the compiled name that follows naming convention?

Considerations:

- Each frontend tends to have its own naming conventions. Either we assume we
  can reasonably achieve alignment on naming conventions across all functions
  used, or we carve out naming conventions for a subset of names (qis and rt
  functions) to be able to give clear guidance for target packages.
- How much value is there in keeping front end specific names up to a certain
  stage, and only then switch naming conventions? -> avoids naming conflicts in
  general libraries and sources? -> also avoids that each front end needs to
  implement the name replacement? -> should qis functions always be public?
- Target package: signatures must match for replacement, failure upon name match
  but signature mismatch *up to precision resolution* - one direction only; i.e.
  we can go from unspecified precision to specified precision -> does that work
  at the IR level? How do I even know precision is unspecified? -> attribute to
  force exact data type match?

frontend forward declares

- Who should add a function to the list of qis naming conventions and when? ->
  backend providers, asap; meaning even speculative ones should be added

### Linking

important to be able to use target specific instructions at the application
level without requiring frontends or other backends to add support on a
case-by-case basis.

QIS resolution can be done by having an optional attribute (one at most) on
function definitions in the program IR (i.e. the IR before our custom linking
stage) that indicates the target instruction name to check for. This means that
the program IR opts into using certain instructions (that should be listed under
naming conventions) if they are available on the targeted backend.

However, to enable research scenarios it needs to be possible, for example, to
easily prototype simulation specific optimizations that rely on direct access to
the quantum state, and leverage them to accelerate the simulation of quantum
subroutines defined in a library without modifying the source code of that
library.

This can be achieve by a custom compiler pass (QIR -> QIR) that takes a config
file of IR function names and the qis name as arguments and retroactively adds
this attribute. Note that this config file is frontend specific.

What we gain by adding a linking stage with some customizations, compared to
just use the standard llvm linker:

- It is still possible to have a simulator (or hardware for that matter) that
  implements several gate sets but use a specific gate set, i.e. only a subset
  of the implemented gates, during execution.
- It avoids forcing different front ends to effectively align on naming
  convention at the IR level.
- It permits to check signatures and fail at compile time if they don't match.

### Targeting

The QIR specification defines which instructions, including runtime functions
and QIS functions, are sufficient to support arbitrary computations that make
use of both quantum and classical resources, and gives recommendations for how
to leverage and combine these building blocks in a way that ensures maximal
compatibility with different backends. Most or possibly all backends today do
not support arbitrary computations. A common requirement for a program to be
executable on a quantum backend is, for example, that it is possible to ensure
during compilation that the quantum computation terminates. Such requirements
poses fundamental limitations for which programs can or cannot be executed on a
specific backend. Compiling a program in a way that maximizes compatibility with
different backends means that the program representation facilitates that
further compilation steps can largely eliminate constructs that are not
supported by the backend. This targeting process to meet backend requirements
compiles QIR into a QIR profile. It may result in a compilation failure if
certain constructs are not supported by the backend and cannot reasonably be
eliminated/replaced as part of targeting. For example, suppose the targeted
backend requires measurements to be performed only as a final instruction on a
QPU, i.e. all quantum resources are released after measurement. If the program
contains branching based on measurements, i.e. subsequent quantum computations
depend on a prior measurement result, then this construct (meaning the
branching) can be eliminate by replacing it with a coherent version according to
the [Deferred Measurement
Principle](https://en.wikipedia.org/wiki/Deferred_Measurement_Principle).
However, this may be impractical since it may require a (potentially
significantly) larger number of qubits to perform the computation, such that the
targeting stage may choose to fail compilation instead.

The QIR specification outlines how to ensure that certain data structures,
control flow structures, and classical computations can be eliminated during
targeting. It is up to each front end to determine the implications for when
source code can be successfully compiled and executed and whether or not to give
early feedback during development.

The profile validation stage ...

-> NOTE: Libraries are untargeted.
