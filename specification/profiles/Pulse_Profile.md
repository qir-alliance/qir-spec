# Pulse Profile

This profile defines a subset of the QIR specification for representing
pulse-level control of quantum hardware — the calibrated microwave, RF, or
optical operations that gate-model quantum instructions are ultimately realized
as on physical backends. Like other profile specifications, this document is
intended primarily for
[compiler backend](https://en.wikipedia.org/wiki/Compiler#Back_end) authors and
contributors to the targeting stage of the QIR compiler, and is written to be
self-contained. Where the Base and Adaptive Profiles are distinguished from one
another by how much classical control flow may accompany a sequence of quantum
instructions, the Pulse Profile addresses an orthogonal concern: the
representation of the quantum instructions themselves, at the level of control
channels, frames, and waveforms rather than gates. A backend can support the
Pulse Profile by supporting a minimum set of mandatory capabilities, and can opt
in to one or more additional capabilities — including the dynamic construction
and release of pulse resources at runtime — represented as module flags in the
program IR, following the same conformance model used by the Adaptive Profile's
optional capabilities.

## Definitions and Data Structures

The Pulse Profile introduces three abstract resource types — `Port`, `Frame`,
and `Waveform` — representing pulse-level control abstractions. Consistent with
QIR v2, references to these resources are represented in the LLVM IR as opaque
pointers (ptr); named opaque type definitions are not used, and the pointee
semantics of a given ptr argument are established by this specification rather
than by the LLVM type system, in keeping with the convention already used for
qubit and result references.

<!-- References to Port, Frame, and Waveform resources compose with, and do
not replace, the qubit and result references defined by the QIR
specification. -->

### Port

A Port denotes a hardware-level control endpoint: a physical channel on the
quantum control system through which pulses are emitted or measurements are
acquired. Ports are static properties of the target hardware; in the mandatory
capabilities of this profile, a program does not construct ports, but references
them as declared in module-level metadata (see
[Program Structure](#program-structure)). Two Port references identify the same
physical endpoint if and only if their pointer values are equal.

### Frame

Every Frame reference carries an implicit logical clock: a time value
representing the point in the frame’s timeline at which its next operation will
occur. The absolute origin of the clock is unspecified, but all frames in a
program share the same origin; only differences between clock values are
meaningful. A frame’s clock never decreases and advances only as follows:

- Playing a waveform on the frame advances the frame’s clock by the waveform’s
  duration.
- Inserting a delay on the frame advances the frame’s clock by the delay’s
  duration.
- Acquiring a measurement on the frame advances the frame’s clock by the
  integration duration.
- Synchronizing a frame with other frames advances its clock to the maximum of
  the clocks of all frames being synchronized.

All durations in this specification are expressed in seconds. Updating the
frame’s frequency or phase is instantaneous and does not advance the clock. The
logical clock is a specification-level abstraction that defines program meaning;
it is not observable from within the program. A target runtime is responsible
for realizing it correctly on physical hardware, and must represent it with a
resolution of at most 1 ns and a range sufficient that it cannot wrap or
saturate during the execution of a program (for example, a 64-bit unsigned
integer count of nanoseconds). Each duration is converted to the runtime’s clock
ticks by rounding to the nearest tick.

### Waveform

A Waveform denotes the envelope of a pulse: a description of its `amplitude` and
`phase` modulation as a function of time, independent of any carrier
oscillation. The envelope may be represented as an explicit sequence of
complex-valued samples or as a parameterized closed-form shape (Gaussian, DRAG,
Square, etc.). A waveform is independent of any port or frame: the same waveform
may be played on many frames, and it carries no notion of carrier frequency or
phase — those are supplied by the frame at playback time.

Waveforms are immutable once constructed: an operation that produces a modified
version of an existing waveform produces a distinct Waveform reference and
leaves the original unchanged. The `sample rate` at which a waveform is realized
on physical hardware is a property of the target runtime, not of the waveform
itself; where a waveform is constructed from an explicit sample buffer, the rate
at which that buffer was described is a property of the construction call, not a
persistent property of the resulting reference.

## Mandatory Capabilities

To support the Pulse Profile without any of its optional capabilities, a backend
must support the following mandatory capabilities:

1. It can execute a sequence of pulse-level instructions that manipulate frame
   state and play waveforms on hardware ports, consistent with the per-frame
   timing model defined in this specification.

2. It supports acquiring the state associated with a frame's port at the end of
   the program.

3. It supports declaring Pulse resources — Ports, Frames, and Waveforms via
   module-level metadata and referencing them as compile-time constants, as
   defined in the section on [Program Structure](#program-structure).

4. It produces one of the specified [output schemas](../output_schemas/).

These capabilities are necessary and sufficient to represent pulse-level control
of a fixed set of hardware resources known at compile time, without runtime
resource management or measurement-conditioned branching.

## Optional Capabilities

Beyond the mandatory capabilities above, a backend can opt into one or more of
the following optional capabilities to support more advanced pulse-level
programs:

<!-- markdownlint-disable MD029 -->

5. Dynamic construction and release of Port references at runtime, via the
   `__quantum__rt__pulse__*` functions defined in this specification, rather
   than declaring them via module-level metadata alone. Support for this
   capability is indicated by the `dynamic_port_management` module flag.

6. Dynamic construction and release of Frame references at runtime, allowing a
   frame's **port binding**, **initial frequency**, and **initial phase** to be
   determined by values computed during program execution rather than fixed at
   compile time. Support for this capability is indicated by the
   `dynamic_frame_management` module flag.

7. Dynamic construction and release of Waveform references at runtime, including
   construction from a caller-supplied sample buffer whose contents are computed
   during program execution. Support for this capability is indicated by the
   `dynamic_waveform_management` module flag.

The use of these optional capabilities is represented by module flags in the
program IR, following the same conformance model as the
[Adaptive Profile's optional capabilities](./Adaptive_Profile.md#optional-capabilities).
Any backend that supports capabilities 1–4, and as many of capabilities 5–7 as
it desires, is considered as supporting Pulse Profile programs. A target runtime
must reject, before execution begins, any program that requires a capability the
target backend does not support. Static analysis and verification tools should
be able to determine (via module flags) which capabilities a given program requires so that this
check can also be performed at compile-time.

Capabilities 5–7 are most useful in conjunction with classical-computation or
control-flow capabilities defined elsewhere in the QIR specification — for
example, the Adaptive Profile's optional capabilities for computation on
classical data types. This profile does not require such capabilities and
imposes **no constraint on how the arguments to construction functions are
computed**; a backend may support capabilities 5–7 without also supporting
Adaptive Profile, though the resulting program space is limited to constructing
pulse resources from values already available at the point of construction, such
as loop-invariant or compile-time-derived constants passed in as parameters.

## Program Structure

A Pulse Profile compliant program is defined in an LLVM bitcode file that
contains (at least) the following:

- global constants that store string labels needed for certain
  [output schemas](../output_schemas/) that may be ignored if the output schema
  does not make use of them.

- module-level metadata declaring the `Port`, `Frame`, and `Waveform` resources
  used by the program, as defined in the section on
  [Definitions and Data Structures](#definitions-and-data-structures), for any
  resource type not using the optional dynamic-management capabilities.

- the [entry point definition](#entry-point-definition) that contains the
  program logic.

- declarations of the [QIS functions](#pulse-quantum-instruction-set-pulse-qis)
  used by the program.

- declarations of runtime functions used for initialization and output
  recording, and, only if the corresponding optional capability is supported,
  declarations of the [Pulse Runtime](#pulse-runtime-pulse-rt) functions used
  for dynamic construction and release of pulse resources.

- one or more [attribute groups](#attributes) used to store information about
  the entry point.

- [module flags](#module-flags-metadata) that contain information a compiler or
  backend may need to process the bitcode, including flags indicating which
  optional capabilities are used.

The human-readable LLVM IR for the bitcode can be obtained using standard LLVM
tools. As with other profile specifications, examples in this document reflect
QIR v2 conventions using opaque pointers throughout. The code below illustrates
a Pulse Profile compliant program implementing a single-qubit Ramsey-type
sequence, using only the mandatory capabilities of this profile. Note that the
block labels used in this example are a convention for readability, not a
requirement.:

```llvm

; module-level metadata declaring the pulse resources used by this program
!qir.pulse.ports = !{!5, !6}      ; Two ports
!5 = !{i64 0, !"drive_q0"}
!6 = !{i64 1, !"readout_q0"}

!qir.pulse.frames = !{!7, !8}     ; Two frames
; frame 0: bound to port 0, 5.0 GHz frequency, initial phase=0.0 rad
!7 = !{i64 0, i64 0, double 5.0e9, double 0.0}      ; {frame-id, port-id, frequency, phase}
; frame 1: bound to port 1, 7.0 GHz frequency, initial phase=0.0 rad
!8 = !{i64 1, i64 1, double 7.0e9, double 0.0}

!qir.pulse.waveforms = !{!9}      ; single waveform
; waveform 0, shape="gaussian", amplitude=2.0, standard deviation=8ns(8.0e-8 s), duration=32ns(3.2e-8 s)
!9 = !{i64 0, !"gaussian", double 2.0, double 8.0e-9, double 3.2e-8}

; global constants (labels for output recording)

@0 = internal constant [3 x i8] c"r0\00"

; entry point definition

define i64 @RamseySequence() #0 {
entry:
  ; calls to initialize the execution environment
  call void @__quantum__rt__initialize(ptr null)
  br label %body

body:                                       ; preds = %entry
  ; calls to QIS functions that are not irreversible
  call void @__quantum__qis__pulse__play__body(ptr null, ptr null)              ; args: (frame 0, waveform 0)
  call void @__quantum__qis__pulse__delay__body(ptr null, double 8.0e-9)        ; args: (frame 0, duration)
  call void @__quantum__qis__pulse__shift__phase__body(ptr null, double 1.5707963)  ; args: (frame 0, phase)
  call void @__quantum__qis__pulse__play__body(ptr null, ptr null)              ; args : (frame 0, waveform 0)
  call void @__quantum__qis__pulse__shift__phase__body(ptr null, double -1.5707963)
  br label %measurements

measurements:                               ; preds = %body
  ; Synchronize the frames
  call void (i64, ...) @__quantum__qis__pulse__barrier__body(i64 2, ptr null, ptr nonnull inttoptr (i64 1 to ptr))

  ; calls to QIS functions that are irreversible
  call void @__quantum__qis__pulse__acquire__body(ptr nonnull inttoptr (i64 1 to ptr), double 2.0e-6, ptr writeonly null) ; args : (frame 1, duration, result 0)
  br label %output

output:                                     ; preds = %measurements
  ; calls to record the program output
  call void @__quantum__rt__result_record_output(ptr null, ptr @0)
  ret i64 0
}

; declarations of QIS functions

declare void @__quantum__qis__pulse__play__body(ptr, ptr)
declare void @__quantum__qis__pulse__delay__body(ptr, double)
declare void @__quantum__qis__pulse__shift__phase__body(ptr, double)
declare void @__quantum__qis__pulse__barrier__body(i64, ...)
declare void @__quantum__qis__pulse__acquire__body(ptr, double, ptr writeonly) #1

; declarations of runtime functions for initialization and output recording

declare void @__quantum__rt__initialize(ptr)
declare void @__quantum__rt__result_record_output(ptr, ptr)

; attributes

attributes #0 = { "entry_point" "qir_profiles"="pulse_profile" "output_labeling_schema"="schema_id" "required_num_results"="1" }

attributes #1 = { "irreversible" }

; module flags

!llvm.module.flags = !{!0, !1, !2, !3, !4}

!0 = !{i32 1, !"qir_major_version", i32 2}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_port_management", i1 false}
!3 = !{i32 1, !"dynamic_frame_management", i1 false}
!4 = !{i32 1, !"dynamic_waveform_management", i1 false}

```

The program applies a √X pulse to qubit 0's drive frame, allows free evolution
for 8 ns, applies a virtual-Z-rotated √X pulse (realizing √Y), and records the
acquired readout result.

## Entry Point Definition

The bitcode contains the definition of the LLVM function that will be invoked
when a [pulse-level quantum program](#glossary) is executed, referred to as the
module's "entry point" in the rest of this profile specification. The name of
this function may be chosen freely, as long as it is a valid
[global identifier](https://llvm.org/docs/LangRef.html#identifiers) according to
the LLVM standard. Entry points are identified by a custom function attribute;
the section on [attributes](#attributes) defines which attributes must be
attached to an entry point function.

A Pulse Profile compliant entry point may not take any parameters and must
return an exit code in the form of a 64-bit integer. The exit code `0` must be
used to indicate a successful execution of the program. Any other value of the
exit code indicates a failure during execution.

Execution starts at the entry
[Basic Block](https://en.wikipedia.org/wiki/Basic_block) and follows the
[control flow graph](https://en.wikipedia.org/wiki/Control-flow_graph) defined
by the function's basic blocks and their terminators, ending when a block
terminates in a `ret` instruction. This profile does not impose a fixed number
or structure of basic blocks; program logic may be organized into whichever
blocks are convenient, subject to the ordering constraints described below.

The entry block contains the necessary call(s) to initialize the execution
environment, as the first instruction(s) performed by the program. In
particular, this must ensure that the pulse hardware — ports, and any statically
declared frames — is brought to a well-defined initial state prior to program
execution. The section on [initialization functions](#initialization-functions)
defines how to do that. Calls to [runtime functions](#pulse-runtime-pulse-rt)
used for initialization may only appear at the beginning of the program.

Calls to QIS functions
[quantum__qis__pulse*](#pulse-quantum-instruction-set-pulse-qis) must always
return `void`, regardless of which optional capabilities of this profile are
enabled. Where the optional dynamic resource-management capabilities (see
Optional Capabilities) are _not_ enabled, all arguments to QIS function calls
must be inlined into the call itself as constants — either pointers of type
`ptr` identifying pulse resources, or literal constants of the argument's
declared classical type (e.g., `i64`, `double`). Where dynamic
resource-management capabilities are enabled, a `ptr` argument identifying a
Port, Frame, or Waveform may instead be a local value obtained from an earlier
call to the corresponding `__quantum__rt__pulse__*` construction function; the
section on [Classical Instructions](#classical-instructions) describes the
permitted use of such local values.

This profile requires that acquisitions occur only after all other pulse-level
program logic affecting the same resources has completed. This is expressed as
an ordering constraint rather than as a requirement on block structure: no call
to a QIS function that is not marked `irreversible`, and no call to a runtime
function used for the dynamic construction or release of pulse resources, may
occur after a call to a QIS function marked `irreversible`, within the same
execution path. The section on the
[quantum instruction set](#pulse-quantum-instruction-set-pulse-qis) defines the
requirement(s) regarding the use of the `irreversible` attribute. Additional
restrictions on the use of Port, Frame, and Waveform references are described in
a later section.

The calls used to record the program output must be the final calls performed by
the entry point function along a given execution path, immediately preceding the
`ret` instruction that terminates the function and returns the exit code. More
information about output recording is detailed in the section about runtime
functions.

## Pulse Quantum Instruction Set (Pulse-QIS)

The Pulse Quantum Instruction Set (Pulse-QIS) is a namespaced set of
`__quantum__qis__pulse__*` intrinsic functions that operate on
[opaque types](#definitions-and-data-structures). Together they cover the
operations required to manipulate frame state, and play and acquire pulses on
hardware.

For a quantum instruction set to be fully compatible with the Pulse Profile, it
must satisfy the following requirements:

1. All functions must return `void`; the Pulse Profile does not permit calling
   QIS functions that return a value. Functions that perform an acquisition must
   take the frame pointer as well as the result pointer as arguments.

2. Functions that perform an acquisition must be marked with a custom function
   attribute named `irreversible`.

3. Parameters of type `ptr` identifying results must be `writeonly` parameters;
   only the runtime function `__quantum__rt__result_record_output` used for
   output recording may read an acquired result.

4. Functions that act on a Frame reference must be consistent with the per-frame
   logical clock semantics defined in the section on [Frame references](#frame).
   In particular, a function must correctly advance, leave unchanged, or
   synchronize a frame's logical clock according to its documented behavior, so
   that the ordering and timing of operations implied by the program IR is
   preserved regardless of the specific QIS implementation provided by a
   backend.

| Function                                      | Signature                                                                 | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `__quantum__qis__pulse__play__body`           | `void(ptr %frame, ptr %waveform)`                                         | Executes the waveform referenced by `%waveform` on the frame referenced by `%frame`. The frame is bound to a specific port at construction time, so the port reference is implicit. The waveform carries a duration parameter, which is used by the play intrinsic to set the duration of execution. This intrinsic also advances the clock of the frame by the waveform's duration.                                                                                                                         |
| `__quantum__qis__pulse__delay__body`          | `void(ptr %frame, double %duration)`                                      | Inserts a delay of `%duration` (seconds) on the frame referenced by `%frame`. Note that this is not a global delay operation, it is specific to a frame. This intrinsic advances the clock of the frame by the specified duration.                                                                                                                                                                                                                                                                           |
| `__quantum__qis__pulse__acquire__body`        | `void(ptr %frame, double %duration, ptr writeonly %result) #irreversible` | Acquires a measurement on the port bound to the frame referenced by `%frame`, integrating for `%duration` (seconds). Writes the classified result to `%result`. Here, the term "integration" means collapsing a stream of samples into a single output (IQ point). Whereas, the term "classification" means mapping that IQ point to a 0 or 1 bit.                                                                                                                                                           |
| `__quantum__qis__pulse__barrier__body`        | `void(i64 %n_frames, ptr %frame1,...)`                                    | Synchronizes the timelines of the frames passed as variadic arguments. The count `%n_frames` gives the number of frame references that follow; each subsequent variadic argument is a `ptr` denoting a Frame reference. This intrinsic advances the clocks of every listed frame to the maximum of the clocks of all frames. After the barrier, all listed frames are aligned, and subsequent operations on any of these frames are scheduled from that common time point. Frames not listed are unaffected. |
| `__quantum__qis__pulse__set__frequency__body` | `void(ptr %frame, double %frequency)`                                     | Sets the carrier frequency of the frame referenced by `%frame` to `%frequency` (Hz).                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `__quantum__qis__pulse__set__phase__body`     | `void(ptr %frame, double %phase)`                                         | Sets the accumulated phase of the frame referenced by`%frame` to `%phase` (radians).                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `__quantum__qis__pulse__shift__phase__body`   | `void(ptr %frame, double %delta_phase)`                                   | Adds `%delta_phase (radians)` to the accumulated phase of the frame referenced by `%frame`.                                                                                                                                                                                                                                                                                                                                                                                                                  |

## Classical Instructions

The following instructions are the _only_ LLVM instructions that are permitted
within a Pulse Profile compliant program:

| LLVM Instruction         | Context and Purpose                                                                              | Rules for Usage                                                                                                                                                                                                                                                                                                                                 |
| :----------------------- | :----------------------------------------------------------------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `call`                   | Used within a basic block to invoke any one of the declared QIS functions and runtime functions. | Calls to QIS functions must always return `void`. Where an optional dynamic resource-management capability is supported, the result of a call to the corresponding `__quantum__rt__pulse__*` construction function may be assigned to a named local value; such a value may be used only, unmodified, as a `ptr` argument to a subsequent call. |
| `br`                     | Used to branch from one basic block to another.                                                  | The branching must be unconditional and occurs as the final instruction of a block to jump to the next one.                                                                                                                                                                                                                                     |
| `ret`                    | Used to return the exit code of the program.                                                     | Must occur (only) as the last instruction of the final block in an entry point.                                                                                                                                                                                                                                                                 |
| `inttoptr`               | Used to cast an `i64` integer value to a `ptr`.                                                  | May be used as part of a function call only.                                                                                                                                                                                                                                                                                                    |
| `getelementptr inbounds` | Used to create a `ptr` to pass a constant string for the purpose of labeling an output value.    | May be used as part of a call to an output recording function only.                                                                                                                                                                                                                                                                             |

See also the section on
[Definitions and Data Structures](#definitions-and-data-structures) for more
information about the creation and usage of Port, Frame, and Waveform
references.

## Pulse-Runtime (Pulse-rt)

The following Pulse runtime functions must be supported by all backends:

| Function                                      | Signature                                                 | Description                                                                                                                                                                                                                  |
| --------------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__quantum__rt__pulse__get_port`              | `ptr(i64 %port_id)`                                       | Returns a reference to the hardware port identified by the target-defined integer `%port_id`.                                                                                                                                |
| `__quantum__rt__pulse__create_frame`          | `ptr(ptr %port, double %frequency, double %phase)`        | Constructs a new frame bound to the port referenced by `%port`, with initial carrier frequency `%frequency (Hz)` and initial phase `%phase (radians)`, and returns a reference to it.                                        |
| `__quantum__rt__pulse__waveform_gaussian`     | `ptr(double %amplitude, double %sigma, double %duration)` | Constructs a Gaussian-envelope waveform with peak amplitude `%amplitude`, standard deviation `%sigma (seconds)`, and total duration `%duration (seconds)`, centered at `%duration / 2`, and returns a reference to it.       |
| `__quantum__rt__pulse__waveform_from_samples` | `ptr(ptr %samples, i64 %n_samples, double %sample_rate)`  | Constructs a waveform from `%n_samples` complex-valued IQ samples pointed to by `%samples`, discretized at the description sample rate `%sample_rate (Hz)`. The resulting envelope has duration `%n_samples / %sample_rate`. |

The above functions dynamically construct resources at runtime. Dynamic
construction is indicated via the module flags: `dynamic_port_management`,
`dynamic_frame_management`, `dynamic_waveform_management`. To reclaim the
constructed or allocated resources, following resource release functions can be
used:

```llvm
declare void @__quantum__rt__pulse__release_port(ptr %port)
declare void @__quantum__rt__pulse__release_frame(ptr %frame)
declare void @__quantum__rt__pulse__release_waveform(ptr %waveform)
```

### Initialization Functions

## Attributes

The attribute usage and requirements of the Pulse Profile remain mostly the same
as defined in the [Base Profile](./Base_Profile.md#attributes) but with
following key difference with respect to attributes attached to an entry point
function:

- The Pulse Profile does not support the `"required_num_qubits"` attribute since
  the profile does not define a `"qubit"` resource.

## Module Flags Metadata

The Pulse Profile requires the following module flags to be present within the
QIR bitcode:

- a flag with the string identifier `"qir_major_version"` that contains a
  constant value of type `i32`
- a flag with the string identifier `"qir_minor_version"` that contains a
  constant value of type `i32`
- a flag with the string identifier `"dynamic_port_management"` that contains a
  constant `true` or `false` value of type `i1` indicating whether the program
  uses dynamic port construction and release. When set to `true`, the runtime
  API functions `__quantum__rt__pulse__get_port` and
  `__quantum__rt__pulse__release_port` may be used in the program.
- a flag with the string identifier `"dynamic_frame_management"` that contains a
  constant `true` or `false` value of type `i1` indicating whether the program
  uses dynamic frame construction and release. When set to `true`, the runtime
  API functions `__quantum__rt__pulse__create_frame` and
  `__quantum__rt__pulse__release_frame` may be used in the program.
- a flag with the string identifier `"dynamic_waveform_management"` that
  contains a constant `true` or `false` value of type `i1` indicating whether
  the program uses dynamic waveform construction and release. When set to
  `true`, the runtime API functions `__quantum__rt__pulse__waveform_gaussian` or
  `__quantum__rt__pulse__waveform_from_samples` for waveform construction and
  `__quantum__rt__pulse__release_waveform` for waveform release may be used in
  the program.

These flags are attached as `llvm.module.flags` metadata to the module. They can
be queried using the standard LLVM tools and follow the LLVM specification in
behavior and purpose.

## Additional Examples

## Glossary

## Open Questions

1. The `ptr inttoptr (i64 1 to ptr)` in `__quantum__qis__pulse__acquire__body`'s
   first argument is `frame 1` (the readout frame), and `ptr writeonly null` is
   `result 0`; these are two independent ID spaces, worth confirming that's
   unambiguous once Classical Instructions / Qubit-and-Result-usage-equivalent
   sections exist for Pulse Profile.

2. This proposal currently requires the `%out_err` parameter of all
   `__quantum__rt__pulse__*` construction functions to be passed as `ptr null`,
   meaning a failed construction terminates program execution and no in-program
   error inspection is supported. Supporting real error inspection would require
   the caller to provide addressable storage for `%out_err`, which in turn
   requires a memory capability not currently part of this proposal's optional
   capabilities (see the QIR specification's optional Arrays capability for a
   related precedent). Should this proposal (a) define such a capability now,
   (b) explicitly defer it to a follow-up proposal once a concrete use case
   demonstrates the need, or (c) omit the `%out_err` parameter from
   `__quantum__rt__pulse__*` functions entirely until then?
