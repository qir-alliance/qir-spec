# Notes

## Types

The types chosen in the output schemas represent the base data types for
expressing computation in the context of quantum processing. The `RESULT` and
`BOOL` entries, while they could have been expressed as integers, describe core
domain concepts that are unambiguous and clear in their intent.

## Output Type

The effective output type for labeled output formats is determined by the
labeling format employed as order is not guaranteed.

For ordered output, the output recording calls define an inferred type based on
the order in which the output recording calls are made. If the output is defined
and held within a container type, `TUPLE` or `ARRAY`, then the shot's output
type is that containers type.

`TUPLE` is a container for values that may or may not have the same type.
`ARRAY` is a container whose values are intended to be all of the same type.
Having mixed values in an `ARRAY` entry has undefined behavior when being processed.

For output that isn't contained within a container type, the inferred output
type is a `TUPLE` whose values are the entries found.

### Output Type Examples using the Ordered Schema

Note that `METADATA` records in the following examples are fabricated.

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

The inferred type of the following shot is also
`TUPLE(ARRAY[RESULT], ARRAY[RESULT])` as the `ARRAY` entries are wrapped in a container:

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

```log
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

## QIR to Output Examples

### Multiple Arrays

```llvm
%Qubit = type opaque
%Result = type opaque

@0 = internal constant [5 x i8] c"0_0a\00"
@1 = internal constant [7 x i8] c"1_0a0r\00"
@2 = internal constant [7 x i8] c"1_0a1r\00"
@3 = internal constant [5 x i8] c"2_1a\00"
@4 = internal constant [7 x i8] c"3_1a0r\00"
@5 = internal constant [7 x i8] c"4_1a1r\00"
@6 = internal constant [7 x i8] c"4_1a1r\00"

define void @main() #0 {
entry:
  call void @__quantum__rt__initialize(i8* null)
  call void @__quantum__qis__h__body(%Qubit* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* null)
  call void @__quantum__qis__mz__body(%Qubit* null, %Result* inttoptr (i64 2 to %Result*))
  call void @__quantum__rt__array_record_output(i64 2, i8* getelementptr inbounds ([5 x i8], [5 x i8]* @0, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 1 to %Result*), i8* getelementptr inbounds ([7 x i8], [7 x i8]* @1, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* null, i8* getelementptr inbounds ([7 x i8], [7 x i8]* @2, i32 0, i32 0))
  call void @__quantum__rt__array_record_output(i64 3, i8* getelementptr inbounds ([5 x i8], [5 x i8]* @3, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 4 to %Result*), i8* getelementptr inbounds ([7 x i8], [7 x i8]* @4, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 3 to %Result*), i8* getelementptr inbounds ([7 x i8], [7 x i8]* @5, i32 0, i32 0))
  call void @__quantum__rt__result_record_output(%Result* inttoptr (i64 2 to %Result*), i8* getelementptr inbounds ([7 x i8], [7 x i8]* @6, i32 0, i32 0))
  ret void
}

declare void @__quantum__rt__initialize(i8*)

declare void @__quantum__qis__h__body(%Qubit*)

declare void @__quantum__qis__mz__body(%Qubit*, %Result* writeonly) #1

declare void @__quantum__rt__array_record_output(i64, i8*)

declare void @__quantum__rt__result_record_output(%Result*, i8*)

attributes #0 = { "entry_point" "required_num_qubits"="5" "required_num_results"="5" "qir_profiles"="base_profile" "output_labeling_schema"="schema_id" }
attributes #1 = { "irreversible" }

!llvm.module.flags = !{!0, !1, !2, !3}

!0 = !{i32 1, !"qir_major_version", i32 1}
!1 = !{i32 7, !"qir_minor_version", i32 0}
```

Output for a single shot:

```log
HEADER\tschema_id\tordered
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
