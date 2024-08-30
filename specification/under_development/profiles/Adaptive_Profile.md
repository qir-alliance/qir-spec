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
   execution of the program. Qubits not undergoing the measurement should not
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
is always guaranteed to terminate, i.e. there are no control flow loops
permitted that would lead to a potentially indefinitely running program.

Beyond the providing the required capabilities above, a backend can opt into one
or more of the following [optional capabilities](#optional-capabilities) to
support more advanced adaptive computations:

<!-- markdownlint-disable MD029 -->
5. Computations on classical (non-composite) data types, specifically on
   integers or floating-point numbers.
6. IR-defined functions and calls of these functions at any point in the
   program.
7. Backwards branching to express terminating loops. Non-terminating loops
   ("while"-loops) are not permitted within the Adaptive Profile, regardless of
   the support for this optional feature. It is specifically not permitted to
   have a loop that terminates only based on a measurement outcome.
   Correspondingly, permitting for backward branching mostly makes sense when
   the backend also supports computations on at least one classical data type.
8. Multiple target branching.
9. Multiple return points.
<!-- markdownlint-enable MD029 -->

The use of these optional features is represented as a [module
flag](#module-flags-metadata) in the program IR. Any backend that supports
capabilities 1-4, and as many of capabilities 5-9 as it desires, is considered
as supporting Adaptive Profile programs. Static analysis/verification tools
should be able to determine what capabilities of the Adaptive Profile a backend
is implementing and should run a verification pass to ensure Adaptive Profile
programs that are using capabilities not supported by a backend are rejected
with an informative message. More details about each of the aforementioned
capabilities are outlined in the following sections.

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

Additionally, the Adaptive Profile requires that it must be possible to take
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
analysis to determine the validity of the program should check for cycles in the
control flow graph and reject any program with a cycle as invalid unless support
for backward branching is enabled.

While the Adaptive Profile requires that it must be possible to use a qubit
after it was measured, the availability of a `reset` instruction depends on the
QIS supported by the backend. If a single-qubit measurement is supported as part
of the QIS, it is always possible to reset that qubit, if needed for qubit reuse
later in the program, using forward branching as illustrated for example by the
following IR snippet:

```llvm
...
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* writeonly null)
  %0 = tail call i1 @__quantum__rt__read_result(%Result* readonly null)
  br i1 %0, label %then, label %continue
then:                                   ; preds = ...
  tail call void @__quantum__qis__x__body(%Qubit* null)
  br label %continue
continue:
  ...
```

Although forward branching can be useful when combined with purely classical
operations within a quantum program, the real utility is being able to
conditionally perform quantum instructions depending on measurement outcomes,
for example when performing real-time error-correction as part of a quantum
programs.

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
underflow may be undefined. All LLVM instructions that must be available to
support an extended Adaptive Profile including classical computations are listed
in the section on [classical instructions](#classical-instructions).

Which data types are used in classical computations as part of an extended
Adaptive Profile must be indicated in the form of [module
flags](#module-flags-metadata). The module flag(s) specifically also include
information about the bitwidth(s) of the used data type(s). It is the
responsibility of the backend to reject the program if any of the used data
types or widths thereof are not supported.

Support for a classical data type implies that local variables of that data type
may exist at any point in the program. Specifically, it is then also permitted
to pass such variables as arguments to QIS functions, runtime functions, or
IR-defined functions (**Bullet 6**) if available, as illustrated in the
[examples](#examples) section. Passing constant values of any data type as
arguments to QIS and runtime functions is always permitted, regardless of
whether classical computations on that data type are supported.

In addition to local variables, global constants may be defined for any of the
supported classical data types. Such global constants may be used anywhere in
the program where a value of this type can be used.

### Bullet 6: IR-defined functions and function calls

A backend can choose to support an extended Adaptive Profile that includes
IR-defined functions, that is functions whose implementation is defined as part
of the program IR. An Adaptive Profile program that includes IR-defined
functions must indicate this in the form of a [module
flag](#module-flags-metadata).

IR-defined functions may take arguments of type `%Qubit*` and `%Result*`, and it
may either return a value of type `%Result` or choose to have a `void` return
type. If [classical computations](#bullet-5-classical-computations) are
supported in addition to IR-defined functions, then values of the supported data
type(s) may also be passed as arguments to, and returned from, an IR-defined
function. Since the adaptive profile does not include support for composite data
types, such as tuples and arrays, they cannot be passed to or returned from
IR-defined functions.

The body of an IR-defined function may use any of the available [classical
instructions](#classical-instructions). It may call QIS functions and other
IR-defined functions. In contrast to the [entry point
function](#entry-point-definition), an IR-defined function may *not* contain any
calls to [output recording](#output-recording) or initialization functions, but
it may call other runtime functions. Just like for the entry point function,
values of type `%Qubit*` and `%Result*` may only occur in calls to other
functions; qubit values of these types that are passed as arguments cannot be
assigned to local variables, that is they cannot be aliased.

### Bullet 7: Backwards branching

Opting into this capability relieves the restriction on backwards branching so
that a more compact representation of loops can be expressed in programs. Any
use of this optional capability must be indicated in the form of [module
flags](#module-flags-metadata) in the program IR.

Proving non-termination with a static analysis may be impossible due to the
capabilities forming a Turing-complete subset of LLVM. Since there is no static
analysis that can prove termination then it is up to backends to enforce
termination guarantees via a means of their choosing (for example a watchdog
process with a timeout that will kill an executing Adaptive Profile program if
it takes too much time).

```llvm
  ...
  br label %loop
loop:
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* writeonly null)
  %0 = call i1 @__quantum__rt__read_result(%Result* readonly null)
  br i1 %0, label %cont, label %loop
cont:
  ...
```
<!--
Since the Adaptive Profile does not allow for any composite data types,
supporting backwards branching necessarily requires supporting non-constant
values to be used to identify a qubit or result value. For example, the
following IR expresses a loop that flips the state of qubit 1 to 4, if qubit 0
is in a non-zero state:

```llvm
...
define void @simple_loop() {
entry:
  br label %loop_body
loop_body:                          ; preds = %loop_body, %entry
  %0 = phi i64 [ 0, %entry ], [ %1, %loop_body ]
  %1 = add i64 %0, 1
  call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* nonnull inttoptr (i64 %1 to %Qubit*))
  %2 = icmp sle i64 %1, 4
  br i1 %2, label %loop_body, label %loop_exit
loop_exit:                          ; preds = %loop_body
  ...
}
...
```

To ensure termination of the program, the condition for exiting the loop must
not depend on any quantum measurements, since these are non-deterministic in
general. Enforcing this restriction can be done with a static analysis tool,
whereby any expression that may depend on a quantum measurement must be assumed
to depend on it. 
-->

<!--FIXME: "dynamic" qubit indexing allowed here? allowed anywhere else? if not, what can we do with loops?? -->
<!--FIXME: alternative: allow for potential non-termination and the backend deals with this by having a time-out. -->
<!--FIXME: update the module flag depending on which of the two versions - or both - is supported. -->
<!--FIXME: update the data types and values section to say qubits and results must be constant -->
<!--FIXME: update this section here to require that the value used to access qubits and results must not depend on a measurement -->

### Bullet 8: Multiple Target Branching

It can be desirable to support control flow constructs that indicate how a
computation can lead to branching to one of *many* different execution paths.
Having such a construct exposed in the IR allows for more aggressive
optimizations across different blocks without any dependencies between them. A
backend may hence opt into supporting `switch` instructions to facilitate such
optimizations. An Adaptive Profile program that includes `switch` instructions
must indicate this in the form of a [module flag](#module-flags-metadata).

For this capability to be practically useful, integer computations must be
supported as well (**Bullet 5**). For example, the snippet below causes a jump
to a block `onzero`, `onone`, `ontwo`, or `otherwise` respectively, depending on
the value of an integer variable `%val`:

```llvm
switch i32 %val, label %otherwise [ i32 0, label %onzero
                                    i32 1, label %onone
                                    i32 2, label %ontwo ]
```

The variable `%val` may, for example, depend on measurement results or a global
constant. We refer to the [LLVM language
reference](https://llvm.org/docs/LangRef.html#switch-instruction) for more
information about the switch instruction.

<!--FIXME: check that the entry point section allows for entry point arguments - global constants as the alternative? -->

### Bullet 9: Multiple Return Points

A backend my choose to support multiple return points in an entry point
function, and IR-defined functions if the optional capability in **Bullet 6** is
supported. This eliminates the need to create `phi` nodes for the purpose of
propagating the computed output to a single final block. Any use of this
optional capability must be indicated in the form of [module
flags](#module-flags-metadata) in the program IR.

A return statement is necessarily always the last statement in a block. For each
block that contains returns a zero exit code in the entry point function, that
same block must also contain the necessary calls to [output recording
functions](#output-recording) to ensure the correct program output is recorded.
If the block returns a non-zero exit code, calls to these functions may be
omitted, implying that no output will be recorded in this case.

For example, an Adaptive Profile program that uses this optional capability may
contain a logic like this:

```llvm
@0 = internal constant [2 x i8] c"0\00"

define i64 @main() local_unnamed_addr #0 {
entry:
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* writeonly null)
  %0 = tail call i1 @__quantum__rt__read_result(%Result* readonly null)
  br i1 %0, label %error, label %exit
error:
  ; qubits should be in a zero state at the end of the program
  ret i64 1
exit:
  call void @__quantum__rt__result_record_output(%Result* null, i8* getelementptr inbounds ([2 x i8], [2 x i8]* @0, i32 0, i32 0))
  ret i64 0
}
```

## Program Structure

An Adaptive Profile-compliant program is defined in the form of a single LLVM
bitcode file that contains the following:

- the definitions of the opaque `Qubit` and `Result` types
- global constants that store [string labels](#output-recording) needed for
  certain output schemas that may be ignored if the [output
  schema](../output_schemas/) does not make use of them
- optionally, and only if classical computations (**Bullet 5**) are supported,
  global constants of the supported classical data types
- the [entry point definition](#entry-point-definition) that contains the
  program logic
- optionally, and only if IR-defined functions (**Bullet 6**) are supported,
  additional functions that are called from the entry point function
- declarations of the [QIS functions](#quantum-instruction-set) used by the
  program
- declarations of [runtime functions](#runtime-functions) used for
  initialization and output recording
- one or more [attribute groups](#attributes) used to store information about
  the entry point, and optionally additional information about other function
  declarations
- [module flags](#module-flags-metadata) that contain information that a
  compiler or backend may need to process the bitcode, including module flags
  that indicate which features of the Adaptive Profile are used

The human-readable LLVM IR for the bitcode can be obtained using standard [LLVM
tools](https://llvm.org/docs/CommandGuide/llvm-dis.html). For clarity, this
specification contains examples of the human-readable IR emitted by [LLVM
13](https://releases.llvm.org/13.0.1/docs/LangRef.html). While the bitcode
representation is portable and usually backward compatible, there may be visual
differences in the human-readable format depending on the LLVM version. These
differences are irrelevant when using standard tools to load, manipulate, and/or
execute bitcode.

The code below illustrates how a simple program implementing a teleport chain
looks within a minimal Adaptive Profile representation:

```llvm
; type definitions

%Result = type opaque
%Qubit = type opaque

; global constants (labels for output recording)

@0 = internal constant [5 x i8] c"0_t0\00"
@1 = internal constant [5 x i8] c"0_t1\00"

; entry point definition

define i64 @TeleportChain() local_unnamed_addr #0 {
entry:
  ; calls to initialize the execution environment
  call void @__quantum__rt__initialize(i8* null)
  br label %body

body:                                       ; preds = %entry
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*), %Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*))
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*), %Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Result* writeonly null)
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  %0 = tail call i1 @__quantum__rt__read_result(%Result* readonly null)
  br i1 %0, label %then__1, label %continue__1

; conditional quantum gate (only one in this block, but many can appear and the full quantum instruction set should be usable)
then__1:                                   ; preds = %body
  tail call void @__quantum__qis__z__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  br label %continue__1

continue__1:                               ; preds = %then__1, %body
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*), %Result* writeonly nonnull inttoptr (i64 1 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  %1 = tail call i1 @__quantum__rt__read_result(%Result* readonly nonnull inttoptr (i64 1 to %Result*))
  br i1 %1, label %then__2, label %continue__2

then__2:                                   ; preds = %continue__1
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  br label %continue__2

continue__2:                               ; preds = %then__2, %continue__1
  tail call void @__quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*), %Qubit* nonnull inttoptr (i64 3 to %Qubit*))
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*), %Result* writeonly nonnull inttoptr (i64 2 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 4 to %Qubit*))
  %2 = tail call i1 @__quantum__rt__read_result(%Result* readonly nonnull inttoptr (i64 2 to %Result*))
  br i1 %2, label %then__3, label %continue__3

then__3:                                   ; preds = %continue__2
  tail call void @__quantum__qis__z__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  br label %continue__3

continue__3:                               ; preds = %then__3, %continue__2
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*), %Result* writeonly nonnull inttoptr (i64 3 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 3 to %Qubit*))
  %3 = tail call i1 @__quantum__rt__read_result(%Result* readonly nonnull inttoptr (i64 3 to %Result*))
  br i1 %3, label %then__4, label %continue__4

then__4:                                   ; preds = %continue__3
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  br label %continue__4

continue__4:                                   ; preds = %continue__3, %then__4
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* writeonly nonnull inttoptr (i64 4 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*), %Result* writeonly nonnull inttoptr (i64 5 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 5 to %Qubit*))
  br label %exit

exit:
  call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 4 to %Result*), i8* getelementptr inbounds ([5 x i8], [5 x i8]* @0, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 5 to %Result*), i8* getelementptr inbounds ([5 x i8], [5 x i8]* @1, i32 0, i32 0))
  ret i64 0
}

; declarations of QIS functions

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*) local_unnamed_addr

declare void @__quantum__qis__h__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__x__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__z__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__reset__body(%Qubit*) local_unnamed_addr

declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

; declarations of runtime functions

declare void @__quantum__rt__initialize(i8*)

declare i1 @__quantum__rt__read_result(%Result* readonly)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

; attributes

attributes #0 = { "entry_point" "qir_profiles"="adaptive_profile" "output_labeling_schema"="schema_id" "required_num_qubits"="6" "required_num_results"="6" }

attributes #1 = { "irreversible" }

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

The program performs gate teleportation involving mid-circuit measurements and
conditionally applied quantum instructions.

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

An entry point function may not take any parameters and must  must return an
exit code in the form of a 64-bit integer. The exit code `0` must be used to
indicate a successful execution of the quantum program. Any other value of the
exit code indicates a failure during execution. The program IR must use exit
codes within the range `1` to `63` to indicate a failure; exit codes that are
larger than `63` are reserved for execution failures detected by the executing
backend. The recorded output always contains the exit code for each shot. If a
shot fails, no other output values may be recorded. See the [output
schemas](../output_schemas/) for more detail.

The Adaptive Profile program makes no restrictions on the structure of [basic
blocks](https://en.wikipedia.org/wiki/Basic_block) within the entry point
function, other than that a block cannot jump to a previously encountered block
in the control flow graph unless it makes use of the optionally supported
capability in **Bullet 7**. Execution starts at the entry block and follows the
[control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) defined
by the block terminators ending when a block terminates in a return (`ret`)
statement. Block names/block identifiers may be chosen arbitrarily, and the
order in which blocks are listed in the function definition is irrelevant for
execution.

The entry block contains the necessary call to initialize the execution
environment as the first instruction to ensure that all used qubits are set to a
zero-state. Calls to runtime functions for initialization may only appear at the
beginning of the program. All subsequent instructions are either function calls,
or any of the supported [LLVM instructions](#classical-instructions). Calls to
[output recording functions](#output-recording) may only be followed by calls to
other output recording functions and the return statement. Calls to QIS
functions, other runtime functions, or IR-defined functions (**Bullet 6**) if
available, can occur at any point after initialization and before output
recording.

## Quantum Instruction Set

For a quantum instruction set to be fully compatible with the Adaptive Profile,
it must satisfy the following three requirements:

- All functions must return `void`, or any of the supported classical data types
  (**Bullet 5**).
- Functions may take values of any type as arguments. Functions that measure
  qubits must take the qubit pointer(s) as well as the result pointer(s) as
  arguments and return `void`.
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

The following table lists all classical instructions the must be supported to
execute a minimal Adaptive Profile program, that is a program that does not make
use of any optional capabilities:

| LLVM Instruction         | Context and Purpose                                                                              | Rules for Usage                                                                                             |
| :----------------------- | :----------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a basic block to invoke any one of the QIS-, IR-, and runtime functions.             | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction).       |
| `br`                     | Used to branch from one basic block to another.                                                  | The branching is the final instruction in any basic block and may conditionally jump to different blocks depending on an `i1` value. |
| `ret`                    | Used to return the exit code of the program.                                                     | Must occur (only) as the last instruction of the final block in an entry point, unless multiple return statements (optional capability) are supported. |
| `inttoptr`               | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`.                       | May be used as part of a function call only.                                                                |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value.   | May be used as part of a call to an output recording function only.                                         |

See also the section on [data types and values](#data-types-and-values) for more
information about the creation and usage of LLVM values.

Additional LLVM instructions, as listed below, must be supported to enable
classical computations (**Bullet 4**) and multiple target branching (**Bullet
8**).

If a backend chooses to support integer computations, then the following LLVM
instructions must be supported:

| LLVM Instruction | Context and Purpose                                                   | Note                                                                                       |
|:-----------------|:----------------------------------------------------------------------|:-------------------------------------------------------------------------------------------|
| `add`            | Adds two signed or unsigned integers.                                    | Overflow behavior is undefined, no support for `nuw` and/or `nsw`.                                                                                         |
| `sub`            | Subtracts two signed or unsigned integers.                                        | Underflow behavior is undefined, no support for `nuw` and/or `nsw`.                                                                                           |
| `mul`            | Multiplies two integers.                       | Overflow/underflow behavior is undefined, no support for `nuw` and/or `nsw`.                                                                                             |
| `udiv`           | Divides two unsigned integers.                                           | Division by zero leads to undefined behavior.                                                                 |
| `sdiv`           | Divides two signed integers.                                             | Division by zero and overflow leads to undefined behavior.                                                               |
| `urem`           | Computes the remainder of a division of two unsigned integers.                                 | Division by zero leads to undefined behavior.                                                                |
| `srem`           | Computes the remainder of a division of two signed integers.                                   | Division by zero and overflow leads to undefined behavior.                                                                |
| `and`            | Computes the bitwise logical AND of two integers.                                          |                                                                                            |
| `or`             | Computes the bitwise logical OR of two integers.                                           |                                                                                            |
| `xor`            | Computes the bitwise logical exclusive OR (XOR) of two integers.                                          |                                                                                            |
| `shl`            | Computes a bitwise left shift of an integer.                             | Behavior when shifting more bits that the bitwidth of the integer is undefined, no support for `nuw`.                                                                                            |
| `lshr`           | Computes a bitwise right shift of an unsigned integer.            | Behavior when shifting more bits that the bitwidth of the integer is undefined, no support for `exact`.                                                                          |
| `ashr`           | Computes a bitwise right shift of a signed integer.            |  Behavior when shifting more bits that the bitwidth of the integer is undefined, no support for `exact`.                                                                      |
| `icmp`           | Compares two signed or unsigned integers.                      | All condition codes as listed in the [LLVM Language Reference](https://llvm.org/docs/LangRef.html#icmp-instruction) must be supported. |
| `zext .. to`           | Extends an integer value to create an integer of greater bitwidth by filling the added bits with zero.                                  | May be used at any point in the program if classical computations on both the input and the output type are supported. May only be used as part of a call to an output recording function if computations on the output type are not supported.                                                             |
| `sext .. to`           | Extends an integer value to create an integer of greater bitwidth by filling the added bits with the sign bit of the integer.               | May be used at any point in the program if classical computations on both the input and the output type are supported. May only be used as part of a call to an output recording function if computations on the output type are not supported.                                                                                            |
| `trunc .. to`           | Truncates the highest order bits of an integer to create an integer of smaller bitwidth.                          | Behavior if the truncation changes the value of the integer is undefined, no support for `nuw` and/or `nsw`. May be used at any point in the program if classical computations on both the input and the output type are supported. May only be used as part of a call to an output recording function if computations on the output type are not supported.                                                                                       |
| `select`         | Evaluates to one of two integer values depending on a boolean condition. |                                                                                            |
| `phi`            | Implement the φ node in the SSA graph representing the function.                   | Must be at the start of a basic block, or preceded by other `phi` instructions.                                                                                           |

For more information about any of these instructions, we refer to the
corresponding section in the [LLVM Language
Reference](https://llvm.org/docs/LangRef.html).

If a backend chooses to support floating point computations, then the following
LLVM instructions must be supported:

| LLVM Instruction | Context and Purpose               | Note                        |
| :--------------- | :-------------------------------- | :-------------------------- |
| `fadd`           | Adds two floating-point values.  |                             |
| `fsub`           | Subtracts two floating-point values. |                             |
| `fmul`           | Multiplies two floating-point values.          |                             |
| `fdiv`           | Divides two floating-point values. | Division by zero leads to undefined behavior, no support for `NaN`. |
| `fpext .. to`           | Casts a value of floating-point type to a larger floating-point type. | May be used at any point in the program if classical computations on both the input and the output type are supported. May only be used as part of a call to an output recording function if computations on the output type are not supported. |
| `fptrunc .. to`           | May be used at any point in the program if classical computations on both the input and the output type are supported. May only be used as part of a call to an output recording function if computations on the output type are not supported. |  |

If the backend chooses to support multiple target branching, the following LLVM
instruction must be supported:

| LLVM Instruction | Context and Purpose               | Note                        |
| :--------------- | :-------------------------------- | :-------------------------- |
| `switch`           | Transfers control flow to one of several different blocks depending on an integer value.  | The integer value that determines the block to jump to must be a constant value unless integer computations are supported.                |

See also the [LLVM Language
Reference](https://llvm.org/docs/LangRef.html#switch-instruction) for more
information about the `switch` instruction.

## Runtime Functions

The following runtime functions must be supported by all backends:

| Function                            | Signature            | Description                                                                                                                                                                                                                                                  |
| :---------------------------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__initialize           | `void(i8*)`          | Initializes the execution environment. Sets all qubits to a zero-state if they are not dynamically managed.                                     |
| __quantum__rt__read_result | `i1(%Result* readonly)` | Reads the value of the given measurement result and converts it to a boolean value. |
| __quantum__rt__tuple_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.  |
| __quantum__rt__array_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__result_record_output | `void(%Result*,i8*)` | Adds a measurement result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__bool_record_output | `void(i1,i8*)` | Adds a boolean value to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |

If a backend chooses to support integer computations, then the following
additional runtime function must be available:

| Function                         | Signature       | Description                                                            |
| :------------------------------- | :-------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__int_record_output | `void(i64,i8*)` | Records an integer value in the generated output. The second parameter defines the string label for the value. Depending on the output schema, the label is included in the output or omitted.        |

If a backend chooses to support floating-point computations, then the following
additional runtime function must be available:

| Function                            | Signature       | Description     |
| :---------------------------------- | :-------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__float_record_output | `void(f64,i8*)` | Records a floating-point value in the generated output. The second parameter defines the string label for the value. Depending on the output schema, the label is included in the output or omitted. |

### Output Recording

The program output of a quantum application is defined by a sequence of calls to
runtime functions that record the values produced by the computation,
specifically calls to the runtime functions ending in `record_output` listed in
the tables [above](#runtime-functions). In the case of the Adaptive Profile,
these calls are contained within each block terminating in a return (`ret`)
statement in the entry point function. Unless the backend supports multiple
return points (**Bullet 9**), there is a single block that contains all calls to
output recording functions followed by the final return statements. Multiple
return statements in the application code can be replaced with suitable `phi`
nodes by the compiler to propagate the data into that block.

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

Within the Adaptive Profile, local variables are created when reading
mid-circuit measurements (**Bullet 2**) or to store classical computations
(**Bullet 5**) if supported. This implies the following:

- Variables of boolean type may be defined, even if the backend supports none of
  the optional extensions to the Adaptive Profile.
- Values of type `%Qubit*` and `%Result*` may only occur in function calls;
  specifically, local variables of these types cannot be created regardless of
  which optional extensions are supported by the targeted backend. See also the
  subsequent paragraphs for more detail.
- Variables of numeric data types may be defined if the backend supports the
  extension in **Bullet 5**. Such variables may be used in the supported [LLVM
  instructions](#classical-instructions) acting on that data type, or in
  function calls.
- Call arguments can be constant values, classical variables, as well as
  `inttoptr` casts or `getelementptr` instructions that are inlined into a call
  instruction.

Constants of any type are permitted as arguments to QIS and runtime functions.
Constant values of type `i64`, for example, are used and permitted as part of
calls to output recording functions regardless of whether integer computations
are supported; see the section on [output recording](#output-recording) for more
details.

### Qubit and Result Usage

The `%Qubit*` and `%Result*` data types must be supported by all backends.
Qubits and results can occur only as arguments in function calls and are
represented as a pointer of type `%Qubit*` and `%Result*` respectively. To be
compliant with the Adaptive Profile specification, the program must not make use
of dynamic qubit or result management, meaning qubits and results must be
identified by a constant integer value that is bitcast to a pointer to match the
expected type. How such an integer value is interpreted and specifically how it
relates to hardware resources is ultimately up to the executing backend.

The integer constant that is cast must be in the interval `[0, numQubits)` for
`%Qubit*` and `[0,numResults)` for `%Result*`, where `numQubits` and
`numResults` are the required number of qubits and results defined by the
corresponding [entry point attributes](#attributes). Since backends may look at
the values of the `required_num_qubits` and `required_num_results` attributes to
determine whether a program can be executed, it is recommended to index qubits
and results consecutively so that there are no unused values within these
ranges.

## Attributes

The attribute usage and requirements of the Adaptive Profile remain the same as
defined in the [Base Profile](./Base_Profile.md#attributes).

## Module Flags Metadata

The Adaptive Profile requires the same mandatory module flags as specified in
the [Base Profile](./Base_Profile.md#module-flags-metadata). Additionally, the
following [module
flags](https://llvm.org/docs/LangRef.html#module-flags-metadata) may be defined
to indicate the use of optional capabilities. A lack of these module flags
indicates that these capabilities are not used in the program.

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
- A flag named `"ir_functions"` that contains a constant `true` or `false` value
  of type `i1` value indicating if subroutines may be expressed a functions
  which can be called from the entry-point.
- A flag named `"backwards_branching"`  with a boolean `i1` value indicating if
  the program uses branch instructions that cause cycles in the control flow
  graph.
- A flag named `"multiple_target_branching"`  with a constant `true` or `false`
  value of type `i1` indicating if the program uses the `switch` instruction in
  llvm.

For non-constant integer and floating-point values the assumption is that while
a `%Result*` may point to a valid memory location in RAM or some other memory
pool, by default, instructions performed on virtual registers with these data
types correspond to these values being stored in integer or floating registers
when an instruction is executed. Before a virtual register is used in an
instruction, there is no assumption that the value in the virtual register
always corresponds to a physical register. For example, when considering
register coloring, the virtual register, `%0`, in the QIR program may refer to a
value stored in RAM for most of its lifetime before being loaded into a register
when an instruction operates on `%0`.

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
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* writeonly null)
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  %0 = tail call i1 @__quantum__rt__read_result(%Result* readonly null)
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Result* writeonly nonnull inttoptr (i64 1 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  %1 = tail call i1 @__quantum__rt__read_result(%Result* readonly nonnull inttoptr (i64 1 to %Result*))
  %2 = and i1 %0, %1
  br i1 %2, label %then, label %continue

then: 
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  br label %continue

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
