# Quantum Intermediate Representation (QIR)

This specification defines an [LLVM](https://llvm.org/)-based intermediate
representation for quantum programs.

## Motivation

There are many languages and circuit-building packages that are used today to
program quantum computers. These languages have some similarities, but vary
significantly in their syntax and semantics.

Similarly, there are many different types of quantum computers available
already, and more types being developed. Different computers have different
instruction sets, different timings, and different classical capabilities.

It is very useful to have a single intermediate representation that can express
programs from all of the different quantum languages and can be converted into
code for any of the different quantum computers. This allows language developers
to write one compiler and quantum computer developers to write one code
generator, while still allowing all languages to run on all computers. This is a
well-established pattern in classical compilation.

## Model

We see compilation as having three high-level phases:

1. A language-specific phase that takes code written in some quantum language,
   performs language-specific transformations and optimizations, and compiles
   the result into this intermediate format.
2. A generic phase that performs transformations and analysis of the code in the
   intermediate format.
3. A target-specific phase that performs additional transformations and
   ultimately generates the instructions required by the execution platform in a
   target-specific format.

By defining our representation within the popular open-source
[LLVM](http://llvm.org) framework, we enable users to easily write code
analyzers and code transformers that operate at this level, before the final
target-specific code generation.

It is neither required nor expected that any particular execution target
actually implement every runtime function specified here. Rather, it is expected
that the target-specific compiler will translate the functions defined here into
the appropriate representation for the target, whether that be code, calls into
target-specific libraries, metadata, or something else.

This applies to quantum functions as well as classical functions. We do not
intend to specify a gate set that all targets must support, nor even that all
targets use the gate model of computation. Rather, the quantum functions in this
document specify the interface that language-specific compilers should meet. It
is the role of the target-specific compiler to translate the quantum functions
into an appropriate computation that meets the computing model and capabilities
of the target platform.

## Profiles

We know that many current targets will not support the full breadth of possible
quantum programs that can be expressed in this representation. We define a
sequence of specification _profiles_ that define coherent subsets of
functionality that a specific target can support.

## Version Compatibility

QIR specification versions are not intended to map one-to-one with specific
LLVM versions. However, QIR version 2.0 uses the opaque pointers, and
therefore is compatible with LLVM versions 16.0 and above. To use versions
of LLVM prior to 16.0, follow QIR version 1.0 with typed pointers.

Of note, LLVM versions 16.0 and above can still consume typed pointers, so
QIR 2.0 toolchains using these newer LLVM versions should still be able to
consume QIR 1.0 programs. QIR 2.0 programs cannot be consumed by QIR 1.0
toolchains.

The table below describes this compatibility:

Input | Output | Tooling
-- | -- | --
QIR v1.0 | QIR v1.0 | Use LLVM 15 or earlier
QIR v1.0 | QIR v2.0 | Use LLVM 16 or later
QIR v2.0 | QIR v2.0 | Use LLVM 16 or later
QIR v2.0 | QIR v1.0 | NOT SUPPORTED
