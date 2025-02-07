# Ordered Output Format with Optional Labels

For systems that don't support string parameters, the ordered output format can be used. This format omits any labels that are passed through output recording functions. A [grammar](./Grammars.md#no-labels-and-ordered) for this format is available which defines the structure and valid values.

The format specifies what the [output recording](../profiles/Base_Profile.md#output-recording) functions emit based on the selected schema and entry point [attributes][].

## Record types

Records are expected to have 1-3 fields:

- RecordType: an id that identifies the type of content in the record. The only supported RecordTypes will be `START`, `METADATA`, `OUTPUT`, and `END`.
  - `START` indicates the beginning of a shot's output definition
  - `METADATA` records have a name field and optional value field
  - `OUTPUT` records have a type in the set: `RESULT`, `TUPLE`, `ARRAY`, `INT`, `BOOL`, or `DOUBLE`.
    - `TUPLE` and `ARRAY` types have a third field indicating the number of items in the container.
    - `RESULT`, `INT`, `BOOL`, `DOUBLE` types have a third field indicating the value of the record.
  - `END` indicate the completion of a shot's output definition with the exit code for the entry point.

Output for each shot is expected to have:

- One `START` record
- `METADATA` records for each of the defined entry point attributes. The generation of these records is not part of the generated QIR, but written as part of the [base profile][] spec as pass-thru metadata. The [base profile required attributes](../profiles/Base_Profile.md#attributes) define the minimum set of attributes which will appear. Examples can be found in the [notes for implementors examples](./Notes_For_Implementors.md#examples).
- One or more `OUTPUT` records
- One `END` record

The `START` and `END` records define a shot, but are not part of the generated QIR. They are produced as part of the provider's recording of a shot's output. The `START` record does not have any value entry. The `END` record has a value entry of `0`. The `OUTPUT` records will have a value corresponding to the runtime function called, either a result type record or a string representation of a supported primitive type. The `OUTPUT` records must appear in the same order as the calls in the QIR program.

Example log for a single shot:

```log
START
METADATA\tuser_metadata1_name_only
METADATA\tuser_metadata2_name\tuser_metadata2_value
METADATA\tuser_metadata3_name\tuser_metadata3_value
METADATA\tentry_point
METADATA\tnum_required_qubits\t5
METADATA\tnum_required_results\t5
METADATA\toutput_labeling_schema
METADATA\tqir_profiles\tbase_profile
OUTPUT\tTUPLE\t2
OUTPUT\tARRAY\t4
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t3
OUTPUT\tBOOL\ttrue
OUTPUT\tINT\t42
OUTPUT\tDOUBLE\t3.1415
END\t0
```

## Declared Runtime Functions

Each of these runtime functions are meant as signifiers to the provider as to how raw device results should be collected into the common output format. For simulation or future environments with full runtime support, these functions can be linked to implementations that directly perform the recording of output to the relevant stream. Each of these functions follow the naming pattern `__quantum__rt__*_record_output` where the initial part indicates the type of output to be recorded.

Though the output format is labeled, the label parameters for the output recording calls may still provide values which are treated as if the QIR had specified the label as `i8* null`.

### Primitive Result Records

```llvm
void @__quantum__rt__result_record_output(%Result*, i8*)
```

Adds a measurement result to the generated output. It produces output records of exactly `"OUTPUT\tRESULT\t0"` or `"OUTPUT\tRESULT\t1"`. The second parameter defines a string label for the result value. Depending on the output schema, the label is included in the output or omitted.

```llvm
void @__quantum__rt__bool_record_output(i1, i8*)
```

produces output records of exactly `"OUTPUT\tBOOL\tfalse"` or `"OUTPUT\tBOOL\ttrue"`

```llvm
void @__quantum__rt__integer_record_output(i64, i8*)
```

produces output records of the format `"OUTPUT\tINT\tn"` where `n` is the string representation of the integer value, such as `"OUTPUT\tINT\t42"`

```llvm
void @__quantum__rt__double_record_output(double, i8*)
```

produces output records of the format `"OUTPUT\tDOUBLE\td"` where `d` is the string representation of the double value, such as `"OUTPUT\tDOUBLE\t3.14159"`

### Tuple Type Records

```llvm
void @__quantum__rt__tuple_record_output(i64, i8*)
```

Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. It produces output records of exactly `"OUTPUT\tTUPLE\tn"` where `n` is the string representation of the integer value, such as `"OUTPUT\tTUPLE\t4"`. The second parameter defines a string label for the tuple. Depending on the output schema, the label is included in the output or omitted.

### Array Type Records

```llvm
void @__quantum__rt__array_record_output(i64, i8*)
```

Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. It produces output records of exactly `"OUTPUT\tARRAY\tn"` where `n` is the string representation of the integer value, such as `"OUTPUT\tARRAY\t4"`. The second parameter defines a string label for the array. Depending on the output schema, the label is included in the output or omitted.

## Examples

### Basic Single Item Output

The QIR program would include a single call to the runtime function matching the type of the return value:

```llvm
@0 = internal constant [3 x i8] c"0_i\00"
call void @__quantum__rt__integer_record_output(i64 %5, i8* getelementptr inbounds ([3 x i8], [3 x i8]* @0, i32 0, i32 0))
ret void
```

Such that the provider output for `3` shots would be:

```log
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tINT\t42
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tINT\t41
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tINT\t42
END\t0
```

## Measurement Result Array Output

For an array of measurement results (or classical values), the QIR program would include an array output recording call, where the first argument indicates the length of the array, followed by the corresponding output recording calls that represent each one of the array items (shown with static result allocation transformations performed):

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

This would produce provider output for `3` shots of the form:

```log
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tARRAY\t1
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t1
OUTPUT\tRESULT\t1
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tARRAY\t1
OUTPUT\tRESULT\t1
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t1
OUTPUT\tRESULT\t1
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tARRAY\t1
OUTPUT\tRESULT\t0
OUTPUT\tARRAY\t2
OUTPUT\tRESULT\t1
OUTPUT\tRESULT\t1
END\t0
```

## Tuple Output

Recording tuple output works much the same way as array output. So, a QIR program that returns a tuple of a measurement result and calculated double value would end with:

```llvm
@0 = internal constant [4 x i8] c"0_t\00"
@1 = internal constant [6 x i8] c"1_t0r\00"
@2 = internal constant [6 x i8] c"2_t1d\00"
call void @__quantum__rt__tuple_record_output(i64 2, i8* getelementptr inbounds ([4 x i8], [4 x i8]* @0, i32 0, i32 0))
call void @__quantum__rt__result_record_output(%Result* %2, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @1, i32 0, i32 0))
call void @__quantum__rt__double_record_output(double %3, i8* getelementptr inbounds ([6 x i8], [6 x i8]* @2, i32 0, i32 0))
ret void
```

Here producing a provider output for `3` shots of the form:

```log
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
OUTPUT\tTUPLE\t2
OUTPUT\tRESULT\t0
OUTPUT\tDOUBLE\t0.42
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
OUTPUT\tTUPLE\t2
OUTPUT\tRESULT\t1
OUTPUT\tDOUBLE\t0.42
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
OUTPUT\tTUPLE\t2
OUTPUT\tRESULT\t0
OUTPUT\tDOUBLE\t0.25
END\t0
```

## Complex Output

Combining the above techniques can allow for complex output with nested container types. For example, a program that returns an array of tuples each containing an integer and result might have QIR with a pattern of:

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
call void @__quantum__rt__result_record_output((%Result* nonnull inttoptr (i64 1 to %Result*), i8* getelementptr inbounds ([8 x i8], [8 x i8]* @6, i32 0, i32 0))
ret void
```

Such a QIR program would produce output for a single shot in the form:

```log
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
OUTPUT\tARRAY\t2
OUTPUT\tTUPLE\t2
OUTPUT\tINT\t42
OUTPUT\tRESULT\t0
OUTPUT\tTUPLE\t2
OUTPUT\tINT\t33
OUTPUT\tRESULT\t1
END\t0
```

[base profile]: ../profiles/Base_Profile.md
[attributes]: ../profiles/Base_Profile.md#attributes
