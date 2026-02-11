
# Dynamic Allocation and Arrays

As of v1.0, QIR only supported handling of qubits and results statically known
at compile time. This extension for QIR 2.0
[Adaptive Profile](./profiles/Adaptive_Profile.md) adds the ability to
dynamically allocate qubits, results and their arrays.

## Motivation & Scope

Dynamic qubit/result allocation and first-class array support enable QIR to represent
algorithms and workflows that require:

- Allocating ancilla qubits or measurement results at runtime (e.g., for quantum
  error correction, variational algorithms, or parameterized circuits)
- Passing qubits and arrays as function arguments, supporting modular and
  scalable quantum programs
- Iterating over arrays of qubits/results and returning arrays of measurement results
- Efficient targeting of devices with varying qubit counts and improved
  interoperability with advanced quantum languages

This extension maintains backward compatibility with existing QIR tooling and
profiles, and is designed to keep classical memory management simple (favoring
stack allocation and native LLVM arrays).

## Specification

### Enabling Dynamic Memory Management

To use dynamic allocation, set the following module flags to `true`:

- `"dynamic_qubit_management"`
- `"dynamic_result_management"`

When these flags are set, the `required_num_qubits` and `required_num_results`
attributes on the entry point are not required; the runtime manages allocation.

### Enabling Array Support

To use arrays of qubits and results, set the following module flag to `true`:

- `"arrays"`

This flag enables array support for both qubits and results, regardless of
whether they are allocated statically or dynamically.

### Types

Use native LLVM array types (`[%N x ptr]`) and `alloca` for stack
allocation, or heap allocation as needed.

### Runtime API

**Qubit management:**

```llvm
declare ptr @__quantum__rt__qubit_allocate(ptr %out_err)
declare void @__quantum__rt__qubit_release(ptr %qubit)
; Caller provides a buffer capable of holding N pointer-sized entries.
declare void @__quantum__rt__qubit_array_allocate(i64 %N, ptr %array, ptr %out_err)
declare void @__quantum__rt__qubit_array_release(i64 %N, ptr %array)
```

**Result management:**

```llvm
declare ptr @__quantum__rt__result_allocate(ptr %out_err)
declare void @__quantum__rt__result_release(ptr %result)
declare void @__quantum__rt__result_array_allocate(i64 %N, ptr %array, ptr %out_err)
declare void @__quantum__rt__result_array_release(i64 %N, ptr %array)
```

**Notes:**

- The `array_allocate` functions write N pointer values into the memory at
  `%array`. The caller is responsible for allocating and freeing the classical
  memory.
- The `array_release` functions release the runtime-managed objects, but do not
  free the classical buffer.

**Error handling:**

- All allocation functions accept an optional output parameter `%out_err` for
  error handling.
- If `%out_err` is `null`, allocation failure results in runtime termination
  (crash). This is the common case for most programs.
- If `%out_err` is non-null, the caller must have allocated memory for an `i1`
  and passed a pointer to it. The runtime will set this `i1` to `true` on
  allocation failure and `false` on success. Advanced users can check this flag
  to handle allocation failures gracefully.

### Array Output Recording

To record/print an entire measurement result array in one line:

```llvm
declare void @__quantum__rt__result_array_record_output(i64 %N, ptr %result_array, ptr %tag)
```

`%N` is the size of `%result_array`. Endianness for rendering is undecided.

**Note:** This is the only specialized array output recording function. No
additional output recording functions will be introduced for other types or
purposes.

### Support Matrix

When describing container/object capabilities, consider two axes:

- Container allocation: Stack (compile-time size) vs Heap (runtime size)
- Object creation: Dynamic (via `dynamic_*_management` flags) vs Static
  (compile-time ID via `required_num_*` flags)

This yields four supported scenarios (stack/heap × dynamic/static) and clarifies
compiler/runtime responsibilities.

### Qubit State After Release

The state of a qubit after `__quantum__rt__qubit_release` is backend-specific.
Backends may return qubits in a clean state (e.g., reset to |0⟩) or in a dirty
state (whatever state the qubit was in when released). Programs should not rely
on any particular state and should explicitly reset qubits if a known state is
required.

### Rationale and Implementation Notes

- Caller-managed classical memory keeps memory semantics simple and leverages
  LLVM's native array and aggregate operations.
- Separating classical memory lifetime from runtime-managed quantum objects
  simplifies backends.
- The error handling approach via output parameters allows most programs to use
  simple allocation with implicit failure handling while enabling advanced users
  to handle allocation failures explicitly.

## Open Questions

- Exact semantics for `result_array_record_output` formatting (endianness)
