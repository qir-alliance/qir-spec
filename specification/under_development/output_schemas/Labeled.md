# Labeled Output Schema

This output schema is meant for backends that asynchronously emit output records and support strings as arguments to functions.

The labeled output schema for asynchronous output emission is the same as the [ordered schema](./Ordered.md) with the following changes:
- `OUTPUT` records `RESULT`, `BOOL`, `INT`, `DOUBLE`, `TUPLE`, and `ARRAY`,  have a fourth element indicating the label of the record.
- Generated QIR that intends to produce output that adheres to the labeled schema must include a `labeling_format` attribute in entry-point functions. This has the implication that a `METADATA` record specifying the labeling format must be present for each `START`/`END` block. For example:
    - `METADATA\tlabeling_format\tsample_format_name`

A grammar that defines the structure and valid values for this format is available [here](./Grammars.md#labeled-and-async).

Labels are needed for reconstruction of asynchronous output emission and are assigned by the front-end QIR generator. Order is not important for the `OUTPUT` records within a `START`/`END` block. However, the responsibility of reconstructing the output based on the defined labeling format belongs to the party permforming the output labeling. The usage of `t0_0a` and `t2_2a` (and other values) are examples of a labeling format, and are only used as an example.

QIR consumers need to map the labels associated to each output recording call to its corresponding output record label.

Here's an example of the output emitted for a single shot:

```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tARRAY\t4\t1_t0a
OUTPUT\tRESULT\t0\t2_t0a0r
OUTPUT\tRESULT\t0\t3_t0a1r
OUTPUT\tRESULT\t0\t4_t0a2r
OUTPUT\tRESULT\t0\t5_t0a3r
OUTPUT\tTUPLE\t3\t6_t1t
OUTPUT\tBOOL\ttrue\t7_t1t0b
OUTPUT\tINT\t42\t8_t1t1i
OUTPUT\tDOUBLE\t3.1415\t9_t1t2d
END\t0
```

## Output Recording Functions

These runtime functions determine how values should be collected to be emitted as output. For simulation or future environments with full runtime support, these functions can be linked to implementations that directly perform the recording of output to the relevant stream. Each of these functions follow the naming pattern `__quantum__rt__*_record_output` where the initial part indicates the type of output to be recorded.

### Result

```llvm
void @__quantum__rt__result_record_output(%Result*, i8*)
```

Produces output records of the format `"OUTPUT\tRESULT\t0\tlabel"` or `"OUTPUT\tRESULT\t1\tlabel"`, representing measurement results. The fourth element is a string label associated to the result value which is included in the corresponding output record.

### Boolean

```llvm
void @__quantum__rt__bool_record_output(i1, i8*)
```

Produces output records of the format `"OUTPUT\tBOOL\tfalse\tlabel"` or `"OUTPUT\tBOOL\ttrue\tlabel"`. The fourth element (`label`) is a string label associated to the Boolean value which is included in the corresponding output record.

### Integer

```llvm
void @__quantum__rt__integer_record_output(i64, i8*)
```

Produces output records of the format `"OUTPUT\tINT\tn\tlabel"` where `n` is the string representation of the integer value, such as `"OUTPUT\tINT\t42\tlabel"`. The fourth element (`label`) is a string label associated to the ineteger value which is included in the corresponding output record.

### Double

```llvm
void @__quantum__rt__double_record_output(double, i8*)
```

Produces output records of the format `"OUTPUT\tDOUBLE\td\tlabel"` where `d` is the string representation of the double value, such as `"OUTPUT\tDOUBLE\t3.14159\tlabel"`. The fourth element (`label`) is a string label associated to the double value which is included in the corresponding output record.

### Tuple

```llvm
void @__quantum__rt__tuple_record_output(i64, i8*)
```

Produces output records of the format  `"OUTPUT\tTUPLE\tn\tlabel"` where `n` is the string representation of the integer value, such as `"OUTPUT\tTUPLE\t4\tlabel"`.  The fourth element (`label`) is a string label associated to the tuple which is included in the corresponding output record. This record indicates the existence of a tuple and how many elements it has.

### Array

```llvm
void @__quantum__rt__array_record_output(i64, i8*)
```

Produces output records of the format `"OUTPUT\tARRAY\tn\tlabel"` where `n` is the string representation of the integer value, such as `"OUTPUT\tARRAY\t4\tlabel"`. The fourth element (`label`) is a string label associated to the array which is included in the corresponding output record. This record indicates the existence of an array and how many elements it has.

## Examples

### Basic Single Item Output

A QIR program that contains a single call to the integer output recording function:

```llvm
@0 = internal constant [3 x i8] c"0_i\00"
call void @__quantum__rt__integer_record_output(i64 %5, i8* getelementptr inbounds ([3 x i8], [3 x i8]* @0, i32 0, i32 0))
ret void
```

The output for `3` shots would have the following form (using symbolic `METADATA` records):

```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tINT\t42\t0_i
END\t0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tINT\t41\t0_i
END\t0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tINT\t42\t0_i
END\t0
```

## Measurement Result Array Output

For two arrays of measurement results, the QIR program contains array output recording calls where the first argument indicates the length of the array, followed by the corresponding output recording calls that represent each one of the array items (shown with static result allocation):

```llvm
@0 = internal constant [5 x i8] c"0_0a\00"
@1 = internal constant [7 x i8] c"1_0a0r\00"
@2 = internal constant [5 x i8] c"2_1a\00"
@3 = internal constant [7 x i8] c"3_1a0r\00"
@4 = internal constant [7 x i8] c"4_1a1r\00"
call void @__quantum__rt__array_record_output(i64 1, i8* getelementptr inbounds ([5 x i8], [5 x i8]* @0, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* %2, i8* getelementptr inbounds ([7 x i8], [7 x i8]* @1, i32 0, i32 0))
call void @__quantum__rt__array_record_output(i64 2, i8* getelementptr inbounds ([5 x i8], [5 x i8]* @2, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 0 to %Result*), i8* getelementptr inbounds ([7 x i8], [7 x i8]* @3, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 0 to %Result*), i8* getelementptr inbounds ([7 x i8], [7 x i8]* @4, i32 0, i32 0))
ret void
```

The output for `3` shots would have the following form (using symbolic `METADATA` records):

```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tARRAY\t1\t0_0a
OUTPUT\tRESULT\t0\t1_0a0r
OUTPUT\tARRAY\t2\t2_1a
OUTPUT\tRESULT\t1\t3_1a0r
OUTPUT\tRESULT\t1\t4_1a1r
END\t0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tARRAY\t1\t0_0a
OUTPUT\tRESULT\t1\t1_0a0r
OUTPUT\tARRAY\t2\t2_1a
OUTPUT\tRESULT\t1\t3_1a0r
OUTPUT\tRESULT\t1\t4_1a1r
END\t0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tARRAY\t1\t0_0a
OUTPUT\tRESULT\t0\t1_0a0r
OUTPUT\tARRAY\t2\t2_1a
OUTPUT\tRESULT\t1\t3_1a0r
OUTPUT\tRESULT\t1\t4_1a1r
END\t0
```

## Tuple Output

Recording tuple output works much the same way as array output. So, a QIR program that returns a tuple of a measurement result and a double value uses the following output recording functions:

```llvm
@0 = internal constant [4 x i8] c"0_t\00"
@1 = internal constant [6 x i8] c"1_t0r\00"
@2 = internal constant [6 x i8] c"2_t1d\00"
call void @__quantum__rt__tuple_record_output(i64 2, i8* getelementptr inbounds ([4 x i8], [4 x i8]* @0, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* %2, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @1, i32 0, i32 0))
call void @__quantum__rt__double_record_output(double %3, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @2, i32 0, i32 0))
ret void
```

The output for `3` shots would have the following form (using symbolic `METADATA` records):

```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tRESULT\t0\t1_t0r
OUTPUT\tDOUBLE\t0.42\t2_t1d
END\t0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tRESULT\t1\t1_t0r
OUTPUT\tDOUBLE\t0.42\t2_t1d
END\t0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tRESULT\t0\t1_t0r
OUTPUT\tDOUBLE\t0.25\t2_t1d
END\t0
```

## Complex Output

Combining the above techniques can allow for complex output with nested container types. For example, a program that returns an array of tuples each containing an integer and result uses the following output recording functions:

```llvm
@0 = internal constant [4 x i8] c"0_a\00"
@1 = internal constant [6 x i8] c"1_a0t\00"
@2 = internal constant [8 x i8] c"2_a0t0i\00"
@3 = internal constant [8 x i8] c"3_a0t1r\00"
@4 = internal constant [6 x i8] c"4_a1t\00"
@5 = internal constant [8 x i8] c"5_a1t0i\00"
@6 = internal constant [8 x i8] c"6_a1t1r\00"
call void @__quantum__rt__array_record_output(i64 2, i8* getelementptr inbounds ([4 x i8], [4 x i8]* @0, i32 0, i32 0))
call void @__quantum__rt__tuple_record_output(i64 2, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @1, i32 0, i32 0))
call void @__quantum__rt__integer_record_output(i64 %3, i8* getelementptr inbounds ([8 x i8], [8 x i8]* @2, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* null, i8* getelementptr inbounds ([8 x i8], [8 x i8]* @3, i32 0, i32 0))
call void @__quantum__rt__tuple_record_output(i64 2, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @4, i32 0, i32 0))
call void @__quantum__rt__integer_record_output(i64 %7, i8* getelementptr inbounds ([8 x i8], [8 x i8]* @5, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 1 to %Result*), i8* getelementptr inbounds ([8 x i8], [8 x i8]* @6, i32 0, i32 0))
ret void
```

The output for one shot would have the following form (using symbolic `METADATA` records):

```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
START
METADATA\tentry_point
METADATA\tqir_profiles\tbase_profile
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
METADATA\tlabeling_format\tsample_format_name
OUTPUT\tARRAY\t2\t0_a
OUTPUT\tTUPLE\t2\t1_a0t
OUTPUT\tINT\t42\t2_a0t0i
OUTPUT\tRESULT\t3_a0t1r
OUTPUT\tTUPLE\t2\t4_a1t
OUTPUT\tINT\t33\t5_a1t0i
OUTPUT\tRESULT\t1\6_a1t1r
END\t0
```

[ordered format]: No_Labels_And_Ordered.md
