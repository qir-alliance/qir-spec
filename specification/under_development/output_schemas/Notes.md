# Notes

## Types

The types chosen in the output schemas represent the base data types for expressing computation in the context of quantum processing. The `RESULT` and `BOOL` entries, while they could have been expressed as integers, describe core domain concepts that are unambiguous and clear in their intent.

### Output Type

The effective ouput type for labeled output formats is determined by the labeling format employed as order is not guaranteed.

For ordered output, the output recording calls define an inferred type based on the order in which the output recording calls are made. If the ouput is defined and held within a container type, `TUPLE` or `ARRAY`, then the shot's output type is that containers type.

`TUPLE` is a container for values that may or may not have the same type. `ARRAY` is a container whose values are intended to be all of the same type. Having mixed values in an `ARRAY` entry has undefined behavior when being processed.

For output that isn't contained within a container type, the inferred output type is a `TUPLE` whose values are the entries found.

#### Ordered Examples

The inferred type of the following shot is `TUPLE(ARRAY[RESULT], ARRAY[RESULT])`:

```log
START
METADATA\tentry_point
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tqir_profiles\tbase_profile
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t3
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
END\t0
```

The inferred type of the following shot is also `TUPLE(ARRAY[RESULT], ARRAY[RESULT])` as the `ARRAY` entries are wrapped in a container:

```log
START
METADATA\tentry_point
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tqir_profiles\tbase_profile
OUTPUT\tTUPLE\t2
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t3
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
END\t0
```

The inferred type of the following shot is `TUPLE(ARRAY[RESULT], INT, DOUBLE)`:

```log
START
METADATA\tentry_point
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tqir_profiles\tbase_profile
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tINT\t5
OUTPUT\tDOUBLE\t-0.5e3
END\t0
```

The inferred type of the following shot is `ARRAY[ARRAY[RESULT]]`:

```console
START
METADATA\tentry_point
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tqir_profiles\tbase_profile
OUTPUT\tARRAY\t2
OUTPUT\tARRAY\t1
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t3
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
END\t0
```

## Examples

### Multiple Arrays

```llvm
%Qubit = type opaque
%Result = type opaque

define void @main() #0 {
entry:
  call void @__quantum__rt__initialize(i8* null)
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* inttoptr (i64 2 to %Result*))
  call void @__quantum__rt__array_record_output(i64 2, i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* null)
  call void @__quantum__rt__result_record_output(%Result* null, i8* null)
  call void @__quantum__rt__array_record_output(i64 3, i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 4 to %Result*), i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 3 to %Result*), i8* null)
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 2 to %Result*), i8* null)
  ret void
}

declare void @__quantum__rt__initialize(i8*)

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

declare void @__quantum__rt__array_record_output(i64, i8*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

attributes #0 = { "entry_point" "required_num_qubits"="5" "required_num_results"="5" "qir_profiles"="base_profile" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
```

Ouput for a single shot:

```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
START
METADATA\tentry_point
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tqir_profiles\tbase_profile
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t3
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
END\t0
```
