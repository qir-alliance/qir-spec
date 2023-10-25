# Ordered Output Schema

This output schema is meant for backends that can synchronously emit output records and do not support strings as arguments to functions.

## Records

The output emitted by a system consists of a series of records, where each record is separated by a line break.

Records are expected to have one to three elements tab-separated elements.

The first element of a record is always the record type, which can be any of the following: `HEADER`, `START`, `END`, `METADATA`, or `OUTPUT`.

### `HEADER` Records

`HEADER` records provide information about the emitted output. Records of this type have two additional elements:
- _name_: A string that represents the name of a property associated to the output.
- _value_: A string that represents the value of a property associates to the output.

`HEADER` records are not emitted based on the contents of the QIR program. Backends are responsible for emitting them to include information about the output such as the schema it conforms to or the schema version.

Examples of `HEADER` records:
```log
HEADER\tschema_name\tordered
HEADER\tschema_version\t1.0
```

### `START` Records

`START` records indicate the beginning of the output of a single execution of the program (shot). Records of this type do not have additional elements.

`START` records are not emitted based on the contents of the QIR program. Backends are responsible for emitting them, with the corresponding `END` records, to enclose the output of a shot.

An example of a `START` record:
```log
START
```

### `END` Records

`END` records indicate the end of the output of a single execution of the program (shot). Records of this type have an additional element:
- _exit_code_: An integer that represents the exit code of the program. The value `0` represents success and it currently is the only supported value.

`END` records are not emitted based on the contents of the QIR program. Backends are responsible for emitting them, with the corresponding `START` records, to enclose the output of a shot.

An example of an `END` record:
```log
END 0
```

### `METADATA` Records

`METADATA` records provide information about the shot's output and the program that produced it. Records of this type have two additional elements, one required and one optional:
- _attribute_name_ (required): A string that represents the name of an attribute of the program that emitted the output.
- _attribute_value_ (optional): A string that represents the value associated to an attribute of the program that emitted the output.

`METADATA` records are emitted based on the attributes present in the program's entry point function. For each one of these attributes, a `METADATA` record must be emitted. The [base profile required attributes section](../profiles/Base_Profile.md#attributes) specifies the minimum set of attributes that will be present. Specific examples can be found in the [notes for implementors](./Notes#examples).

Examples of `METADATA` records:
```log
METADATA\tentry_point
METADATA\trequired_num_qubits\t5
METADATA\trequired_num_results\t5
```

### `OUTPUT` Records

`OUTPUT` records represent an output value. Records of these type have two additional elements:
- _data_type_: A string that specifies the data type, which can be classified as a primitive data type or a container data type:
    - Primitive data types: Represent particular kinds of data and can be any of the following: `RESULT`, `BOOL`, `INT` or `DOUBLE`.
    - Container types: Represent kinds of containers and can be any of the following: `TUPLE` or `ARRAY`
- _data_value_: A string that represent the value of the output for primitive data types or an integer that represents the number of elements for container types.

