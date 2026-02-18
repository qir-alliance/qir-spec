
# Arrays and Dynamic Allocation

As of v1.0, QIR only supported handling of qubits and results statically known
at compile time, and did not provide native array support. This extension for
QIR 2.0 [Adaptive Profile](./profiles/Adaptive_Profile.md) adds two independent
capabilities:

1. **Arrays**: First-class support for arrays of any supported type using native
   LLVM array types
2. **Dynamic allocation**: Runtime allocation of qubits and results

These capabilities are orthogonal and can be used independently or together.

## Motivation & Scope

**Array support** enables QIR to represent algorithms and workflows that require:

- Passing collections of qubits or results as function arguments
- Iterating over collections of quantum resources
- Returning arrays of measurement results
- Working with any supported type in aggregate form
- Modular and scalable quantum program structure

**Dynamic allocation** enables QIR to represent algorithms and workflows that
require:

- Allocating qubits or results at runtime (e.g., for quantum error correction,
  variational algorithms, or parameterized circuits)
- Efficient targeting of devices with varying qubit counts
- Adaptively determining resource requirements during execution

These extensions maintain backward compatibility with existing QIR tooling and
profiles, and are designed to keep classical memory management simple (favoring
stack allocation and native LLVM arrays).

## Array Support

Array support provides first-class native LLVM array types for all supported
types in QIR. While this specification focuses on arrays of qubits and results
(the primary use case), the array capability is general and applies to any type
that a profile supports.

### Enabling Arrays

To use arrays, set the following module flag to `true`:

- `"arrays"`

When enabled, programs may use native LLVM array types (e.g., `[N x ptr]` for
arrays of qubits or results) and associated LLVM array operations regardless of
whether the contained objects are allocated statically or dynamically.

### Supported LLVM Array Operations

When arrays are enabled, the following LLVM features must be supported:

- **Array types**: Native LLVM array types such as `[N x ptr]`
- **Stack allocation**: The `alloca` instruction for stack-allocated arrays with
  compile-time known sizes
- **Element access**: The `getelementptr` (GEP) instruction for computing
  addresses of array elements
- **Aggregate operations**: The `extractvalue` and `insertvalue` instructions
  for accessing and modifying elements
- **Load/Store**: Standard `load` and `store` instructions for reading from and
  writing to array elements

Note that LLVM does not natively support dynamically-sized arrays (arrays whose
size is determined at runtime). For runtime-sized collections, classical memory
management remains the responsibility of the caller.

### Array Output Recording for Results

When arrays are enabled, the following specialized function is available to
record an entire measurement result array in a single output record:

```llvm
declare void @__quantum__rt__result_array_record_output(i64 %N, ptr %result_array, ptr %tag)
```

`%N` is the size of `%result_array`. `%result_array` must point to valid memory
containing `%N` sequential result pointers. The array is rendered in the output
in memory order: the first element in the array (at the lowest memory address,
`%result_array[0]`) appears first (leftmost) in the output, followed by
subsequent elements in order.

**Note:** This is the only specialized array output recording function. No
additional output recording functions will be introduced for other types or
purposes. See the [output schemas](./output_schemas/) documentation for specific
rendering details.

### Array Examples

**Static array of statically-allocated qubits:**

```llvm
; Declare an array of 5 qubit pointers
%qubits = alloca [5 x ptr], align 8

; Initialize with statically-allocated qubits (using integer-to-pointer casts)
%q0_ptr = getelementptr inbounds [5 x ptr], ptr %qubits, i64 0, i64 0
store ptr inttoptr (i64 0 to ptr), ptr %q0_ptr, align 8

%q1_ptr = getelementptr inbounds [5 x ptr], ptr %qubits, i64 0, i64 1
store ptr inttoptr (i64 1 to ptr), ptr %q1_ptr, align 8
; ... etc

; Use the qubits
%q0 = load ptr, ptr %q0_ptr, align 8
call void @__quantum__qis__h__body(ptr %q0)
%q1 = load ptr, ptr %q1_ptr, align 8
call void @__quantum__qis__h__body(ptr %q1)
```

**Static array with dynamically-allocated results:**

```llvm
; Requires both arrays=true and dynamic_result_management=true
%results = alloca [3 x ptr], align 8

; Allocate each result individually
%r0 = call ptr @__quantum__rt__result_allocate(ptr null)
%r0_ptr = getelementptr inbounds [3 x ptr], ptr %results, i64 0, i64 0
store ptr %r0, ptr %r0_ptr, align 8
; ... allocate and store r1, r2

; Perform measurements
%r0_loaded = load ptr, ptr %r0_ptr, align 8
call void @__quantum__qis__mz__body(ptr %qubit0, ptr %r0_loaded)

; Record the entire array
call void @__quantum__rt__result_array_record_output(i64 3, ptr %results, ptr @tag)

; Release each result
call void @__quantum__rt__result_release(ptr %r0)
; ... release r1, r2
```

