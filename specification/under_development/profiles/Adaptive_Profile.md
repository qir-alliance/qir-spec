# Adaptive Profile

This profile defines a subset of the QIR specification to support a coherent set
of functionalities and capabilities that might be offered by a quantum backend.
Like all profile specifications, this document is primarily intended for
[compiler backend](https://en.wikipedia.org/wiki/Compiler#Back_end) authors as
well as contributors to the [targeting
stage](../Compilation_And_Targeting.md#targeting) of the QIR compiler.

The adaptive profile specifies supersets of the base profile that enable
control flow based on mid-circuit measurements and classical computations
within coherence times. A backend can support this profile by supporting
a minimum set of features beyond the base profile and can opt in for features
beyond that. This marks the first attempt at defining a profile greater in scope
than the base profile but still limited when compared to the full QIR specification.

To support the adaptive profile without any of its optional features, the following *capabilities* must be
implemented (a few restrictions are removed from the base profile):

1. An adaptive profile program can execute a sequence of quantum instructions
   that transform the quantum state.
2. An adaptive profile program can measure any qubit used in the program and
   thus a backend must be able to measure the state of all qubits for use in
   program output generation.
3. An adaptive profile program must produce one of the specified [output schemas](../output_schemas/).

Minimum capability additions to the base profile an adaptive profile supporting
backend must be able to support:

<!-- markdownlint-disable MD029 -->
4. Conditional branching (the profile must support the `br` instruction assuming
   that the instruction only expresses non-loop control flow). Since support for
   the `br` instruction relies on the `i1` type a small amount of instructions
   implementing classical logic on `i1` types is also assumed.
5. Mid-circuit measurement (`quantum__qis__mz__body` or some other measurement
   function must be supported in the quantum instruction set).
6. Conditional quantum operations in the instruction set that appear in the
   target basic blocks of a `br` instruction must be performed conditionally
   as with a classical LLVM program.
7. An `rt` function to turn a measurement result into a boolean
   (`__quantum__rt__read_result__body`) must be in the instruction set.

Beyond this, a backend can opt into one or more of the following additional
capabilities to extend minimal adaptive profile compliance with additional
features. A maximal adaptive profile program adds all of the following
capabilities. The extended possible adaptive profile capabilities a program can
express are:

8. Qubit resetting (`__quantum__qis__reset__body` supported in the instruction set).
9. Classical computations on integers, floating-point numbers, or fixed-point numbers.
10. User-defined functions and function calls.
11. Backwards branching.
12. Multiple target branching.
<!-- markdownlint-enable MD029 -->

Thus, any backend that supports capabilities 1-7 and as many of capabilities
8-12 as it desires is considered as supporting adaptive profile programs.
An adaptive profile program must indicate what additional capabilities it uses
via module flags. Additionally, backends can indicate how they support the
various optional capabilities and any caveats on support for the capabilities
that they do support via this [document](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).
Ideally, static analysis/verification tools should be able to understand what
capabilities of the adaptive profile a backend is implementing and should run
a verification pass to ensure adaptive profile programs that are using capabilities
not supported by a backend are rejected with an informative message.
More details about each of the aforementioned capabilities are outlined below.

## Mandatory Capabilities

### Bullet 1: Quantum transformations

The set of available instructions that transform the quantum state may vary
depending on the targeted backend. The profile specification defines how to
leverage and combine the available instructions to express a program, but does
not dictate which quantum instructions may be used. Targeting a program to a
specific backend requires choosing a suitable profile and quantum instruction
set (QIS). Both can be chosen largely independently, though certain instruction
sets may be incompatible with this (or other) profile(s). The section on the
[quantum instruction set](#quantum-instruction-set) defines the requirements for
a QIS to be compatible with the adaptive profile.
More information about the role of
the QIS, recommendations for front- and backend providers, as well as the
distinction between run-time functions and quantum instructions, can be found in
this [document](../Instruction_Set.md).

### Bullet 2: Measurements

The second requirement relieves a restriction from the base profile that qubits
can only be measured at the end of the program and that no quantum operations
can be performed on a measured qubit.
The only requirement here is that all qubits must be measurable, but
there are no restrictions on when these measurements are made, and there is
no restriction necessitating that all qubits be measured. I.E. it's perfectly
valid to measure a subset of qubits used in the program, not have all measured
qubits in the output, and perform the measurements at different points.

### Bullet 3: Program output

There is no change to output specifications with respect to the base profile.

The specifications of QIR and all its profiles need to accurately
reflect the program intent. This includes being able to define and customize the
program output. The base profile and adaptive profile specifications hence
require explicitly expressing which values/measurements are returned by the
program and in which order. How to express this is defined in the section on
[output recording](#output-recording).

A suitable output schema can be generated in a post-processing step after the
computation on the quantum processor itself has finished; customization of the
program output hence does not require support on the QPU itself.

The defined [output schemas](../output_schemas/) provide different options for
how a backend may express the computed value(s). The exact schema can be freely
chosen by the backend and is identified by a string label in the produced
schema. Each output schema contains sufficient information to allow quantum
programming frameworks to generate a user-friendly presentation of the returned
values in the requested order, such as, e.g., a histogram of all results when
running the program multiple times.

### Bullet 4: Conditional Forward branching

The adaptive profile can allow for arbitrary forward branching with the
restriction being that branch instructions cannot express programs that do not
terminate. By default, support for backwards branching is not a requirement,
though a backend can opt into **Bullet 11** to support backwards branching.
In the case that **Bullet 11** is not opted into, then a simple static analysis
can check for cycles in the control flow graph and reject any program with a
cycle as invalid. Depending on the vector of capabilities defined by an adaptive
profile program (like when **Bullet 11** is opted into), proving non-termination
with a static analysis may be impossible due to the capabilities forming a
Turing-complete subset of LLVM. Therefore, it is a rule that a *valid* adaptive
profile program should not contain non-terminating loops and that a frontend
generating a program with a non-terminating loop is generating a program that is
not compliant with the adaptive profile specification. However, since there is
no static analysis that can prove termination then it is up to backends to enforce
termination guarantees via a means of their choosing (for example a watchdog process
with a timeout that will kill an executing adaptive profile program if it takes
too much time). Different forms of conditional logic can be supported in the
profile based on optional features, but at minimum, the simple `br` branch
instruction must be supported.

### Bullet 5: Mid-circuit measurement

The adaptive profile allows for mid-circuit measurement to be expressed in
programs by removing restrictions on a measurement operation (we will use
measurement in Z represented by `llvm __quantum__qis__mz__body` in this
document, but other forms of measurement can also apply) that state that
measurements occur at the end of the quantum program and that the only
instructions following them are output recording functions. If a backend opts
into using this feature then it allows for programs with the following structure:

```llvm
call quantum__qis__h__body(%Qubit* null) ; arbitrary gate here
...
call quantum__qis__mz__body(%Qubit* null, %Result* null)
call quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*)) ; arbitrary gate choice again
...
```

### Bullet 6: Conditional Quantum Operations

Although forward branching can be useful when combined with purely classical
operations within a quantum program, the real utility is being able to
conditionally perform gates as part of things like repeat-until-success or
quantum-error-correction routines in quantum programs.

Here is an example program that mixes mid-circuit measurement (**Bullet 5**), a
`qis` function to convert a measurement result to a boolean (**Bullet 7**), and
a branch instruction (**Bullet 4**) to control how gates are applied based on
mid-circuit measurement.

```llvm
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  %0 = tail call i1 @__quantum__rt__read_result__body(%Result* null)
  br i1 %0, label %then, label %continue
then:                                   ; preds = %entry
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  br label %continue__1.i.i.i

continue:
...
```

### Bullet 7: Measurement Results to Booleans

A function to turn measurement results into classical data, mid-circuit, is
critical to using forward branching and conditional quantum execution.

```llvm
%0 = tail call i1 @__quantum__rt__read_result__body(%Result* null)
 br i1 %0, label %then, label %continue
```

## Optional Capabilities

### Bullet 8: Qubit resetting

If a backend opts into supporting this feature, then we can allow
for an instruction to reset qubits back to the |0> state to be defined
in the instruction set. This can be illustrated by the following program:

```llvm
call quantum__qis__h__body(%Qubit* null) ; arbitrary gate here
...
call quantum__qis__reset__body(%Qubit* null)
call quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*)) ; arbitrary gate choice again
...
```

This can be combined with the mid-circuit measurement (**Bullet 5**) to allow
for the capability to re-use the same qubit for computations, limiting the number
of qubits required for redundant calculations and also allowing for circuit width
to be reduced in favor of increasing depth:

```llvm
call quantum__qis__h__body(%Qubit* null)
call quantum__qis__mz__body(%Qubit* null, %Result* null) ; 1st coin flip
call quantum__qis__reset__body(%Qubit* null)
call quantum__qis__h__body(%Qubit* null)
call quantum__qis__mz__body(%Qubit* null, %Result* nonnull inttoptr (i64 1 to %Result*)) ; 2nd coin flip
call quantum__qis__reset__body(%Qubit* null)
```

### Bullet 9: Classical Computations

An adaptive profile program may include instructions or intrinsics for numeric
and logical computations that don't involve allocating memory for aggregate data
structures. These can include integer arithmetic calculations of a backend-specified
width, floating point arithmetic calculations of a backend-specified width,
logical operations on integers of a backend-specified width, or operations
on fixed-point numbers via intrinsics. Frontends can use any integer or floating
point width when generating code, and it is the responsibility of a backend to
provide a compile-time error message if the frontend uses an integer width greater
than that which the support.

When an adaptive profile program indicates that it is using a particular data
type, then instruction set (`qis`) functions or classical (`rt`) functions that
a backend may support can now be called. For example, consider that if a backend
supports integer computations and random number generation, then an adaptive profile
qir program may have code like the following to do randomized benchmarking:

```llvm
%0 = call i64 @__quantum__rt__rand_range(i64 0, i64 2)
%1 = icmp eq i64 %0, 0
br i1 %1, label %zero_rand_sequence, label %one_rand_sequence
```

By combining mid-circuit measurements with instructions on classical
data types, you can conditionally apply gates based on logic using multiple
mid-circuit measurements and boolean computations:

```llvm
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  %0 = tail call i1 @__quantum__rt__read_result__body(%Result* null)
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Result* nonnull inttoptr (i64 1 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  %1 = tail call i1 @__quantum__rt__read_result__body(%Result* nonnull inttoptr (i64 1 to %Result*))
  %2 = and i1 %0, %1
  br i1 %2, label %then, label %continue

then:                                   ; preds = %entry
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  br label %continue__1.i.i.i

continue:
...
```

An adaptive profile program can indicate which classical data type it supports by
setting the following module flags with `true` or `false` values for the rightmost
section of the module flag metadata, like in the table below. Any program like the
previous one that uses instructions on classical data types must have the
appropriate module flag set, or it is not a legal adaptive profile program.

| LLVM Module Flag                               | Context and Purpose                                                          |
| :--------------------------------------------- | :--------------------------------------------------------------------------- |
| `!{i32 1, !"classical_ints", i1 val_1}`        | indicates whether the integer `i1 and iN` data types are used by the program |
| `!{i32 1, !"classical_floats", i1 val_2`       | indicates whether a floating point `fN` data type is used by the program     |
| `!{i32 1, !"classical_fixed_points", i1 val_3` | indicates whether a fixed-point  data type is used by the program            |

For each data type being supported, some corresponding instructions must be
supported. The phi instruction can be used to conditionally move values between
branches dependent on control flow and must also be supported.
The `select` instruction should also be supported since practically, llvm optimization
passes are likely to generate `select` instructions when simplifying certain control
flow patterns. For each datatype, any caveats on the ability to support certain
instructions or where major differences in the behavior of the backend's execution
from the semantics of the LLVM instruction should be noted in this
[document](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile):

An adaptive profile program using integers as a datatype (the `classical_ints`
module flag is set to `true`) can use the instructions from the table below.

| LLVM Instruction | Context and Purpose                                                   | Note                                                                                       |
|:-----------------|:----------------------------------------------------------------------|:-------------------------------------------------------------------------------------------|
| `add`            | Used to add two integers together.                                    |                                                                                            |
| `sub`            | Used to subtract two integers.                                        |                                                                                            |
| `mul`            | Used to multiply integers                                             |                                                                                            |
| `udiv`           | Used for unsigned division.                                           | Can cause real-time errors.                                                                |
| `sdiv`           | Used for signed division.                                             | Can cause real-time errors.                                                                |
| `urem`           | Used for unsigned remainder division.                                 | Can cause real-time errors.                                                                |
| `srem`           | Used for signed remainder division.                                   | Can cause real-time errors.                                                                |
| `and`            | Bitwise and of two integers.                                          |                                                                                            |
| `or`             | Bitwise or of two integers.                                           |                                                                                            |
| `xor`            | Bitwise xor of two integers.                                          |                                                                                            |
| `shl`            | a left bit shift on a register or number.                             |                                                                                            |
| `lshr`           | Shifts a number the specified number of bits to the right.            | No sign extension.                                                                         |
| `ashr`           | Shifts a number the specified number of bits to the right.            | Does sign extension.                                                                       |
| `icmp`           | Performs signed or unsigned integer comparisons.                      | Different options are: `eq`, `ne`, `slt`, `sgt`, `sle`, `sge`, `ult`, `ugt`, `ule`, `uge`. |
| `zext`           | zero extend an iM to an iN where N>M                                  |                                                                                            |
| `sext`           | signed zero extend an iM to an iN where N>M                           |                                                                                            |
| `select`         | conditionally select the value in a register based on a boolean value |                                                                                            |
| `phi`            | assign a value to a register based on control-flow                    |                                                                                            |

Consider the following code snippet to illustrate phi instruction support for integers:

```llvm
define void @purelyclassical() local_unnamed_addr #0 {
entry:
  %0 = add i64 1, 2 ; 3
  %1 = icmp eq i64 %0, 3
  br i1 %6, label %then, label %else
then:
  %2 = add i64 %0, 1
  br label %else
else:
  %8 = phi i64 [ 0, %entry ],  [ %2, %then ]
  ret void
}
```

If an adaptive profile program has support for floating point computations (the
`classical_floats` module flag is set to `true`), then the following instructions
are supported.

| LLVM Instruction | Context and Purpose               | Note                        |
| :--------------- | :-------------------------------- | :-------------------------- |
| `fadd`           | Used to add two floats together.  |                             |
| `fsub`           | Used to subtract floats integers. |                             |
| `fmul`           | Used to multiply floats           |                             |
| `fdiv`           | Used for floating point division. | Can cause real-time errors. |
|                  |                                   |                             |

Finally, an adaptive profile program using fixed-point values (the `classical_fixed_points`
module flag is set to `true`), can use the following intrinsics:

| LLVM Intrinsic       | Context and Purpose                                  | Note                        |
| :------------------- | :--------------------------------------------------- | :-------------------------- |
| `llvm.smul.fix.*`    | Used to multiply two signed fixed point numbers.     |                             |
| `llvm.smul.fix.sat*` | Same as above but clamps to min/max number in scale. |                             |
| `llvm.umul.fix.*`    | Used to multiply two unsigned fixed point numbers.   |                             |
| `llvm.umul.fix.sat*` | Same as above but clamps to min/max number in scale. |                             |
| `llvm.sdiv.fix.*`    | Used to divide two signed fixed point numbers.       | Can cause real-time errors. |
| `llvm.sdiv.fix.sat*` | Same as above but clamps to min/max number in scale. |                             |
| `llvm.udiv.fix.*`    | Used to divide two unsigned fixed point numbers.     | Can cause real-time errors. |
| `llvm.udiv.fix.sat*` | Same as above but clamps to min/max number in scale. |                             |
|                      |                                                      |                             |

### Bullet 10: User-defined functions and function calls

An adaptive profile program may use user-defined functions and function calls.
For example, consider that with user-defined functions if a backend has a `Cnot`
gate in its instruction set, then a program that liberally uses `Swap` operations
can define a function and call it as follows:

```llvm
define void @swap(%Qubit* %arg1, %Qubit* %arg2) {
call void __quantum__qis__cnot__body(%Qubit* %arg1, %Qubit* %arg2)
call void __quantum__qis__cnot__body(%Qubit* %arg2, %Qubit* %arg1)
call void __quantum__qis__cnot__body(%Qubit* %arg1, %Qubit* %arg2)
}

define void @main() {
...
call void @swap_0_1(%Qubit* null, %Qubit* nonnull inttoptr (1 to %Qubit*))
...
}
```

Moreover, classical functions can be defined in the IR assuming that a backend
has opted into supporting classical computations:

```llvm
define i64 @triple(i64 %0) {
%1 = mul i64 %0, 3
ret i64 %1
}

define void @main() {
...
%0 = call void @triple(i64 2)
...
}
```

The only restriction on user functions and definitions is that you cannot have
dynamically allocated `%Qubit*`  arguments, they must still be constant `%Qubit*`
id's. An adaptive profile program using this feature must have a module flag
set like the following: `!{i32 1, !"user_functions", i1 true}`.

### Bullet 11: Backwards branching

Opting into this capability releases the restriction on backwards branching so
that a more compact representation of loops can be expressed in programs. Here
is a program that implements a loop via a backwards branch that performs coinflips
with a qubit and exits the program when the coin flip produces a 1. It is up to
a backend to enforce that a program using backwards branching does not cause
non-termination.

```llvm
...
define void @simple_loop() local_unnamed_addr #0 {
entry:
  br label %loop
loop:
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  %0 = call i1 @__quantum__rt__read_result__body(%Result* null)
  br i1 %0, label %exit, label %loop
exit:
  ret void
}
...
```

An adaptive profile program using this feature must
have a module flag set like the following: `!{i32 1, !"backwards_branching", i1 true}`.

### Bullet 12: Multiple Target Branching

It can be desirable to support control constructs that indicate how a computation
can lead to branching to one of *many* different control flow paths. Having such
a construct exposed in the IR allows for more aggressive optimization considerations
where it is easy to gather that gates being performed on the same qubits across
different blocks can have no control flow dependencies. As such, a backend can
opt into switch instruction support so that more aggressive static analysis and
optimization are possible. To make such a construct useful, some amount of integer
computation support (**Bullet 9**) must be supported. In the snippet below, we
can imagine that mid-circuit measurement fed into classical computations producing
`%val` and that each target block has conditional quantum operations.

```llvm
 Implement a jump table:
switch i32 %val, label %otherwise [ i32 0, label %onzero
                                    i32 1, label %onone
                                    i32 2, label %ontwo ]
```

An adaptive profile program using this feature must have a module flag set
like the following: `!{i32 1, !"multiple_target_branching", i1 true}`.

## Program Structure

An adaptive profile-compliant program is defined in the form of a single LLVM bitcode
file that contains the following:

- the definitions of the opaque `Qubit` and `Result` types
- global constants that store [string labels](#output-recording) needed for
  certain output schemas that may be ignored if the [output
  schema](../output_schemas/) does not make use of them
- the [entry point definition](#entry-point-definition) that contains the
  program logic
- declarations of the [QIS functions](#quantum-instruction-set) used by the
  program
- declarations of [run-time functions](#run-time-functions) used for
  initialization and output recording
- one or more [attribute groups](#attributes) used to store information about
  the entry point, and optionally additional information about other function
  declarations
- [module flags](#module-flags-metadata) that contain information that a
  compiler or backend may need to process the bitcode. These include module flags
  that indicate which features of the adaptive profile are used. A back end can
  list which module flags they support in the following [document](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).

The human-readable LLVM IR for the bitcode can be obtained using standard [LLVM
tools](https://llvm.org/docs/CommandGuide/llvm-dis.html). For clarity, this
specification contains examples of the human-readable IR emitted
by [LLVM 13](https://releases.llvm.org/13.0.1/docs/LangRef.html). While the
bitcode representation is portable and usually backward compatible, there may be
visual differences in the human-readable format depending on the LLVM version.
These differences are irrelevant when using standard tools to load, manipulate,
and/or execute bitcode.

The code below illustrates how a simple program looks within an adaptive profile
representation:

```llvm
; ModuleID = './QSharpVersion/qir/Example.ll'
source_filename = "./QSharpVersion/qir/Example.ll"

; declare fundamanetal quantum types supported by the profile

%Result = type opaque
%Qubit = type opaque

; constants for output labeling

@0 = internal constant [5 x i8] c"0_t0\00"
@1 = internal constant [5 x i8] c"0_t1\00"

; Entry point for teleport chain program utilizaing the minimal adaptive profile + bullet 8

define void @TeleportChain__DemonstrateTeleportationUsingPresharedEntanglement() local_unnamed_addr #0 {
entry:
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*), %Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*))
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*), %Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Result* null)
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  %0 = tail call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %0, label %then0__1.i.i.i, label %continue__1.i.i.i

; conditional quantum gate (only one in this block, but many can appear and the full quantum instruction set should be usable)
then0__1.i.i.i:                                   ; preds = %entry
  tail call void @__quantum__qis__z__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  br label %continue__1.i.i.i

continue__1.i.i.i:                                ; preds = %then0__1.i.i.i, %entry
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*), %Result* nonnull inttoptr (i64 1 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  %1 = tail call i1 @__quantum__qis__read_result__body(%Result* nonnull inttoptr (i64 1 to %Result*))
  br i1 %1, label %then0__2.i.i.i, label %TeleportChain__TeleportQubitUsingPresharedEntanglement__body.2.exit.i

then0__2.i.i.i:                                   ; preds = %continue__1.i.i.i
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  br label %TeleportChain__TeleportQubitUsingPresharedEntanglement__body.2.exit.i

TeleportChain__TeleportQubitUsingPresharedEntanglement__body.2.exit.i: ; preds = %then0__2.i.i.i, %continue__1.i.i.i
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*), %Qubit* nonnull inttoptr (i64 3 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*), %Result* nonnull inttoptr (i64 2 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  %2 = tail call i1 @__quantum__qis__read_result__body(%Result* nonnull inttoptr (i64 2 to %Result*))
  br i1 %2, label %then0__1.i.i1.i, label %continue__1.i.i2.i

then0__1.i.i1.i:                                  ; preds = %TeleportChain__TeleportQubitUsingPresharedEntanglement__body.2.exit.i
  tail call void @__quantum__qis__z__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  br label %continue__1.i.i2.i

continue__1.i.i2.i:                               ; preds = %then0__1.i.i1.i, %TeleportChain__TeleportQubitUsingPresharedEntanglement__body.2.exit.i
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*), %Result* nonnull inttoptr (i64 3 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*))
  %3 = tail call i1 @__quantum__qis__read_result__body(%Result* nonnull inttoptr (i64 3 to %Result*))
  br i1 %3, label %then0__2.i.i3.i, label %TeleportChain__DemonstrateTeleportationUsingPresharedEntanglement__body.1.exit

then0__2.i.i3.i:                                  ; preds = %continue__1.i.i2.i
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  br label %TeleportChain__DemonstrateTeleportationUsingPresharedEntanglement__body.1.exit

TeleportChain__DemonstrateTeleportationUsingPresharedEntanglement__body.1.exit: ; preds = %continue__1.i.i2.i, %then0__2.i.i3.i
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* nonnull inttoptr (i64 4 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*), %Result* nonnull inttoptr (i64 5 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 4 to %Result*), i8* getelementptr inbounds ([5 x i8], [5 x i8]* @0, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 5 to %Result*), i8* getelementptr inbounds ([5 x i8], [5 x i8]* @1, i32 0, i32 0))
  ret void
}

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*) local_unnamed_addr

declare void @__quantum__qis__h__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__x__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__z__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__reset__body(%Qubit*) local_unnamed_addr

declare void @__quantum__rt__result_record_output(%Result*, i8*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result*)

declare i1 @__quantum__qis__read_result__body(%Result*)

; attributes

attributes #0 = { "entry_point" "qir_profiles"="adaptive_profile" "output_labeling_schema"="schema_id" "required_num_qubits"="6" "required_num_results"="6" }

; module flags

!llvm.module.flags = !{!0, !1, !2, !3, !4, !5, !6, !7, !8, !9, !10}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
!4 = !{i32 1, !"qubit_resetting", i1 true} ; bullet 8 qubit resetting
!5 = !{i32 1, !"classical_ints", i1 false} ; ...
!6 = !{i32 1, !"classical_floats", i1 false}
!7 = !{i32 1, !"classical_fixed_points", i1 false}
!8 = !{i32 1, !"user_functions", i1 false}
!9 = !{i32 1, !"backwards_branching", i1 false}
!10 = !{i32 1, !"multiple_target_branching", i1 false}
```

The program performs gate teleportation, and it uses conditional single qubit
gates and mid-circuit measurements to effect control flow.

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
identifier](https://llvm.org/docs/LangRef.html#identifiers) according to the
LLVM standard. The entry point is identified by a custom function attribute; the
section on [attributes](#attributes) defines which attributes must be attached
to the entry point function.

An entry point function may not take any parameters and must either return void
in case the program has no failure conditions or must return an exit code in the
form of a 64-bit integer. In the case that a shot fails either because the entry
point function returns an integer value indicating that the program caught an
error or because an instruction caused an uncaught error (for example a `div`
instruction fails due to division by 0), then the output format should indicate
that the shot failed with output for the shot appearing as `ERROR Code: ival`
where `ival` is the error code from the adaptive profile program or `ERROR message`
in the case that an uncaught failure occurs, and the message is chosen by the backend.

The adaptive profile program makes no restrictions on the structure of basic
blocks within the entry point function, other than that a block cannot jump to a
previously encountered block in the control flow graph unless a backend opts
into **Bullet 11**. By default adaptive profile programs limit branching to only
express forward branching and nested conditionality. Additionally, the only
functions that can be called by default in the entry block are `qis` or `rt`
functions defined in the instruction set and profile. This restriction is removed
if a backend opts into **Bullet 10** which allows for user-defined functions.

## Quantum Instruction Set

For a quantum instruction set to be fully compatible with the adaptive profile, it
must satisfy the following three requirements:

- All functions must return `void`, `iN`, or `fN` types (`i1` and `i64` for example)
  and can only take in `%Qubit*`, `%Result*`, `iN`, or `fN` types as arguments.
  Additionally, arguments to the quantum instruction set cannot have dynamically
  computed arguments by default. They can however refer to static global values
  that are defined by linking (for example
  `call @__quantum__qis__rz__body(double @angle, %Qubit* null)` where `@double`
  is a static global who gets a new rotation angle linked at each shot).
  Dynamically computed arguments can be supplied to instruction set functions
  when adaptive profile programs use a classical data type from **Bullet 9**.
  Functions that measure qubits must take the qubit pointer(s) as well as the
  result pointer(s) as arguments.

- Functions that perform a measurement of one or more qubit(s) must be marked
  with a custom function attribute named `irreversible`. The use of
  [attributes](#attributes) in general is outlined in the corresponding section.

For more information about the relationship between a profile specification and the
quantum instruction set, we refer to the paragraph on [Bullet 1](#bullet-1-quantum-transformations)
in the introduction of this document. For more information about how and when
the QIS is resolved, as well as recommendations for front- and backend
developers, we refer to the document on [compilation stages and
targeting](../Compilation_And_Targeting.md).

## Classical Instructions

The following instructions are the LLVM instructions that were permitted
within a base profile-compliant program:

| LLVM Instruction         | Context and Purpose                                                                               | Rules for Usage                                                                                             |
| :----------------------- | :------------------------------------------------------------------------------------------------ | :---------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a basic block to invoke any one of the declared QIS functions and run-time functions. | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction).       |
| `br`                     | Used to branch from one block to another in the entry point function.                             | The branching must be unconditional and occurs as the final instruction of a block to jump to the next one. |
| `ret`                    | Used to return the exit code of the program.                                                      | Must occur (only) as the last instruction of the final block in the entry point.                            |
| `inttoptr`               | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`.                        | May be used as part of a function call only.                                                                |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value.    | May be used as part of a call to an output recording function only.                                         |

The adaptive profile extends the base profile with additional instructions such
as `br` (**Bullet 4**) and the additional opt-in instructions or intrinsics in
(**Bullet 9**)

See also the section on [data types and values](#data-types-and-values) for more
information about the creation and usage of LLVM values.

## Run-Time Functions

The following run-time functions must be supported by all backends:

| Function                            | Signature            | Description                                                                                                                                                                                                                                                  |
| :---------------------------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__initialize           | `void(i8*)`          | Initializes the execution environment. Sets all qubits to a zero-state if they are not dynamically managed.                                                                                                                                                  |
| __quantum__rt__tuple_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.  |
| __quantum__rt__array_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__result_record_output | `void(%Result*,i8*)` | Adds a measurement result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__bool_record_output   | `void(i1,i8*)`       | Adds a boolean value to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                              |

The following output recording functions can appear if you opt into supporting
real-time integer calculations (the backend supports the `classical_ints` module
flag). If you opt into a less standard width than any of the options below, then
it is up to the program to use a `zext` or `sext` instruction to get an `i32` or
`i64` value as an argument to the call, even if this extension is not actually
performed on the hardware and is just a means to make the program well-typed:

| Function                         | Signature       | Description                                                                                                                                                                                              |
| :------------------------------- | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__int_record_output | `void(i64,i8*)` | Adds an integer result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.        |
| __quantum__rt__i32_record_output | `void(i32,i8*)` | Adds an 32-bit integer result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted. |

The following output recording functions can appear if you opt into supporting
real-time floating point or fixed floating point calculations (the backend
supports the `classical_floats` and `classical_fixed_points` module flags). If
you opt into a less standard width than any of the options below, then it is up
to the program to use a `zext` or `sext` instruction to get an `f32` or `f64`
value as an argument to the call, even if this extension is not actually performed
on the hardware and is just a means to make the program well-typed:

| Function                            | Signature       | Description                                                                                                                                                                                                                    |
| :---------------------------------- | :-------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__double_record_output | `void(f64,i8*)` | Adds a double precision floating point value result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__f32_record_output    | `void(f32,i8*)` | Adds an 32-bit floating point value result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.          |

Additionally, a backend can provide more `rt` functions that can be used by
adaptive profile programs in accordance with the classical data types that it supports.

### Initialization

*A [workstream](https://github.com/qir-alliance/qir-spec/issues/11) to specify
how to initialize the execution environment is currently in progress. As part of
that workstream, this paragraph and the listed initialization function(s) will
be updated.*

### Output Recording

The program output of a quantum application is defined by a sequence of calls to
run-time functions that record the values produced by the computation,
specifically calls to the run-time functions ending in `record_output` listed in
the tables [above](#run-time-functions). In the case of the adaptive profile, these
calls are contained within the final block of the entry point function, i.e. the
block that terminates in a return instruction. In the case that conditional
data needs to be returned, then phi instructions are expected to be used to move
conditional data into the final block of the entry-point function.

For all output recording functions, the `i8*` argument must be a non-null
pointer to a global constant that contains a null-terminated string. A backend
may ignore that argument if it guarantees that the order of the recorded output
matches the order defined by the entry point. Conversely, certain output schemas
do not require the recorded output to be listed in a particular order. For those
schemas, the `i8*` argument serves as a label that permits the compiler or tool
that generated the labels to reconstruct the order intended by the program.
[Compiler frontends](https://en.wikipedia.org/wiki/Compiler#Front_end) must
always generate these labels in such a way that the bitcode does not depend on
the output schema; while choosing how to best label the program output is up to
the frontend, the choice of output schema, on the other hand, is up to the
backend. A backend may reject a program as invalid or fail execution if a label
is missing.

Both the labeling schema and the output schema are identified by a metadata
entry in the produced output. For the [output schema](../output_schemas/), that
identifier matches the one listed in the corresponding specification. The
identifier for the labeling schema, on the other hand, is defined by the value
of the `"output_labeling_schema"` attribute attached to the entry point.

## Data Types and Values

Within the adaptive profile, defining local variables is supported via
reading mid-circuit measurements via (**Bullets 5/7**) or by classical instructions
and calls (**Bullets 9**) if a backend supports
these features. This implies the
following:

- Call arguments can be constant values, `inttoptr` casts,
  `getelementptr` instructions that are inlined into a call instruction, or
  classical registers.
- backends can have various numeric data types used in their instructions
  if they opt in to using the classical types specified in  **Bullet 9**.

Constants of any type are permitted as part of a function call. What data types
occur in the program hence depends on what QIS functions are used in addition to
the run-time functions for initialization and output recording. Constant values
of type `i64` in particular may be used as part of calls to output recording
functions; see the section on [output recording](#output-recording) for more
details.

The `%Qubit*` and `%Result*` data types must be supported by all backends.
Qubits and results can occur only as arguments in function calls and are
represented as a pointer of type `%Qubit*` and `%Result*` respectively, where
the pointer itself identifies the qubit or result value rather than a memory
location where the value is stored: a 64-bit integer constant is cast to the
appropriate pointer type. A more detailed elaboration on the purpose of this
representation is given in the next subsection. The integer constant that is
cast must be in the interval `[0, numQubits)` for `%Qubit*` and `[0,
numResults)` for `%Result*`, where `numQubits` and `numResults` are the required
number of qubits and results defined by the corresponding [entry point
attributes](#attributes). Since backends may look at the values of the
`required_num_qubits` and `required_num_results` attributes to determine whether
a program can be executed, it is recommended to index qubits and results
consecutively so that there are no unused values within these ranges.

Due to **Bullet 7** being a mandatory capability, the `i1` type must be supported
by adaptive profile backends and branching should be possible based on the i1 values.
Other types like `i64` and `f64` are opt-in types depending on the capabilities
a backend wants to support via **Bullet 9**.

### Qubit and Result Usage

Qubits and result values are represented as opaque pointers in the bitcode,
which may only ever be dereferenced as part of a run-time function implementation.
In general, the QIR specification distinguishes between two kinds of pointers
for representing a qubit or result value, as explained in more detail
[here](../Execution.md), and either one, though not both, may be used
throughout a bitcode file. A [module flag](#module-flags-metadata) in the
bitcode indicates which kinds of pointers are used to represent qubits and
result values.

The first kind of pointer points to a valid memory location that is managed
dynamically during program execution, meaning the necessary memory is allocated
and freed by the run-time. The second kind of pointer merely identifies a qubit
or result value by a constant integer encoded in the pointer itself. To be
compliant with the adaptive profile specification, the program must not make use
of dynamic qubit or result management, meaning it must use only the second kind of
pointer; qubits and results must be identified by a constant integer value that
is bitcast to a pointer to match the expected type. How such an integer value is
interpreted and specifically how it relates to hardware resources is ultimately
up to the executing backend.

Additionally, the adaptive profile imposes the following restrictions on qubit and
result usage:

- Qubits must not be used after they have been passed as arguments to a function
  that performs an irreversible action. Such functions are marked with the
  `irreversible` attribute in their declaration.

- Results can only be used either as `writeonly` arguments, as arguments to
  [output recording functions](#output-recording), or as arguments to the
  measurement result to boolean conversion function (**Bullet 7**). We refer to the [LLVM
  documentation](https://llvm.org/docs/LangRef.html#function-attributes)
  regarding how to use the `writeonly` attribute.

## Attributes

The following custom attributes must be attached to the entry point function:

- An attribute named `"entry_point"` identifying the function as the starting
  point of a quantum program
- An attribute named `"qir_profiles"` with the value `"adaptive_profile"`
  identifying the profile the entry point has been compiled for
- An attribute named `"output_labeling_schema"` with an arbitrary string value
  that identifies the schema used by a [compiler
  frontend](https://en.wikipedia.org/wiki/Compiler#Front_end) that produced the
  IR to label the recorded output
- An attribute named `"required_num_qubits"` indicating the number of qubits
  used by the entry point
- An attribute named `"required_num_results"` indicating the maximal number of
  measurement results that need to be stored while executing the entry point
  function


Optionally, additional attributes may be attached to the entry point. Any custom
function attributes attached to the entry point should be reflected as metadata
in the program output; this includes both mandatory and optional attributes but
not parameter attributes or return value attributes. This in particular implies
that the [labeling schema](#output-recording) used in the recorded output can be
identified by looking at the metadata in the produced output. See the
specification of the [output schemas](../output_schemas/) for more information
about how metadata is represented in the output schema.

Custom function attributes will show up as part of an [attribute
group](https://releases.llvm.org/13.0.1/docs/LangRef.html#attrgrp) in the IR.
Attribute groups are numbered in such a way that they can be easily referenced
by multiple function definitions or global variables. Consumers of adaptive
profile-compliant programs must not rely on a particular numbering but instead,
look for the function to which an attribute with the name `"entry_point"` is
attached to determine which one to invoke when the program is launched.

Both the `"entry_point"` attribute and the `"output_labeling_schema"` attribute
can only be attached to a function definition; they are invalid on a function
that is declared but not defined. For the adaptive profile, this implies that they
can occur only in one place.

Within the restrictions imposed by the adaptive profile, the number of qubits that
are needed to execute the quantum program must be known at compile time. This
number is captured in the form of the `"required_num_qubits"` attribute attached
to the entry point. The value of the attribute must be the string representation
of a non-negative 64-bit integer constant.

Similarly, the number of measurement results that need to be stored when
executing the entry point function is captured by the `"required_num_results"`
attribute.

Beyond the entry point-specific requirements related to attributes, custom
attributes may optionally be attached to any of the declared functions. The
`irreversible` attribute in particular impacts how the program logic in the
entry point is structured, as described in the section about the [entry point
definition](#entry-point-definition). Furthermore, the following [LLVM
attributes](https://llvm.org/docs/LangRef.html#function-attributes) may be used
according to their intended purpose on function declarations and call sites:
`inlinehint`, `nofree`, `norecurse`, `readnone`, `readonly`, `writeonly`, and
`argmemonly`.

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
- A flag named `"qubit_resetting"` with a boolean i1 value indicating
if the program uses reset operations on qubits.
- A flag named `"classical_ints"`  with a boolean i1 value indicating
if the program uses classical computations on integers.
- A flag named `"classical_floats"`  with a boolean i1 value indicating
if the program uses classical computations on floating point values.
- A flag named `"classical_fixed_points"`  with a boolean i1 value indicating
if the program uses reset operations on fixed point values.
- A flag named `"user_functions"`  with a boolean i1 value indicating
if the program uses user defined functions and function calls.
- A flag named `"backwards_branching"`  with a boolean i1 value indicating
if the program uses branch instructions that causes "backwards" jumps in the control flow.
- A flag named `"multiple_target_branching"`  with a boolean i1 value indicating
if the program uses the switch instruction in llvm.

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
major and minor versions of the specification that the QIR bitcode adheres to.

- Since the QIR specification may introduce breaking changes when updating to a
  new major version, the behavior of the `"qir_major_version"` flag must be set
  to `Error`; merging two modules that adhere to different major versions must
  fail.

- The QIR specification is intended to be backward compatible within the same
  major version but may introduce additional features as part of newer minor
  versions. The behavior of the `"qir_minor_version"` flag must hence be `Max`
  so that merging two modules compiled for different minor versions results in a
  module that adheres to the newer of the two versions.

### Memory Management

Each bitcode file contains the information whether pointers of type `%Qubit*`
and `%Result*` point to a valid memory location, or whether a pointer merely
encodes an integer constant that identifies which qubit or result the value
refers to. This information is represented in the form of the two module flags
named `"dynamic_qubit_management"` and `"dynamic_result_management"`. Within the
same bitcode module, there can never be a mixture of the two different kinds of
pointers. The behavior of both module flags correspondingly must be set to
`Error`. As detailed in the section on [qubit and result
usage](#qubit-and-result-usage), an adaptive profile-compliant program must not make
use of dynamic qubit or result management. The value of both module flags hence
must be set to `false`.

For `i1`, `i64`, `f64`, ... values created by mid-circuit measurement, extern
functions, or classical computations the assumption is that while a `%Result*`
may point to a valid memory location in RAM or some other memory pool, by default,
instructions performed on virtual registers with these data types correspond to
these values being stored in integer or floating registers when an instruction is
executed. Before a virtual register is used in an instruction, there is no
assumption that the value in the virtual register always corresponds to a physical
register. For example, when considering register coloring, the virtual register,
`%0`, in the QIR program may refer to a value stored in RAM for most of its
lifetime before being loaded into a register when an instruction operates on `%0`.
backends should specify any constraints on classical compute support on this
[page](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).

### Error Messages

Two forms of error messages can occur as a result of the submission of adaptive
profile programs to a backend:

1. Compile-time error messages.
2. Run-time error messages.

The compile-time error messages can occur when a backend doesn't support some
of the optional features from **Bullets 8-12**. In this case, the backend should
flag which features in the module flags that were enabled that it does not
support. Additionally, if there are specific limitations on the support of certain
features, like not supporting a particular instruction in **Bullet 9**, then the
backend should return an error message indicating the type of instruction that
was not supported.

The run-time error messages can occur when opting into features such as the
classical computations in **Bullets 9**. In there, if division or remainder
instructions are supported, then a division by 0 error can occur. In the case
that a shot executing the program encounters such a real-time error, then an
error code should be reported for the shot in the QIR output format section for
the given shot.

### LLVM 15 Opaque Pointers

The transition of LLVM in LLVM 15 and on means that the `%Result*` and `%Qubit*`
representations of qubits and measurement results will no longer be valid.
Establishing a baseline LLVM version is not the point of this workstream. After
discussions around LLVM 15 and on support resolve, this spec will be updated on
how to indicate an adaptive profile program pre-LLVM 15 and for LLVM 15 and on.
The changes to these pointer representations are orthogonal to the concerns of
the adaptive profile other than that the signature of the measurement instruction
must necessarily change to represent how measurement results are actually
converted into `i1` values. See the discussion on this [upgrade](https://github.com/qir-alliance/qir-spec/issues/30).