`OUTPUT` records are emitted based on the [output recording function](../profiles/Base_Profile.md#output-recording) calls present in the program. The order in which `OUTPUT` records are emitted **must** match the order of the output recording function calls in the program.

Examples of `OUTPUT` records:
```log
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t1
OUTPUT\tBOOL\ttrue
OUTPUT\tBOOL\tfalse
OUTPUT\tINT\t42
OUTPUT\tDOUBLE\t3.14159
OUTPUT\tARRAY\t4
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tRESULT\t0
OUTPUT\tTUPLE\t2
OUTPUT\tRESULT\t0
OUTPUT\tBOOL\tfalse
```

## Output Structure

The output for each shot is expected to have the following structure:
1. One `START` record.
2. A variable number of `METADATA` records.
3. One or more `OUTPUT` records.
4. One `END` record.

Here's an example of the output emitted for a single shot:

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

END\t0
```

## Output Recording Functions

These runtime functions determine how values should be collected to be emitted as output. For simulation or future environments with full runtime support, these functions can be linked to implementations that directly perform the recording of output to the relevant stream. Each of these functions follow the naming pattern `__quantum__rt__*_record_output` where the initial part indicates the type of output to be recorded.

Though all the output recording functions have an `i8*` parameter representing a label, a `null` value may be passed when using the orderd output schema.

### Primitive Output Records

#### Result

```llvm
void @__quantum__rt__result_record_output(%Result*, i8*)
```

Produces output records that are exactly `"OUTPUT\tRESULT\t0"` or `"OUTPUT\tRESULT\t1"`, representing measurement results.

#### Boolean

```llvm
void @__quantum__rt__bool_record_output(i1, i8*)
```

Produces output records that are exactly `"OUTPUT\tBOOL\tfalse"` or `"OUTPUT\tBOOL\ttrue"`.

#### Integer

```llvm
void @__quantum__rt__integer_record_output(i64, i8*)
```

Produces output records of the format `"OUTPUT\tINT\tn"` where `n` is the string representation of the integer value, such as `"OUTPUT\tINT\t42"`.

#### Double

```llvm
void @__quantum__rt__double_record_output(double, i8*)
```

Produces output records of the format `"OUTPUT\tDOUBLE\td"` where `d` is the string representation of the double value, such as `"OUTPUT\tDOUBLE\t3.14159"`

### Tuple Output Records

```llvm
void @__quantum__rt__tuple_record_output(i64, i8*)
```

Produces output records of the format `"OUTPUT\tTUPLE\tn"` where `n` is the string representation of the integer value, such as `"OUTPUT\tTUPLE\t4"`. This record indicates the start of a tuple and how many elements it has.

### Array Output Records

```llvm
void @__quantum__rt__array_record_output(i64, i8*)
```

Produces output records of the format `"OUTPUT\tARRAY\tn"` where `n` is the string representation of the integer value, such as `"OUTPUT\tARRAY\t4"`. This record indicates the start of an array and how many elements it has.

## Examples

### Basic Single Item Output

A QIR program that contains a single call to the integer output recording function:

```llvm
call void @__quantum__rt__integer_record_output(i64 %5, i8* null)
ret void
```

The output for `3` shots would have the following form (using symbolic `METADATA` records):

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

For two arrays of measurement results, the QIR program contains array output recording calls where the first argument indicates the length of the array, followed by the corresponding output recording calls that represent each one of the array items (shown with static result allocation):

```llvm
call void @__quantum__rt__array_record_output(i64 1, i8* null)
call void @__quantum__rt__result_record_output(%Result* null, i8* null)
call void @__quantum__rt__array_record_output(i64 2, i8* null)
call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 1 to %Result*), i8* null)
call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 2 to %Result*), i8* null)
ret void
```

The output for `3` shots would have the following form (using symbolic `METADATA` records):

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

Recording tuple output works much the same way as array output. So, a QIR program that returns a tuple of a measurement result and a double value uses the following output recording functions:

```llvm
call void @__quantum__rt__tuple_record_output(i64 2, i8* null)
call void @__quantum__rt__result_record_output(%Result* %2, i8* null)
call void @__quantum__rt__double_record_output(double %3, i8* null)
ret void
```

The output for `3` shots would have the following form (using symbolic `METADATA` records):

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

Combining the above techniques can allow for complex output with nested container types. For example, a program that returns an array of tuples each containing an integer and result uses the following output recording functions:

```llvm
call void @__quantum__rt__array_record_output(i64 2, i8* null)
call void @__quantum__rt__tuple_record_output(i64 2, i8* null)
call void @__quantum__rt__integer_record_output(i64 %3, i8* null)
call void @__quantum__rt__result_record_output(%Result* null, i8* null)
call void @__quantum__rt__tuple_record_output(i64 2, i8* null)
call void @__quantum__rt__integer_record_output(i64 %7, i8* null)
call void @__quantum__rt__result_record_output(%Result* nonnull inttoptr (i64 1 to %Result*), i8* null)
ret void
```

The output for one shot would have the following form (using symbolic `METADATA` records):

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
