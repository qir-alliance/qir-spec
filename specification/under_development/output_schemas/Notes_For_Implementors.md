# Notes

## Types

The types chosen in the output schemas represent the base data types for expressing computation in the context of quantum processing. The `RESULT` and `BOOL` entries, while they could have been expressed as integers, describe core domain concepts that are unambiguous and clear in their intent.

### Output Type

The effective ouput type for labeled output formats is determined by the labeling scheme employed as order is not guaranteed.

For unlabeled output, the output recording calls define an inferred type based on the order in which the output recording calls are made. If the ouput is defined and held within a container type, `TUPLE` or `ARRAY`, then the shot's output type is that containers type.

`TUPLE` is a container for values that may or may not have the same type. `ARRAY` is a container whose values are intended to be all of the same type. Having mixed values in an `ARRAY` entry has undefined behavior when being processed.

For output that isn't contained within a container type, the inferred output type is a `TUPLE` whose values are the entries found.

#### Unlabeled Examples

The inferred type of the following is `TUPLE(ARRAY[RESULT], ARRAY[RESULT])`:

```console
START
METADATA        entry_point
METADATA        num_required_qubits     5
METADATA        num_required_results    5
METADATA        output_labeling_schema
METADATA        qir_profiles    base_profile
OUTPUT  ARRAY   2
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  ARRAY   3
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  RESULT  0
END     0
```

The inferred type of the following is also `TUPLE(ARRAY[RESULT], ARRAY[RESULT])` as the `ARRAY` entries are wrapped in a container:

```console
START
METADATA        entry_point
METADATA        num_required_qubits     5
METADATA        num_required_results    5
METADATA        output_labeling_schema
METADATA        qir_profiles    base_profile
OUTPUT  TUPLE   2
OUTPUT  ARRAY   2
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  ARRAY   3
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  RESULT  0
END     0
```

The inferred type of the following is `TUPLE(ARRAY[RESULT], INT, DOUBLE)`:

```console
START
METADATA        entry_point
METADATA        num_required_qubits     5
METADATA        num_required_results    5
METADATA        output_labeling_schema
METADATA        qir_profiles    base_profile
OUTPUT  ARRAY   2
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  INT     5
OUTPUT  DOUBLE  -0.5e3
END     0
```

The inferred type of the following is `ARRAY[ARRAY[RESULT]]`:

```console
START
METADATA        entry_point
METADATA        num_required_qubits     5
METADATA        num_required_results    5
METADATA        output_labeling_schema
METADATA        qir_profiles    base_profile
OUTPUT  ARRAY   2
OUTPUT  ARRAY   1
OUTPUT  RESULT  0
OUTPUT  ARRAY   3
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  RESULT  0
END     0
```

## Examples

### Muliple Arrays

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

attributes #0 = { "entry_point" "num_required_qubits"="5" "num_required_results"="5" "output_labeling_schema" "qir_profiles"="base_profile" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
!2 = !{i32 1, !"dynamic_qubit_management", i1 false}
!3 = !{i32 1, !"dynamic_result_management", i1 false}
```

Ouput:

```console
START
METADATA        entry_point
METADATA        num_required_qubits     5
METADATA        num_required_results    5
METADATA        output_labeling_schema
METADATA        qir_profiles    base_profile
OUTPUT  ARRAY   2
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  ARRAY   3
OUTPUT  RESULT  0
OUTPUT  RESULT  0
OUTPUT  RESULT  0
END     0
```
