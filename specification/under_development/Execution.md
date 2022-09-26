# Execution

TODO: define terminology (e.g. QPU), and add some diagrams for how a quantum
backend conceptually looks like somewhere.

entry point should not call another entry point

## QPU Resources

The amount of available memory on a QPU is commonly still fairly limited, with
regards to qubits as well as with regards to classical memory for storing
measurement results before they are read out and transmitted to another
classical processor. Any memory - quantum or classical - that is used during
quantum execution is not usually managed dynamically. Instead, operations are
scheduled and resources are bound as part of compilation. How early in the
process this happens varies, and QIR permits to express programs in a form that
either defers allocation and management of such resources to later stages, or to
directly identify individual qubits and results by a constant integer value as
outlined above. This permits various frontends to accurately reflect application
intent.

Ultimately, it is up to the executing backend which data structure is associated
with a qubit or result value. This gives a backend the freedom to, e.g., process
measurement results asynchronously, or attach additional device data to qubits.
Qubits and result values are correspondingly represented as opaque pointers in
the bitcode, and a QIR program must not dereference such pointers, independent
on whether they are merely bitcasts of integer constants as they are in the Base
Profile program above, or whether they are created dynamically, meaning the
value is managed by the executing backend.

QIR does not make a type distinction for the two kinds of pointers, nor does it
use a different address space for them. This ensures that libraries and
optimization passes that map between different instruction sets do not need to
distinguish whether the compiled application code makes use of dynamic qubit and
result management or not. To execute a given bitcode file, the backend needs to
know how to process qubit and result pointers used by a program. This is
achieved by storing metadata in the form of [module
flags](https://llvm.org/docs/LangRef.html#module-flags-metadata) in the bitcode.
