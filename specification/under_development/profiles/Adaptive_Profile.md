# Adaptive Profile

This profile defines a subset of the QIR specification to support a coherent set
of functionalities and capabilities that might be offered by a quantum backend.
Like all profile specifications, this document is primarily intended for
[compiler backend](https://en.wikipedia.org/wiki/Compiler#Back_end) authors as
well as contributors to the [targeting
stage](../Compilation_And_Targeting.md#targeting) of the QIR compiler.

The Adaptive Profile specifies supersets of the [Base
Profile](./Base_Profile.md) that enable control flow based on mid-circuit
measurements and classical computations while quantum resources remain coherent.
A backend can support this profile by supporting a minimum set of features
beyond the [Base Profile](./Base_Profile.md) and can opt in for features beyond
that.

To support the Adaptive Profile without any of its optional features, a backend
must support the following [mandatory capabilities](#mandatory-capabilities):

1. It can execute a sequence of quantum instructions that transform the quantum
   state.
2. A backend must support applying a measurement operation at any point in the
   exeuction of the program. Qubits not undergoing the measurement should not
   have their state affected.
3. A backend must be able to apply quantum instructions conditionally on a
   measurement outcome. Specifically, forward branching using the LLVM branch
   instruction `br` must be supported, along with the necessary runtime function
   to convert a measurement to an `i1` value and the LLVM instructions for
   computations on `i1` values defined in detail below.
4. It must produce one of the specified [output schemas](../output_schemas/).

This means that at minimum, backends supporting Adaptive Profile programs should
support mid-circuit measurement, turning measurements into booleans, and
branching based on those booleans. The QIR Adaptive Profile in particular also
requires that branches can be arbitrarily nested. This includes a requirement
that it must be possible to perform a measurement within a branch, and then
branch again on that measurement. As for the Base Profile, any Adaptive Profile
is always garanteed to terminate, i.e. there are not control flow loops
permitted that would lead to a potentially indefinitvely running program.

Beyond the providing the required capabilities above, a backend can opt into one
or more of the following [optional capabilities](#optional-capabilities) to
support more advanced adaptive computations:

<!-- markdownlint-disable MD029 -->
5. Computations on classical (non-composite) data types, specifically on
   integers, floating-point numbers, or fixed-point numbers.
6. IR-defined functions and calls of these functions at any point in the
   program.
7. Backwards branching to express terminating loops. Non-terminating loops
   ("while"-loops) are not permitted within the Adaptive Profile, regardless of
   the support for this optional feature. It is specifically not permitted to
   have a loop that terminates only based on a measurement outcome.
   Correspondinly, permitting for backward branching only makes sense when the
   backend also supports computations on at least one classical data type.
8. Multiple target branching.
9. Multipe return points.
<!-- markdownlint-enable MD029 -->

The use of these optional features is represented as a [module
flag](#module-flags-metadata) in the program IR. Any backend that supports
capabilities 1-4 and as many of capabilities 5-9 as it desires is considered as
supporting Adaptive Profile programs. The optional capabilities supported by
different backends along with details about that support are captured in this
[document](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).
Ideally, static analysis/verification tools should be able to understand what
capabilities of the Adaptive Profile a backend is implementing and should run a
verification pass to ensure Adaptive Profile programs that are using
capabilities not supported by a backend are rejected with an informative
message. More details about each of the aforementioned capabilities are outlined
in the following sections.

## Mandatory Capabilities

**Bullet 1: Quantum transformations** <br/>

The set of available instructions that transform the quantum state may vary
depending on the targeted backend. The profile specification defines how to
leverage and combine the available instructions to express a program, but does
not dictate which quantum instructions may be used. Targeting a program to a
specific backend requires choosing a suitable profile and quantum instruction
set (QIS). Both can be chosen largely independently, though certain instruction
sets may be incompatible with this (or other) profile(s). The section on the
[quantum instruction set](#quantum-instruction-set) defines the requirements for
a QIS to be compatible with the Adaptive Profile. More information about the
role of the QIS, recommendations for front- and backend providers, as well as
the distinction between runtime functions and quantum instructions, can be found
in this [document](../Instruction_Set.md).

**Bullet 2: Measurements** <br/>

As for the Base Profile, a measurement function is a QIS function marked with an
[`irreversible` attribute](./Base_Profile.md#quantum-instruction-set) that
populates a value of type `%Result`. The available measurement functions are
defined by the executing backend as part of the QIS. Unlike the Base Profile,
the Adaptive Profile relieves a restriction that qubits can only be measured at
the end of the program and that no quantum operations can be performed after or
conditionally on a measurement outcome.

Within the Adaptive Profile, there are no restrictions on when these
measurements are performed during program execution. Correspondingly, it must be
possible to measure individual qubits, or subsets of qubits depending on the
supported QIS, without impacting the state of the non-measured qubits.
Furthermore, it must be possible to use the measured qubit(s) afterwards and
apply additional quantum instructions to the same qubit(s).

**Bullet 3: Forward Branching** <br/>

Additionally, the Adapative Profile requires that it must be possible to take
action based on a measurement result. Specifically, it must be possible to
execute subsequent quantum instructions conditionally on the produced `%Result`
value. To that end, a runtime function must be provided that converts a
`%Result` value into a value of type `i1`; see the section on [Runtime
Functions](#runtime-functions) for further clarification. Additionally, the LLVM
branch instruction `br` must be supported; see the section on [Classical
Instructions](#classical-instructions) for further clarification.

The Adaptive Profile allows for arbitrary forward branching based on `i1`
values. While arbitrary nesting of branches must be supported, an Adaptive
Profile program must ensure that the program terminates. Unless the profile
makes use of the optional capability of backward branching (**Bullet 7**), the
control flow structure of a program is hence a tree without any cycles. A static
analysis to detemine the validity of the program should check for cycles in the
control flow graph and reject any program with a cycle as invalid unless support
for backward branching is enabled.

While the Adaptive Profile requires that it must be possible to use a qubit
after it was measured, the availability of a `reset` instruction depends on the
QIS supported by the backend. If a single-qubit measurement is supported as part
of the QIS, it is always possible to reset that qubit, if needed for qubit
resuse later in the program, using forward branching as illustrated for example
by the following IR snippet:

```llvm
...
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  %0 = tail call i1 @__quantum__rt__read_result__body(%Result* null)
  br i1 %0, label %then, label %continue
then:                                   ; preds = ...
  tail call void @__quantum__qis__x__body(%Qubit* null)
  br label %continue
continue:
  ...
```

Although forward branching can be useful when combined with purely classical
operations within a quantum program, the real utility is being able to
conditionally perform gates depending on measurement outcomes, for example when
performing real-time error-correction as part of a quantum programs.

**Bullet 4: Program output** <br/>

The specifications of QIR and all its profiles need to accurately reflect the
program intent. This includes being able to define and customize the program
output. The Base Profile and Adaptive Profile specifications hence require
explicitly expressing which values/measurements are returned by the program and
in which order. How to express this is defined in the section on [output
recording](#output-recording).

The defined [output schemas](../output_schemas/) provide different options for
how a backend may express the computed value(s). The exact schema can be freely
chosen by the backend and is identified by a string label in the produced
schema. Each output schema contains sufficient information to allow quantum
programming frameworks to generate a user-friendly presentation of the returned
values in the requested order, such as, e.g., a histogram of all results when
running the program multiple times.

While the general output recording mechanism and the output schemas are the same
for all profiles, the Adaptive Profile makes it possible to output classical
values, if - and only if - computations on classical data types are supported
(see the section on [output recording](#output-recording) for more details). If
computations on classical data types are supported, the program may furthermore
produce a non-zero exit codes indicating a runtime failure (e.g. for division by
zero). Injecting suitable logic to produce a non-zero exit code in the case of
classical computations that lead to an incorrect program output is generally up
to the compiler, and the backend is not required to detect runtime failures.
Unless the backend supports the optional capability of having multiple return
statements in a program, it is up to the compiler to make use of `phi`-nodes to
propagate any error code to the single final return statement at the end of the
entry-point function.

## Optional Capabilities

### Bullet 5: Classical Computations

A backend can choose to support an extended Adaptive Profile that may include
instructions for classical computations on atomic data types, including integer
and floating-point arithmetics. The behavior in the case of an overflow or
underflow may be undefined. Backend providers are encouraged to capture optional
profile capabilities including any supported data types in this
[document](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).
All LLVM instructions that must be available to support an extended Adapative
Profile including classical computations are listed in the section on [classical
instructions](#classical-instructions).

Which data types are used in classical computations as part of an extended
Adaptive Profile must be indicated in the form of [module
flags](#module-flags-metadata). The module flag(s) specifically also include
information about the bitwith(s) of the used data type(s). It is the
responsiblity of the backend to provide a compile-time error message if any of
the used data types or widths thereof are not supported.

If the program makes use of classical computations on a specific data type, it
implies that variables of that data type may exist at any point in the program.
Specifically, it is then also permitted to pass such variables as arguments to
QIS functions, runtime functions, or [IR
functions](#bullet-6-ir-defined-functions-and-function-calls) (if available), as
illustrated in the [examples](#examples) section. Passing constant values of any
data type as arguments to QIS and runtime functions is always permitted,
regardless of whether classical computations on that data type are supported.

<!-- FIXME:
Allow to define and use global constants for (only) the supported data types.
-->

### Bullet 6: IR-defined functions and function calls

A backend can choose to support an extended Adaptive Profile that includes
IR-defined functions, that is functions whose implementation is defined as part
of the program IR. An Adaptive Profile program that includes IR-defined functions
must indicate this in the form of a [module flag](#module-flags-metadata).

IR-defined functions may take arguments of type `%Qubit`
and `%Result`, and it may either return a value of type `%Result` or choose to
have a `void` return type. If [classical computations](#bullet-5-classical-computations)
are supported in addition to IR-defined functions, then values of the supported
data type(s) may also be passed as arguments to, and returned from, an
IR-function.

The body of an IR-defined function may use any of the available [classical
instructions](#classical-instructions). It may call QIS function and other IR
functions. In contrast to the [entry point function](#entry-point-definition),
an IR-defined function may *not* contain any calls to [output
recording](#output-recording) functions, but it may call any other available
runtime function.

<!-- FIXME: 
Within the body of an IR-defined function, values of type `%Qubit` and `%Result`
can only occur in calls to other functions. - same for entry points
-->

### Bullet 7: Backwards branching

Opting into this capability releases the restriction on backwards branching so
that a more compact representation of loops can be expressed in programs. Here
is a program that implements a loop via a backwards branch that performs
coinflips with a qubit and exits the program when the coin flip produces a 1. It
is up to a backend to enforce that a program using backwards branching does not
cause non-termination.

Proving non-termination with a static analysis may be impossible due to the
capabilities forming a Turing-complete subset of LLVM. Since there is no static
analysis that can prove termination then it is up to backends to enforce
termination guarantees via a means of their choosing (for example a watchdog
process with a timeout that will kill an executing Adaptive Profile program if
it takes too much time).

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

An Adaptive Profile program using this feature must have a module flag set like
the following: `!{i32 1, !"backwards_branching", i1 true}`.

### Bullet 8: Multiple Target Branching

It can be desirable to support control constructs that indicate how a
computation can lead to branching to one of *many* different control flow paths.
Having such a construct exposed in the IR allows for more aggressive
optimization considerations where it is easy to gather that gates being
performed on the same qubits across different blocks can have no control flow
dependencies. As such, a backend can opt into switch instruction support so that
more aggressive static analysis and optimization are possible. To make such a
construct useful, some amount of integer computation support (**Bullet 5**) must
be supported. In the snippet below, we can imagine that mid-circuit measurement
fed into classical computations producing `%val` and that each target block has
conditional quantum operations.

```llvm
 Implement a jump table:
switch i32 %val, label %otherwise [ i32 0, label %onzero
                                    i32 1, label %onone
                                    i32 2, label %ontwo ]
```

An Adaptive Profile program using this feature must have a module flag set like
the following: `!{i32 1, !"multiple_target_branching", i1 true}`.

### Bullet 9: Multiple Return Points

As an optional feature, Adaptive Profile programs can have multiple return
points in the entry point function. For example, an adpative profile program can
contain code like:

```llvm
...
define i32 @simple_br() local_unnamed_addr #0 {
entry:
  br i1 label %error, label %exit
error:
  ret 2
exit:
  ret 0
}
```

An Adaptive Profile program using this feature must have a module flag set like
the following: `!{i32 1, !"multiple_return_points", i1 true}`.

## Program Structure

An Adaptive Profile-compliant program is defined in the form of a single LLVM
bitcode file that contains the following:

- the definitions of the opaque `Qubit` and `Result` types
- global constants that store [string labels](#output-recording) needed for
  certain output schemas that may be ignored if the [output
  schema](../output_schemas/) does not make use of them
- the [entry point definition](#entry-point-definition) that contains the
  program logic
- declarations of the [QIS functions](#quantum-instruction-set) used by the
  program
- declarations of [runtime functions](#runtime-functions) used for
  initialization and output recording
- one or more [attribute groups](#attributes) used to store information about
  the entry point, and optionally additional information about other function
  declarations
- [module flags](#module-flags-metadata) that contain information that a
  compiler or backend may need to process the bitcode. These include module
  flags that indicate which features of the Adaptive Profile are used. A back
  end can list which module flags they support in the following
  [document](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).

The human-readable LLVM IR for the bitcode can be obtained using standard [LLVM
tools](https://llvm.org/docs/CommandGuide/llvm-dis.html). For clarity, this
specification contains examples of the human-readable IR emitted by [LLVM
13](https://releases.llvm.org/13.0.1/docs/LangRef.html). While the bitcode
representation is portable and usually backward compatible, there may be visual
differences in the human-readable format depending on the LLVM version. These
differences are irrelevant when using standard tools to load, manipulate, and/or
execute bitcode.

The code below illustrates how a simple program looks within an Adaptive Profile
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

; Entry point for teleport chain program utilizaing the minimal Adaptive Profile + bullet 8

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
!4 = !{i32 5, !"int_computations", !""}
!5 = !{i32 5, !"float_computations", !""}
!6 = !{i32 5, !"fixedpoint_computations", !""}
!7 = !{i32 1, !"ir_functions", i1 false}
!8 = !{i32 1, !"backwards_branching", i1 false}
!9 = !{i32 1, !"multiple_target_branching", i1 false}
!10 = !{i32 1, !"multiple_return_points", i1 false}
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
where `ival` is the error code from the Adaptive Profile program or `ERROR
message` in the case that an uncaught failure occurs, and the message is chosen
by the backend.

The Adaptive Profile program makes no restrictions on the structure of basic
blocks within the entry point function, other than that a block cannot jump to a
previously encountered block in the control flow graph unless a backend opts
into **Bullet 8**. By default Adaptive Profile programs limit branching to only
express forward branching and nested conditionality. Additionally, the only
functions that can be called by default in the entry block are `qis` or `rt`
functions defined in the instruction set and profile. This restriction is
removed if a backend opts into **Bullet 6** which allows for IR-defined
functions.

## Quantum Instruction Set

For a quantum instruction set to be fully compatible with the Adaptive Profile,
it must satisfy the following three requirements:

- All functions must return `void`, `iN`, or `fN` types (`i1` and `i64` for
  example) and can only take in `%Qubit*`, `%Result*`, `iN`, or `fN` types as
  arguments. Additionally, arguments to the quantum instruction set cannot have
  dynamically computed arguments by default. They can however consume constant
  values of any data type. Dynamically computed arguments can be supplied to
  instruction set functions when adaptive profile programs use a classical data
  type from **Bullet 5**. Functions that measure qubits must take the qubit
  pointer(s) as well as the result pointer(s) as arguments.

- Functions that perform a measurement of one or more qubit(s) must be marked
  with a custom function attribute named `irreversible`. The use of
  [attributes](#attributes) in general is outlined in the corresponding section.

For more information about the relationship between a profile specification and
the quantum instruction set, we refer to the paragraph on [Bullet
1](#adaptive-profile) in the introduction of this document. For more information
about how and when the QIS is resolved, as well as recommendations for front-
and backend developers, we refer to the document on [compilation stages and
targeting](../Compilation_And_Targeting.md).

## Classical Instructions

Without any optional capabilities, the same classical LLVM instructions must be
supported as the ones required by the Base Profile. However, some of the
restrictions in the Base Profile no longer apply for the adaptive profile.
Specifically, the following table lists all classical instructions and their use
for an Adaptive Profile without any optional capabilities:

| LLVM Instruction         | Context and Purpose                                                                              | Rules for Usage                                                                                             |
| :----------------------- | :----------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a basic block to invoke any one of the QIS-, IR-, and runtime functions.             | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction).       |
| `br`                     | Used to branch from one basic block to another.                                                  | The branching is the final instruction in any basic block and may conditionally jump to different blocks depending on an `i1` value. |
| `ret`                    | Used to return the exit code of the program.                                                     | Must occur (only) as the last instruction of the final block in an entry point, unless multiple return statements (optional capability) are supported. |
| `inttoptr`               | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`.                       | May be used as part of a function call only.                                                                |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value.   | May be used as part of a call to an output recording function only.                                         |

See also the section on [data types and values](#data-types-and-values) for more
information about the creation and usage of LLVM values.

Supporting [optional capabilities](#optional-capabilities) requires additional
LLVM instructions to be supported. The following tables list the
instructions required for each of the optional capabilities.

If an Adaptive Profile program has support for integer computations,
then the following instructions are supported:

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
| `trunc`           | truncate an iN to an iM where N>M                           |                                                                                            |
| `select`         | conditionally select the value in a register based on a boolean value |                                                                                            |
| `phi`            | assign a value to a register based on control-flow                    |                                                                                            |

If an Adaptive Profile program has support for floating point computations on
floating-point numbers, then the following instructions are supported:

| LLVM Instruction | Context and Purpose               | Note                        |
| :--------------- | :-------------------------------- | :-------------------------- |
| `fadd`           | Used to add two floats together.  |                             |
| `fsub`           | Used to subtract floats integers. |                             |
| `fmul`           | Used to multiply floats           |                             |
| `fdiv`           | Used for floating point division. | Can cause real-time errors. |
| `fptrunc`           | Floating point truncation from an fN to an fM where N>M |  |
| `fpext`           | Floating point extenstion from an fM to an fN where N>M |  |
|                  |                                   |                             |

## Runtime Functions

The following runtime functions must be supported by all backends:

| Function                            | Signature            | Description                                                                                                                                                                                                                                                  |
| :---------------------------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__initialize           | `void(i8*)`          | Initializes the execution environment. Sets all qubits to a zero-state if they are not dynamically managed.                                                                                                                                                 |
| __quantum__rt__tuple_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.  |
| __quantum__rt__array_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__result_record_output | `void(%Result*,i8*)` | Adds a measurement result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |

The following output recording functions can appear if you opt into supporting
real-time integer calculations.

| Function                         | Signature       | Description                                                                                                                                                                                              |
| :------------------------------- | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__int_record_output | `void(i64,i32,i8*)` | Adds an integer result to the generated output. The second parameter defines the integer precision, and the third one a string label for the result value. Depending on the output schema, the label is included in the output or omitted.        |

The following output recording functions can appear if you opt into supporting
real-time floating point computations.

| Function                            | Signature       | Description                                                                                                                                                                                                                    |
| :---------------------------------- | :-------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__float_record_output | `void(f64,i32,i8*)` | Adds a floating-point value result to the generated output. The second parameter defines the floating-point precision, and the third one defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted. |

Additionally, a backend can provide more `rt` functions that can be used by
Adaptive Profile programs in accordance with the classical data types that it
supports.

### Initialization

*A [workstream](https://github.com/qir-alliance/qir-spec/issues/11) to specify
how to initialize the execution environment is currently in progress. As part of
that workstream, this paragraph and the listed initialization function(s) will
be updated.*

### Output Recording

The program output of a quantum application is defined by a sequence of calls to
runtime functions that record the values produced by the computation,
specifically calls to the runtime functions ending in `record_output` listed in
the tables [above](#runtime-functions). In the case of the Adaptive Profile,
these calls are contained within the final block of the entry point function,
i.e. the block that terminates in a return instruction. In the case that
conditional data needs to be returned, then phi instructions are expected to be
used to move conditional data into the final block of the entry-point function.

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

Within the Adaptive Profile, defining local variables is supported via reading
mid-circuit measurements via (**Bullet 2**) or by classical instructions and
calls (**Bullet 5**) if a backend supports these features. This implies the
following:

- Call arguments can be constant values, `inttoptr` casts, `getelementptr`
  instructions that are inlined into a call instruction, or classical registers.
- backends can have various numeric data types used in their instructions if
  they opt in to using the classical types specified in  **Bullet 5**.

Constants of any type are permitted as part of a function call. What data types
occur in the program hence depends on what QIS functions are used in addition to
the runtime functions for initialization and output recording. Constant values
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

### Qubit and Result Usage

Qubits and result values are represented as opaque pointers in the bitcode,
which may only ever be dereferenced as part of a runtime function
implementation. In general, the QIR specification distinguishes between two
kinds of pointers for representing a qubit or result value, as explained in more
detail [here](../Execution.md), and either one, though not both, may be used
throughout a bitcode file. A [module flag](#module-flags-metadata) in the
bitcode indicates which kinds of pointers are used to represent qubits and
result values.

The first kind of pointer points to a valid memory location that is managed
dynamically during program execution, meaning the necessary memory is allocated
and freed by the runtime. The second kind of pointer merely identifies a qubit
or result value by a constant integer encoded in the pointer itself. To be
compliant with the Adaptive Profile specification, the program must not make use
of dynamic qubit or result management, meaning it must use only the second kind
of pointer; qubits and results must be identified by a constant integer value
that is bitcast to a pointer to match the expected type. How such an integer
value is interpreted and specifically how it relates to hardware resources is
ultimately up to the executing backend.

Additionally, the Adaptive Profile imposes the following restrictions on qubit
and result usage:

- Qubits must not be used after they have been passed as arguments to a function
  that performs an irreversible action. Such functions are marked with the
  `irreversible` attribute in their declaration.

- Results can only be used either as `writeonly` arguments, as arguments to
  [output recording functions](#output-recording), or as arguments to the
  measurement result to boolean conversion function (**Bullet 2**). We refer to
  the [LLVM
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
that is declared but not defined. For the Adaptive Profile, this implies that
they can occur only in one place.

Within the restrictions imposed by the Adaptive Profile, the number of qubits
that are needed to execute the quantum program must be known at compile time.
This number is captured in the form of the `"required_num_qubits"` attribute
attached to the entry point. The value of the attribute must be the string
representation of a non-negative 64-bit integer constant.

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

The following [module
flags](https://llvm.org/docs/LangRef.html#module-flags-metadata) may be added to
the QIR bitcode to indicate support/use of optional capabilities. A lack of
these module flags indicates that these capabilities are not used in the
program.

- a flag with the string identifier `"int_computations"` that contains a string
  value where the string value is a comma-separated list of the supported/used
  integer precision(s). For example, `!0 = !{i32 5, !"int_computations",
  !"i32,i64"}`. Classical computations on integers of all listed precisions must
  be supported by the executing backend. An empty value indicates that no
  integer computations are supported/used.
- a flag with the string identifier `"float_computations"` that contains a
  string value where the string value is a comma-separated list of the
  supported/used floating-point precision(s). For example, `!0 = !{i32 5,
  !"float_computations", !"f32,f64"}`. The precision must be one of the LLVM
  recognized values (f16, f32, f64, f80, or f128), and classical computations on
  floating point numbers of all listed precisions must be supported by the
  executing backend. An empty value indicates that no floating-point
  computations are supported/used.
- a flag with the string identifier `"fixedpoint_computations"` that contains a
  string value where the string value is a comma-separated list of the
  supported/used fixed-point precision(s). For example, `!0 = !{i32 5,
  !"fixedpoint_computations", !"i4,i8"}`. The value of this module flag may only
  be non-empty if integer computations are supported. To support fixed-point
  arithmetic for a precision `N`, a backend must be able to perform integer
  computations with precision `2N`, and it must be able to process constant
  integer values of type `i32` being passed as scale. See also the [LLVM
  Language
  Reference](https://llvm.org/docs/LangRef.html#fixed-point-arithmetic-intrinsics).
  An empty value indicates that no fixed-point computations are supported/used.
- A flag named `"ir_functions"` that contains a constant `true` or `false` value
  of type `i1` value indicating if subroutines may be expressed a functions
  which can be called from the entry-point.
- A flag named `"backwards_branching"`  with a boolean i1 value indicating if
  the program uses branch instructions that causes "backwards" jumps in the
  control flow.
- A flag named `"multiple_target_branching"`  with a constant `true` or `false`
  value of type `i1` indicating if the program uses the switch instruction in
  llvm.

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
usage](#qubit-and-result-usage), an Adaptive Profile-compliant program must not
make use of dynamic qubit or result management. The value of both module flags
hence must be set to `false`.

For `i1`, `i64`, `f64`, ... values created by mid-circuit measurement, extern
functions, or classical computations the assumption is that while a `%Result*`
may point to a valid memory location in RAM or some other memory pool, by
default, instructions performed on virtual registers with these data types
correspond to these values being stored in integer or floating registers when an
instruction is executed. Before a virtual register is used in an instruction,
there is no assumption that the value in the virtual register always corresponds
to a physical register. For example, when considering register coloring, the
virtual register, `%0`, in the QIR program may refer to a value stored in RAM
for most of its lifetime before being loaded into a register when an instruction
operates on `%0`. backends should specify any constraints on classical compute
support on this
[page](./Adaptive_Hardware/providers.md#backend-support-for-adaptive-profile).

## Error Messages

Two forms of error messages can occur as a result of the submission of adaptive
profile programs to a backend:

1. Compile-time error messages.
2. runtime error messages.

The compile-time error messages can occur when a backend doesn't support some of
the optional features from **Bullets 5-9**. If upon inspecting a module flag,
the backend determines that the Adaptive Profile program uses features not
supported by the backend, then a compile-time error message should be provided.

The runtime error messages can occur when opting into features such as the
classical computations in **Bullets 5**. An Adaptive Profile program that
undergoes a real-time classical error (for example unchecked division by zero)
has undefined behavior, and a backend is free to execute an undefined behavior.
Programs can also check computations and provide error code by returning a value
supported by a classical data type in a program, assuming a classical type
specified in **Bullet 5** is supported.

## LLVM 15 Opaque Pointers

The transition of LLVM in LLVM 15 and on means that the `%Result*` and `%Qubit*`
representations of qubits and measurement results will no longer be valid.
Establishing a baseline LLVM version is not the point of this workstream. After
discussions around LLVM 15 and on support resolve, this spec will be updated on
how to indicate an Adaptive Profile program pre-LLVM 15 and for LLVM 15 and on.
The changes to these pointer representations are orthogonal to the concerns of
the Adaptive Profile other than that the signature of the measurement
instruction must necessarily change to represent how measurement results are
actually converted into `i1` values. See the discussion on this
[upgrade](https://github.com/qir-alliance/qir-spec/issues/30).

## Examples

For example, consider a backend that supports integer computations and provides
a runtime function for random number generation. Then an Adaptive Profile
program may contain code like the following to do randomized benchmarking:

```llvm
%0 = call i64 @__quantum__rt__rand_range(i64 0, i64 2)
%1 = icmp eq i64 %0, 0
br i1 %1, label %zero_rand_sequence, label %one_rand_sequence
```

By combining mid-circuit measurements with instructions on classical data types,
you can conditionally apply gates based on logic using multiple mid-circuit
measurements and boolean computations:

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

Consider a backend that supports IR-defined functions and provides a `cnot`
instruction as part of the QIS, but not `swap`. Defining and calling a `swap`
function may then greatly reduce code size for a program that involves frequent
use of swaps between qubits:

```llvm
define void @swap(%Qubit* %arg1, %Qubit* %arg2) {
call void __quantum__qis__cnot__body(%Qubit* %arg1, %Qubit* %arg2)
call void __quantum__qis__cnot__body(%Qubit* %arg2, %Qubit* %arg1)
call void __quantum__qis__cnot__body(%Qubit* %arg1, %Qubit* %arg2)
}

define void @main() {
...
call void @swap(%Qubit* null, %Qubit* nonnull inttoptr (1 to %Qubit*))
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