## Dynamic Allocation

Dynamic allocation enables runtime allocation and release of qubits and results,
allowing programs to determine resource requirements during execution rather
than at compile time.

### Enabling Dynamic Memory Management

To use dynamic allocation, set the following module flags to `true`:

- `"dynamic_qubit_management"` - enables dynamic allocation of qubits
- `"dynamic_result_management"` - enables dynamic allocation of results

When these flags are set, the `required_num_qubits` and/or `required_num_results`
attributes on the entry point are not required; the runtime manages allocation
and deallocation.

### Single-Resource Allocation API

**Qubit allocation:**

```llvm
; Returns a pointer value for a single qubit, initially in the ground state.
; If `%out_err` is `null`, allocation failure results in runtime termination.
; If `%out_err` is non-`null`, it must point to valid memory for an `i1` value.
; On allocation failure, the `i1` is set to true and `null` is returned.
; On success, the `i1` is set to false and a valid qubit pointer is returned.
declare ptr @__quantum__rt__qubit_allocate(ptr %out_err)

; Release a single qubit, such that the pointer value is no longer valid after
; this function returns and the referenced qubit is available for allocation by
; later runtime calls in the program.
declare void @__quantum__rt__qubit_release(ptr %qubit)
```

**Result allocation:**

```llvm
; Returns a pointer value for a single measurement result, initially in a state
; such that calls to `__quantum__rt__read_result` with that pointer will return
; false.
; If `%out_err` is `null`, allocation failure results in runtime termination.
; If `%out_err` is non-`null`, it must point to valid memory for an `i1` value.
; On allocation failure, the `i1` is set to true and `null` is returned.
; On success, the `i1` is set to false and a valid result pointer is returned.
declare ptr @__quantum__rt__result_allocate(ptr %out_err)

; Release a single result, such that the pointer value is no longer valid after
; this function returns and the referenced measurement result is available for
; allocation by later runtime calls in the program.
declare void @__quantum__rt__result_release(ptr %result)
```

### Bulk Allocation API (Requires Arrays)

When both dynamic allocation **and** array support are enabled, bulk allocation
functions are available that efficiently allocate multiple resources at once.
These functions require the caller to provide a pre-allocated array buffer.

**Qubit array allocation:**

```llvm
; Performs an allocation of the given number of qubits, initially in the ground
; state, storing the resulting pointer values into memory at the given pointer.
; The caller is responsible for ensuring `%array` points to valid memory with
; enough space to support writing `%N * sizeof(ptr)` values.
; If `%out_err` is `null`, allocation failure results in runtime termination.
; If `%out_err` is non-`null`, it must point to valid memory for an `i1` value.
; On allocation failure, the `i1` is set to true. On success, the `i1` is set to
; false.
declare void @__quantum__rt__qubit_array_allocate(i64 %N, ptr %array, ptr %out_err)

; Releases the given qubits read from the given memory. `%array` must point to
; valid memory that contains `%N` sequential pointer values. All pointers stored
; in that memory must correspond to currently allocated qubits. These pointer
; values are no longer valid after this function returns and the referenced
; qubits are available for allocation by later runtime calls in the program. The
; memory pointed to by `%array` is left unchanged and management of that memory
; is the responsibility of caller.
declare void @__quantum__rt__qubit_array_release(i64 %N, ptr %array)
```

**Result array allocation:**

```llvm
; Performs an allocation of the given number of results, storing the resulting
; pointer values into memory at the given pointer. The caller is responsible for
; ensuring `%array` points to valid memory with enough space to support writing
; `%N * sizeof(ptr)` values. All returned results are initially in a state such
; that calls to `__quantum__rt__read_result` with that pointer will return false.
; If `%out_err` is `null`, allocation failure results in runtime termination.
; If `%out_err` is non-`null`, it must point to valid memory for an `i1` value.
; On allocation failure, the `i1` is set to true. On success, the `i1` is set to
; false.
declare void @__quantum__rt__result_array_allocate(i64 %N, ptr %array, ptr %out_err)

; Releases the given results read from the given memory. `%array` must point to
; valid memory that contains `%N` sequential pointer values. All pointers stored
; in that memory must correspond to currently allocated results. These pointer
; values are no longer valid after this function returns and the referenced
; measurement results are available for allocation by later runtime calls in the
; program. The memory pointed to by `%array` is left unchanged and management of
; that memory is the responsibility of caller.
declare void @__quantum__rt__result_array_release(i64 %N, ptr %array)
```

**Separation of classical and quantum memory management:**

The bulk allocation functions explicitly separate the responsibilities of
classical and quantum memory management:

