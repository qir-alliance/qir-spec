# Adaptive Profile Main Questions

1. Adaptive Profile as a parametrized family of profiles (so different back-ends can mix and match features) up to some maximum profile?
2. Enforcing non-termination in program structure or leave to back-ends to enforce non-termination?
3. Extern functions that aren't part of the profile or the instruction set?

# Adaptive Profile

This profile defines a subset of the QIR specification to support a coherent set
of functionalities and capabilities that might be offered by a quantum backend.
Like all profile specifications, this document is primarily intended for
[compiler backend](https://en.wikipedia.org/wiki/Compiler#Back_end) authors as
well as contributors to the [targeting
stage](../Compilation_And_Targeting.md#targeting) of the QIR compiler.


The Adaptive Profile specifies supersets of the base profile that enables 
control flow based on mid-circuit measurements and classical computations
within coherence times. A back-end can support this profile by supporting
a minimum set of features beyond the base profile and can opt-in for
features beyond that.
This marks the first attempt at defining
a profile greater in scope than the base profile but still limited when
compared to the full QIR specification. 

Being a superset of the base profile means that these 3 *capabilities* must be implemented (a few restrictions are removed from the base profile):

1.  An Adaptive Profile program can execute a sequence of quantum instructions 
    that transform the quantum state.
2.  An Adaptive Profile program can measure any qubit used in the program and thus 
	a back-end must be able to measure the state of all qubits for use in program output generation.
3.  An Adaptive Profile program must produce one of the specified [output schemas](../output_schemas/).

Minimum capability additions to the base profile an Adaptive Profile supporting back-end must be able to support:

4. Conditional branching (the profile must support the `br` instruction assuming that the instruction only expresses non-loop control flow).
5. Mid-circuit measurement (`quantum__qis__mz__body` or some other measurement function must be supported in the quantum instruction set).
6. Conditional quantum operations in the instruction set that appear in the target basic blocks of a `br` instruction must be performed conditionally
   as with a classical LLVM program.
7. A `qis` function to turn a measurement result into a boolean (`__quantum__qis__read_result__body`) must be in the instruction set.


Beyond this, a back-end can opt into one or more of the following additional capabilities to extend minimal
Adaptive Profile compliance with additional features. A maximal Adaptive Profile program adds
all of the following capabilities. The extended possible Adaptive Profile capabilities a program can express are:

8.  Qubit resetting (`__quantum__qis__reset__body` supported in the instruction set).
9.  Classical computations involving numeric representations
    (integers and floating point numbers of a fixed size).
10.  User defined functions and function calls.
11.  Non-constant floating point arguments to instruction set functions.
12. Calling classical extern functions.
13. Backwards branching.
14. A parametrized entry point function and a function marked with the "shot_loop" attribute. The "entry_point" function
demarcates the parametrized quantum program to execute, and the funciton with the "shot_loop" attribute defines a loop
to call the "entry_point" function.
   
Thus, any back-end that supports capabilities 1-7 and as many of capabilities 8-14 that they desired
is considered as supporting Adaptive Profile programs.
Ideally, tools should be able
to indicate what capabilities of the Adaptive Profile a back-end is implementing
and should run a verification pass to ensure capabilities of the Adaptive Profile
a back-end are not implementing are properly rejected.
More details about each of the capabilities
are outlined below.

**Bullet 1: Quantum transformations** <br/>

The set of available instructions that transform the quantum state may vary
depending on the targeted backend. The profile specification defines how to
leverage and combine the available instructions to express a program, but does
not dictate which quantum instructions may be used. Targeting a program to a
specific backend requires choosing a suitable profile and quantum instruction
set (QIS). Both can be chosen largely independently, though certain instruction
sets may be incompatible with this (or other) profile(s). The section on the
[quantum instruction set](#quantum-instruction-set) defines the requirements for
a QIS to be compatible with the Adaptive Profile. 
More information about the role of
the QIS, recommendations for front- and backend providers, as well as the
distinction between runtime functions and quantum instructions can be found in
[this document](../Instruction_Set.md).

**Bullet 2: Measurements** <br/>

The second requirement relieves a restriction from the base profile that qubits
can only be measured at the end of the program and that no quantum operations
can be performed on a measured qubit. 
The only requirement here is that all qubits must be measurable, but
there are no restrictions on when these measurements are made, and there is
no restriction necessitating that all qubits be measured. I.E. it's perfectly
valid to measure a subset of qubits used in the program, not have all measured
qubits in the output, and perform the measurements at different points.

**Bullet 3: Program output** <br />

There is no change to output specifications with respect to the base profile.

The specification of QIR and all its profiles needs to permit to accurately
reflect the program intent. This includes being able to define and customize the
program output. The Base Profile specification hence requires explicitly
expressing which values/measurements are returned by the program and in which
order. How to express this is defined in the section on [output
recording](#output-recording).

While it is sufficient for the QPU to do a final measurement of all qubits in a
predefined order at the end of the program, only the selected subset will be
reflected in the produced output schema. A suitable output schema can be 
generated in a post-processing step after the computation on the quantum
processor itself has completed; customization of the program output hence does
not require support on the QPU itself.

The defined [output schemas](../output_schemas/) provide different options for
how a backend may express the computed value(s). The exact schema can be freely
chosen by the backend and is identified by a string label in the produced
schema. Each output schema contains sufficient information to allow quantum
programming frameworks to generate a user-friendly presentation of the returned
values in the requested order, such as, e.g., a histogram of all results when
running the program multiple times.

**Bullet 4: Forward branching** <br />
The Adaptive Profile can allow for arbitrary forward branching with the restriction being that
branch instructions cannot express programs that do not terminate. By default, support for
backwards branching is not a requirement, though a back-end can opt into **13** to support
backwards branching.
Moreover, it's allowable that gates are conditionally performed based on the
control flow to various blocks based on **6**.
Depending on the vector of capabilities defined by an Adaptive Profile program, 
proving non-termination with a static analysis may impossible due to the capabilities
forming a Turing-complete subset of LLVM. Thus, it is up to back-ends to enforce 
termination guarantees via a means of their choosing (for example a watchdog process
with a timeout that will kill an executing Adaptive Profile program if it takes
too much time). The following forms of branch instructions can be supported in the 
profile. :
| LLVM Instruction         | Context and Purpose                                                                              | Rules for Usage                                                                                             |
| :----------------------- | :----------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `br i1 label %true_branch, label %false_branch`                   | Branch to one of two target blocks. | Cannot be used to implement a non-terminating loop.     |
| `switch i64 %reg, label %otherwise [i64 0, %zero_branch i64 1, %one_branch ... i64 n, %n_branch]`                     | Used to branch to one of many objects based on an integer key.                            | Cannot be used to implement a non-terminating loop. |
| `select i1 %0, i64 %true_reg, i64 %false_reg`                    | conditionally select the value in a register. | Cannot be used to implement a non-terminating loop.                            |



The `br` instruction represents a usual if-then-else style jump dependent on 
a boolean, whereas the `switch` instruction is similar to a switch statement in a high
level language, and finally the `select` instruction conditionally evaluates to a register's
value depending on the boolean input. A hardware provider can opt into supporting
some subset of the above instructions (for example br and select but not switch, etc.).
Other branch terminators that involve indirect jumps, function calls, or exception
handling are not supported in Adaptive Profile programs.

**Bullet 5: Mid-circuit measurement** <br />
The Adaptive Profile allows for mid-circuit measurement to be expressed in
programs by removing restrictions on the ```llvm __quantum__qis__mz__body```
function that state that measurements occur at the end of the quantum program
and that the only instructions following them are output recording functions.
If a back-end opts into using this feature then it allows for programs with
the following structure:

```llvm
call quantum__qis__h__body(%Qubit* null) ; arbitrary gate here
...
call quantum__qis__mz__body(%Qubit* null, %Result* null)
call quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*)) ; arbitrary gate choice again
...
```

**Bullet 6: Conditional Quantum Operations** <br />
Although forward branching can be useful when combined with purely classical operations
within a quantum program, the real uitility is being able to conditionally perform gates
as part of things like repeat-until-success or quantum-error-correction routines in
quantum programs.

Here is an example program that mixes mid-circuit measurement (**Bullet 5**), a `qis` function to 
convert a measurement result to a boolean (**Bullet 7**), and a branch instruction (**Bullet 4**) to control
how gates are applied based on mid-circuit measurement.
```llvm
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  %0 = tail call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %0, label %then, label %continue
then:                                   ; preds = %entry
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  br label %continue__1.i.i.i

continue:
...
```

**Bullet 7: Measurement Results to Booleans** <br />
A function to turn measurement results into classical data, mid-circuit, is critical to using
forward branching and conditional quantum execution.

```llvm
%0 = tail call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %0, label %then, label %continue
```

**Bullet 8: Qubit resetting** <br />
If a back-end opts into supporting this feature, then we can allow
for an instruction to reset qubits back to the |0> state to be defined
in the instruction set. This can be illustrated by the following program:

```llvm
call quantum__qis__h__body(%Qubit* null) ; arbitrary gate here
...
call quantum__qis__reset__body(%Qubit* null)
call quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*)) ; arbitrary gate choice again
...
```

This can be combined with the mid-circuit measurement (**Bullet 6**) to allow for the capability to re-use
the same qubit for computations, limiting the amount of qubits required
for redundant calculations and also allowing for circuit width to bet reduced in favor of increasing depth:

```llvm
call quantum__qis__h__body(%Qubit* null) 
call quantum__qis__mz__body(%Qubit* null, %Result* null) ; 1st coin flip
call quantum__qis__reset__body(%Qubit* null)
call quantum__qis__h__body(%Qubit* null) 
call quantum__qis__mz__body(%Qubit* null, %Result* null) ; 2nd coin flip
call quantum__qis__reset__body(%Qubit* null)
```

**Bullet 9: Classical computations** <br />
An Adaptive Profile program may include expressions for numeric and logical computations
that don't involve allocating memory for aggregate data structures. These
can include integer arithmetic calcuations of a back-end specified width, floating
point arithmetic calculations of a back-end specified width, or logical operations
on integers of a back-end specified width.

A back-end implementing classical and arithmetic logic on 64 bit integer and 1 bit boolean types
may have the following instructions they can use:

| LLVM Instruction | Context and Purpose                                        | Note                                                                                       |
|:-----------------|:-----------------------------------------------------------|:-------------------------------------------------------------------------------------------|
| `add`            | Used to add two integers together.                         |                                                                                            |
| `sub`            | Used to subtract two integers.                             |                                                                                            |
| `mul`            | Used to multiply integers                                  |                                                                                            |
| `udiv`           | Used for unsigned division.                                | Can cause real-time errors.                                                                |
| `sdiv`           | Used for signed division.                                  | Can cause real-time errors.                                                                |
| `urem`           | Used for unsigned remainder division.                      | Can cause real-time errors.                                                                |
| `srem`           | Used for signed remainder division.                        | Can cause real-time errors.                                                                |
| `and`            | Bitwise and of two integers.                               |                                                                                            |
| `or`             | Bitwise or of two integers.                                |                                                                                            |
| `xor`            | Bitwise xor of two integers.                               |                                                                                            |
| `shl`            | a left bit shift on a register or number.                  |                                                                                            |
| `lshr`           | Shifts a number the specified number of bits to the right. | No sign extension.                                                                         |
| `ashr`           | Shifts a number the specified number of bits to the right. | Does sign extension.                                                                       |
| `icmp`           | Performs signed or unsigned integer comparisons.           | Different options are: `eq`, `ne`, `slt`, `sgt`, `sle`, `sge`, `ult`, `ugt`, `ule`, `uge`. |
| `zext`           | zero extend an iM to an iN where N>M           |  |
|                  |                                                            |                                                                                            |

Additionally if an Adaptive Profile program has support for floating point computations, the following instructions are supported:
| LLVM Instruction | Context and Purpose               | Note                        |
|:-----------------|:----------------------------------|:----------------------------|
| `fadd`           | Used to add two floats together.  |                             |
| `fsub`           | Used to subtract floats integers. |                             |
| `fmul`           | Used to multiply floats           |                             |
| `fdiv`           | Used for floating point division. | Can cause real-time errors. |
|                  |                                   |                             |

Combining these mid-circuit measurements with some of these classical instructions, you can conditionally apply
gates based on logic on multiple mid-circuit measurements:

```llvm
  tail call void @__quantum__qis__h__body(%Qubit* null)
  tail call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  tail call void @__quantum__qis__reset__body(%Qubit* null)
  %0 = tail call i1 @__quantum__qis__read_result__body(%Result* null)
  tail call void @__quantum__qis__h__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  tail call void @__quantum__qis__mz__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Result* nonnull inttoptr (i64 1 to %Result*))
  tail call void @__quantum__qis__reset__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*))
  %1 = tail call i1 @__quantum__qis__read_result__body(%Result* nonnull inttoptr (i64 1 to %Result*))
  %2 = and i1 %0, %1
  br i1 %2, label %then, label %continue

then:                                   ; preds = %entry
  tail call void @__quantum__qis__x__body(%Qubit* nonnull inttoptr (i64 2 to %Qubit*))
  br label %continue__1.i.i.i

continue:
...
```

Finally, the phi instruction can be used to conditionally move values between branches dependent on control flow:
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

**Bullet 10: User defined functions and function calls** <br />
An Adaptive Profile program may use user defined functions and function calls.
For example, consider that with user defined functions if a back-end has a `Cnot` gate in its instruction set,
then a program that liberally uses `Swap` operations can define a function and call it as follows:
```llvm
define void @swap_0_1() {
call void __quantum__qis__cnot__body(%Qubit* null, %Qubit* nonnull inttoptr (i64 1 to %Qubit*))
call void __quantum__qis__cnot__body(%Qubit* nonnull inttoptr (i64 1 to %Qubit*), %Qubit* null)
call void __quantum__qis__cnot__body(%Qubit* null, %Qubit* nonnull inttoptr (i64 1 to %Qubit*))
}

define void @main() {
...
call void @swap_0_1()
...
}
```

Moreover, classical functions can be defined in the IR assuming that a back-end has opted into supporting
classical computations:

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

The only restriction on user functions and definitions is that you cannot pass `%Qubit*` or `%Result*`
id's to functions nor return them, and these functions can only pass classical 
integer or floating point values allowed by the back-end that have been opted into.

**Bullet 11: Dynamically computed or linked float angles for gates** <br />
If a back-end opts into this feature, non-constant floating point calculations can be used as arguments
to functions in the instruction set. Consider the following program illustrating this:
```llvm
  %0 = mul double 3.14, 2.0
  tail call void @__quantum__qis__rz__body(double %0, %Qubit* null)
```

**Bullet 12: Calling classical extern functions** <br />
Allow for programs to have classical functions that live as extern functions whose 
implementation is provided by a classical program not living in the IR. The extern function
can be marked with an attribute to indicate where the classical function lives (for example 
indicating that the function lives in a C program submitting along with the QIR file):

```llvm
...
declare i1 qec_function(i1 %0, i1 %1, i1 %2, i1 %3) #1

define void main() #0 {
}
...
#0 = { "entry_point" ... }
#1 = { "C" }
```

**Bullet 13: Backwards branching.** <br />
Release the restriction on backwards branching so that a more compact representation of
of loops can be expressed in programs. Here is a program that implements a loop via a
backwards branch that performs coinflips with a qubit and exits the program when the 
coin flip produces a 1.

```llvm
; ModuleID = 'qat-link'
source_filename = "qat-link"

%Qubit = type opaque
%Result = type opaque

define void @simple_loop() local_unnamed_addr #0 {
entry:
  br label %loop
loop:
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  %0 = call i1 @__quantum__qis__read_result__body(%Result* null)
  br i1 %0, label %exit, label %loop
exit:
  ret void
}

declare void @__quantum__rt__int_record_output(i64) local_unnamed_addr

declare void @__quantum__qis__mz__body(%Qubit*, %Result*)

declare i1 @__quantum__qis__read_result__body(%Result*)

declare void @__quantum__qis__h__body(%Qubit*)

attributes #0 = { "entry_point" "requiredQubits"="1" "requiredResults"="1" }
```



**Bullet 14: Shotloop attribute and parametrized entry point** <br />
Support a "shot_loop" attribute on a function defined in the IR that defines a shot loop. 
Additionally, allow the entry point function to have classical parameters and a return value so that
the entry point function can be called from the shot loop and be parameterized in a meaningful manner when
supporting quantum instruction sets with dynamically computed float parameters and also dynamic floating
point calculations.  This can be illustrated
by the following program that also uses floating point external functions that are called
within the shot loop but outside of the entry_point function that executes solely on the QPU
where coherence times are a concern.

```llvm
declare double float_extern_1() #2
declare double float_extern_2() #2
define void @shot_loop() #1 {
entry:
br label %loop

loop:
%0 = phi i64 [0, %entry] [%1, %loop]
%1 = add i64 %0, 1
%2 = call double float_extern_2()
%3 = call double float_extern_3()
call void @main(double %2, double %3)
%4 = icmp i64 ult %1, 1000
br i1 %4, label %loop, label %exit

exit:
ret void
}
define void @main(double %0, double %1) #0 {
call void __quantum__qis__rz__body(double %0, %Qubit* null)
...
call void __quantum__qis__rz__body(double %1, %Qubit* nonnull inttoptr (i64 1 to %Qubit*))
...
}

#0 = { "entry_point" ...}
#1 = { "shot_loop" }
#2 = { "C" }
}
```

## Program Structure

An Adaptive Profile compliant program is defined in the form of a single LLVM bitcode
file that contains the following:

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
  compiler or backend may need to process the bitcode.

The human readable LLVM IR for the bitcode can be obtained using standard [LLVM
tools](https://llvm.org/docs/CommandGuide/llvm-dis.html). For the purpose of
clarity, this specification contains examples of the human readable IR emitted
by [LLVM 13](https://releases.llvm.org/13.0.1/docs/LangRef.html). While the
bitcode representation is portable and usually backward compatible, there may be
visual differences in the human readable format depending on the LLVM version.
These differences are irrelevant when using standard tools to load, manipulate,
and/or execute bitcode.

The code below illustrates how a simple program looks within a Base Profile
representation:

```llvm
; type definitions

%Result = type opaque
%Qubit = type opaque

; global constants (labels for output recording)

@0 = internal constant [3 x i8] c"r1\00"
@1 = internal constant [3 x i8] c"r2\00"

; entry point definition

define i64 @Entry_Point_Name() #0 {
entry:
  ; calls to initialize the execution environment
  call void @__quantum__rt__initialize(i8* null)
  br label %body

body:                                     ; preds = %entry
  ; calls to QIS functions that are not irreversible
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__cnot__body(%Qubit* null, %Qubit* inttoptr (i64 1 to %Qubit*))
  br label %measurements

measurements:                             ; preds = %body
  ; calls to QIS functions that are irreversible
  call void @__quantum__qis__mz__body(%Qubit* null, writeonly %Result* null)
  call void @__quantum__qis__mz__body(%Qubit* inttoptr (i64 1 to %Qubit*), writeonly %Result* inttoptr (i64 1 to %Result*))
  br label %output

output:                                   ; preds = %measurements
  ; calls to record the program output
  call void @__quantum__rt__tuple_record_output(i64 2, i8* null)
  call void @__quantum__rt__result_record_output(%Result* null, i8* getelementptr inbounds ([3 x i8], [3 x i8]* @0, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* getelementptr inbounds ([3 x i8], [3 x i8]* @1, i32 0, i32 0))

  ret i64 0
}

; declarations of QIS functions

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__cnot__body(%Qubit*, %Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, writeonly %Result*) #1

; declarations of runtime functions for initialization and output recording

declare void @__quantum__rt__initialize(i8*)

declare void @__quantum__rt__tuple_record_output(i64, i8*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

; attributes

attributes #0 = { "entry_point" "qir_profiles"="base_profile" "output_labeling_schema"="schema_id" "required_num_qubits"="2" "required_num_results"="2" }

attributes #1 = { "irreversible" }

; module flags

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
```

The program entangles two qubits, measures them, and records a tuple with the
two measurement results.

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

Unless a back-end opts into **Bullet 14** as a capability, then the 
the entry point may not take any parameters and must return an exit code in the
form of a 64-bit integer. The exit code `0` must be used to indicate a
successful execution of the program. Exit code `1` can be used to illustrate
that a real-time error occurred in the execution of the program dependent
upon what features a back-end opts into when supporting an Adaptive Profile program.
For example, with **Bullet 9/12** classical code may encounter errors like division
by zero that can cause a an entry-point function.

The adaptive profile program makes no restrictions on the structure of basic blocks within
the entry point function, other than that a block cannnot jump to a previously encountered block 
in the control flow graph unless a back-end opts into **Bullet 13**. By default adaptive profile
programs limit branching to only express forward branching and nested conditionality. Additionally,
the only functions that can be called by default in the entry block are `qis` or `rt` functions defined
in the instruction set and profile. This restriction is removed if a back-end opts into **Bullet 10/12**
which allows for user-defined functions or the declaration of external functions that may be called that
correspond to classical functions not defined as part of the profile.

<!-- The function body consists of four [basic -->
<!-- blocks](https://en.wikipedia.org/wiki/Basic_block), connected by an -->
<!-- unconditional branching that terminates a block and defines the next block to -->
<!-- execute, i.e., its successor. Execution starts at the entry block and follows -->
<!-- the [control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) -->
<!-- defined by the block terminators; block names/block identifiers may be chosen -->
<!-- arbitrarily, and the order in which blocks are listed in the function definition -->
<!-- may deviate from the [example above](#program-structure). The final block is -->
<!-- terminated by a `ret` instruction to exit the function and return the exit code. -->

<!-- The entry block contains the necessary call(s) to initialize the execution -->
<!-- environment. In particular, it must ensure that all used qubits are set to a -->
<!-- zero-state. The section on [initialization functions](#initialization) defines -->
<!-- how to do that. -->

<!-- The successor of the entry block continues with the main program logic. This -->
<!-- logic is split into two blocks, separated again by an unconditional branch from -->
<!-- one to the other. Both blocks consist (only) of calls to [QIS -->
<!-- functions](#quantum-instruction-set). Any number of such calls may be performed. -->
<!-- To be compatible with the Base Profile the called functions must return void. -->
<!-- Any arguments to invoke them must be inlined into the call itself; they must be -->
<!-- constants or a pointer representing a [qubit or result -->
<!-- value](#data-types-and-values). -->

<!-- The only difference between these two blocks is that the first one contains only -->
<!-- calls to functions that are *not* marked as irreversible by an attribute on the -->
<!-- respective function declaration, whereas the second one contains only calls to -->
<!-- functions that perform irreversible actions, i.e. measurements of the quantum -->
<!-- state. The section on the [quantum instruction set](#quantum-instruction-set) -->
<!-- defines the requirement(s) regarding the use of the `irreversible` attribute, -->
<!-- and the section on [qubit and result usage](#qubit-and-result-usage) details -->
<!-- additional restrictions for using qubits and result values. -->

<!-- The final block contains (only) the necessary calls to record the program -->
<!-- output, as well as the `ret` instruction that terminates the block and returns -->
<!-- the exit code. The logic of this block can be done as part of post-processing -->
<!-- after the computation on the QPU has completed, provided the results of the -->
<!-- performed measurements are made available to the processor generating the -->
<!-- requested output. More information about the [output -->
<!-- recording](#output-recording) is detailed in the corresponding section about -->
<!-- [runtime functions](#runtime-functions). -->

## Quantum Instruction Set

For a quantum instruction set to be fully compatible with the Adaptive Profile, it
must satisfy the following three requirements:

- All functions must return `void`, `iN`, or `fN` types (`i1` and `i64` for example). 
  Functions that measure qubits must take the qubit pointer(s) as well as the result pointer(s) as arguments.

- Functions that perform a measurement of one or more qubit(s) must be marked
  with an custom function attribute named `irreversible`. The use of
  [attributes](#attributes) in general is outlined in the corresponding section.

For more information about the relation between a profile specification and the
quantum instruction set we refer to the paragraph on [Bullet 1](#base-profile)
in the introduction of this document. For more information about how and when
the QIS is resolved, as well as recommendations for front- and backend
developers, we refer to the document on [compilation stages and
targeting](../Compilation_And_Targeting.md).

## Classical Instructions

The following instructions are the LLVM instructions that were permitted
within a Base Profile compliant program:

| LLVM Instruction         | Context and Purpose                                                                              | Rules for Usage                                                                                             |
| :----------------------- | :----------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a basic block to invoke any one of the declared QIS functions and runtime functions. | May optionally be preceded by a [`tail` marker](https://llvm.org/docs/LangRef.html#call-instruction).       |
| `br`                     | Used to branch from one block to another in the entry point function.                            | The branching must be unconditional and occurs as the final instruction of a block to jump to the next one. |
| `ret`                    | Used to return the exit code of the program.                                                     | Must occur (only) as the last instruction of the final block in the entry point.                            |
| `inttoptr`               | Used to cast an `i64` integer value to either a `%Qubit*` or a `%Result*`.                       | May be used as part of a function call only.                                                                |
| `getelementptr inbounds` | Used to create an `i8*` to pass a constant string for the purpose of labeling an output value.   | May be used as part of a call to an output recording function only.                                         |

The Adaptive Profile extends the base profile with additional instructions such as `br` (**Bullet 4**) and the additional opt-in instructions in (**Bullet 9**)

See also the section on [data types and values](#data-types-and-values) for more
information about the creation and usage of LLVM values.

## Runtime Functions

The following runtime functions must be supported by all backends, and are the
only runtime functions that may be used as part of a Base Profile compliant
program:

| Function                            | Signature            | Description                                                                                                                                                                                                                                                  |
| :---------------------------------- | :------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __quantum__rt__initialize           | `void(i8*)`          | Initializes the execution environment. Sets all qubits to a zero-state if they are not dynamically managed.                                                                                                                                                  |
| __quantum__rt__tuple_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.  |
| __quantum__rt__array_record_output  | `void(i64,i8*)`      | Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted. |
| __quantum__rt__result_record_output | `void(%Result*,i8*)` | Adds a measurement result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__int_record_output | `void(i64,i8*)` | Adds an integer result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__int32_record_output | `void(i32,i8*)` | Adds an 32-bit integer result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__double_record_output | `void(f64,i8*)` | Adds a double precision floating point value result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__f32_record_output | `void(f32,i8*)` | Adds an 32-bit floating point value result to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |
| __quantum__rt__bool_record_output | `void(i1,i8*)` | Adds a boolean value to the generated output. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.                                                         |

### Initialization

*A [workstream](https://github.com/qir-alliance/qir-spec/issues/11) to specify
how to initialize the execution environment is currently in progress. As part of
that workstream, this paragraph and the listed initialization function(s) will
be updated.*

### Output Recording

The program output of a quantum application is defined by a sequence of calls to
runtime functions that record the values produced by the computation,
specifically calls to the runtime functions ending in `record_output` listed in
the table [above](#runtime-functions). In the case of the Adaptive Profile, these
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
the frontend, the choice of output schema on the other hand is up to the
backend. A backend may reject a program as invalid or fail execution if a label
is missing.

Both the labeling schema and the output schema are identified by a metadata
entry in the produced output. For the [output schema](../output_schemas/), that
identifier matches the one listed in the corresponding specification. The
identifier for the labeling schema, on the other hand, is defined by the value
of the `"output_labeling_schema"` attribute attached to the entry point.

## Data Types and Values

Within the Adaptive Profile, defining local variables is supported via
reading mid-circuit measurements via (**Bullet 7**) or by classical instructions
and classical extern calls (**Bullet 9** or **Bullet 12**) if a back-end supports
these features. This implies the
following:

- Call arguments can be constant values, `inttoptr` casts, 
  `getelementptr` instructions that are inlined into a call instruction, or
  classical registers.
- Back-ends can have various numeric data types used in their instructions
  if they opt in for **Bullet 9** or **Bullet 12**.

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

Due to **Bullet 7**, the `i1` type must be supported by Adpative profile back-ends.
Other types like `i64` and `f64` are opt-in types depending on the capabilities
a back-end wants to support.

### Qubit and Result Usage

Qubits and result values are represented as opaque pointers in the bitcode,
which may only ever be dereferenced as part a runtime function implementation.
In general, the QIR specification distinguishes between two kinds of pointers
for representing a qubit or result value, as explained in more detail
[here](../Execution.md), and either one, thought not both, may be used
throughout a bitcode file. A [module flag](#module-flags-metadata) in the
bitcode indicates which kinds of pointers are used to represent qubits and
result values.

The first kind of pointer points to a valid memory location that is managed
dynamically during program execution, meaning the necessary memory is allocated
and freed by the runtime. The second kind of pointer merely identifies a qubit
or result value by a constant integer encoded in the pointer itself. To be
compliant with the Adpative Profile specification, the program must not make use of
dynamic qubit or result management, meaning it must use only the second kind of
pointer; qubits and results must be identified by a constant integer value that
is bitcast to a pointer to match the expected type. How such an integer value is
interpreted and specifically how it relates to hardware resources is ultimately
up to the executing backend.

Additionally, the Adaptive Profile imposes the following restrictions on qubit and
result usage:

- Qubits must not be used after they have been passed as arguments to a function
  that performs an irreversible action. Such functions are marked with the
  `irreversible` attribute in their declaration.

- Results can only be used either as `writeonly` arguments, as arguments to
  [output recording functions](#output-recording), or as arguments to the 
  measurement to boolean function. We refer to the [LLVM
  documentation](https://llvm.org/docs/LangRef.html#function-attributes)
  regarding how to use the `writeonly` attribute.

## Attributes

The following custom attributes must be attached to the entry point function:

- An attribute named `"entry_point"` identifying the function as the starting
  point of a quantum program
- An attribute named `"qir_profiles"` with the value `"base_profile"`
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
- An attribute named `"shot_loop"` identifying the function to hold the shoot
  loop may appear if a back-end opts into **Bullet 14**.

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
by multiple function definitions or global variables. Consumers of Daptive Profile
compliant programs must not rely on a particular numbering, but instead look for
the function to which an attribute with the name `"entry_point"` is attached to
determine which one to invoke when the program is launched.

Both the `"entry_point"` attribute and the `"output_labeling_schema"` attribute
can only be attached to a function definition; they are invalid on a function
that is declared but not defined. For the Adaptive Profile, this implies that they
can occur only in one place.

Within the restrictions imposed by the Adaptive Profile, the number of qubits that
are needed to execute the quantum program must be known at compile time. This
number is captured in the form of the `"required_num_qubits"` attribute attached
to the entry point. The value of the attribute must be the string representation
of a non-negative 64-bit integer constant.

Similarly, the number of measurement results that need to be stored when
executing the entry point function is captured by the `"required_num_results"`
attribute. <!-- Since qubits cannot be used after measurement, in the case of the -->
<!-- Base Profile, this value is usually equal to the number of measurement results -->
<!-- in the program output. -->

Beyond the entry point specific requirements related to attributes, custom
attributes may optionally be attached to any of the declared functions. The
`irreversible` attribute in particular impacts how the program logic in the
entry point is structured, as described in the section about the [entry point
definition](#function-body). Furthermore, the following [LLVM
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
major and minor version of the specification that the QIR bitcode adheres to.

- Since the QIR specification may introduce breaking changes when updating to a
  new major version, the behavior of the `"qir_major_version"` flag must be set
  to `Error`; merging two modules that adhere to different major versions must
  fail.

- The QIR specification is intended to be backward compatible within the same
  major version, but may introduce additional features as part of newer minor
  versions. The behavior of the `"qir_minor_version"` flag must hence be `Max`,
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
usage](#qubit-and-result-usage), an Adaptive Profile compliant program must not make
use of dynamic qubit or result management. The value of both module flags hence
must be set to `false`.