- **Classical memory (the array buffer)**: Managed entirely by the caller using
  standard LLVM memory operations. The caller allocates memory (typically via
  `alloca` for stack allocation), passes a pointer to this memory to the
  allocation function, and is responsible for the lifetime of this memory.
- **Quantum objects (qubits/results)**: Managed by the runtime. The runtime
  allocates the quantum resources and writes pointers to them into the
  caller-provided buffer. The runtime tracks which quantum resources are
  allocated and releases them when `*_release` is called.

This separation keeps memory semantics simple, leverages LLVM's native array and
aggregate operations, and avoids requiring backends to manage classical memory
for arrays.

### Dynamic Allocation Examples

**Single qubit allocation:**

```llvm
%qubit = call ptr @__quantum__rt__qubit_allocate(ptr null)
call void @__quantum__qis__h__body(ptr %qubit)
call void @__quantum__rt__qubit_release(ptr %qubit)
```

**Single qubit allocation with error checking:**

```llvm
%err = alloca i1, align 1
%qubit = call ptr @__quantum__rt__qubit_allocate(ptr %err)
%failed = load i1, ptr %err, align 1
br i1 %failed, label %error_handler, label %continue
error_handler:
  ; Handle allocation failure
  ret void
continue:
  ; Use the qubit
  call void @__quantum__qis__h__body(ptr %qubit)
  call void @__quantum__rt__qubit_release(ptr %qubit)
  ret void
```

**Bulk qubit allocation (requires arrays):**

```llvm
%qubits = alloca [5 x ptr], align 8
call void @__quantum__rt__qubit_array_allocate(i64 5, ptr %qubits, ptr null)
; Use the qubits...
%q0_ptr = getelementptr inbounds [5 x ptr], ptr %qubits, i64 0, i64 0
%q0 = load ptr, ptr %q0_ptr, align 8
call void @__quantum__qis__h__body(ptr %q0)
; Release when done
call void @__quantum__rt__qubit_array_release(i64 5, ptr %qubits)
```

**Result array allocation and output (requires arrays):**

```llvm
%results = alloca [3 x ptr], align 8
call void @__quantum__rt__result_array_allocate(i64 3, ptr %results, ptr null)
; Perform measurements into the result array...
%r0_ptr = getelementptr inbounds [3 x ptr], ptr %results, i64 0, i64 0
%r0 = load ptr, ptr %r0_ptr, align 8
call void @__quantum__qis__mz__body(ptr %qubit0, ptr %r0)
; Record the entire array as output
call void @__quantum__rt__result_array_record_output(i64 3, ptr %results, ptr @tag)
; Release when done
call void @__quantum__rt__result_array_release(i64 3, ptr %results)
```

## Combined Capabilities Matrix

When both arrays and dynamic allocation are available, programs have flexibility
in how they manage quantum resources:

| **Array Storage**             | **Static Object IDs**                  | **Dynamic Object Allocation**            |
|-------------------------------|----------------------------------------|------------------------------------------|
| **Stack (compile-time size)** | Fixed-size array; compile-time IDs     | Fixed-size array; runtime allocation     |
| **Heap (runtime size)**       | Runtime-sized buffer; compile-time IDs | Runtime-sized buffer; runtime allocation |

This matrix clarifies the independence of the two capabilities while showing how
they combine to support various programming patterns.

## General Considerations

### Resource State After Release

**Qubits:** The state of a qubit after `__quantum__rt__qubit_release` is
backend-specific. Backends may return qubits in a clean state (e.g., reset to
|0⟩) or in a dirty state (whatever state the qubit was in when released).
Programs should not rely on any particular state and should explicitly reset
qubits if a known state is required before reallocation.

**Results:** Results are returned to the runtime and are available for
reallocation. The state is implementation-defined.

### Use-After-Free/Release Behavior

Using a qubit or result pointer after it has been released via `*_release`
results in **undefined behavior**. This includes:

- Applying quantum operations to a released qubit pointer
- Reading or recording a released result pointer
- Passing a released pointer to any runtime or QIS function
- Including a released pointer in a subsequent `*_array_release` call

Backends are not required to detect use-after-free errors, and the behavior in
such cases is implementation-defined. Backends may crash, silently ignore the
operation, or produce incorrect results. It is the responsibility of the QIR
generator (compiler/frontend) to ensure that pointers are not used after being
released.

### Error Handling

All dynamic allocation functions accept an optional output parameter `%out_err`
for error handling:

- If `%out_err` is `null`, allocation failure results in runtime termination
  (crash). This is the common case for most programs.
- If `%out_err` is non-`null`, the caller must have allocated memory for an `i1`
  and passed a pointer to it. The runtime will set this `i1` to `true` on
  allocation failure and `false` on success. Advanced users can check this flag
  to handle allocation failures gracefully.
