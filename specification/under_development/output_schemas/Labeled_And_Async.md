# Labeled Format for Asynchronous Output Generation

The labeled format for asynchronous output generation is the same as the [ordered format][] with the following changes:
  - `OUTPUT` records `TUPLE`, `ARRAY`, `RESULT`, `INT`, `BOOL`, and `DOUBLE` types have a fourth field indicating the label/tag of the record.

Example log for a single shot:

```log
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
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

## Declared Runtime Functions 

Each of these runtime functions are meant as signifiers to the provider as to how raw device results should be collected into the common output format. For simulation or future environments with full runtime support, these functions can be linked to implementations that directly perform the recording of output to the relevant stream. Each of these functions follow the naming pattern `__quantum__rt__*_record_output` where the initial part indicates the type of output to be recorded.  

### Primitive Result Records 

```llvm
void @__quantum__rt__result_record_output(%Result*, i8*)
```

Adds a measurement result to the generated output. It produces output records of exactly `"OUTPUT\tRESULT\t0\ttag"` or `"OUTPUT\tRESULT\t1\ttag"`. The second parameter defines a string label for the result value which is included in the output (`tag`).

```llvm
void @__quantum__rt__bool_record_output(i1, i8*)
```

produces output records of exactly `"OUTPUT\tBOOL\tfalse\ttag"` or `"OUTPUT\tBOOL\ttrue\ttag"`.  The second parameter defines a string label for the result value which is included in the output  (`tag`).

```llvm
void @__quantum__rt__integer_record_output(i64, i8*)
```

produces output records of the format `"OUTPUT\tINT\tn\ttag"` where `n` is the string representation of the integer value, such as `"OUTPUT\tINT\t42\ttag"`.  The second parameter defines a string label for the result value which is included in the output (`tag`).

```llvm
void @__quantum__rt__double_record_output(double, i8*) 
```

produces output records of the format `"OUTPUT\tDOUBLE\td\ttag"` where `d` is the string representation of the double value, such as `"OUTPUT\tDOUBLE\t3.14159\ttag"`. The second parameter defines a string label for the result value which is included in the output (`tag`).

### Tuple Type Records

```llvm
void @__quantum__rt__tuple_record_output(i64, i8*)
```

Inserts a marker in the generated output that indicates the start of a tuple and how many tuple elements it has. It produces output records of exactly `"OUTPUT\tTUPLE\tn\ttag"` where `n` is the string representation of the integer value, such as `"OUTPUT\tTUPLE\t4\ttag"`.  The second parameter defines a string label for the result value which is included in the output (`tag`).

### Array Type Records

```llvm
void @__quantum__rt__array_record_output(i64, i8*)
```

Inserts a marker in the generated output that indicates the start of an array and how many array elements it has. It produces output records of exactly `"OUTPUT\tARRAY\tn\ttag"` where `n` is the string representation of the integer value, such as `"OUTPUT\tARRAY\t4\ttag"`.  The second parameter defines a string label for the result value which is included in the output (`tag`).

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
OUTPUT\tINT\t42\t0_i
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tINT\t41\t0_i
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tINT\t42\t0_i 
END\t0
```

## Measurement Result Array Output 

For an array of measurement results (or classical register), the QIR program would include array start and end calls, with intervening result record calls (shown with static result allocation transformations performed): 

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
OUTPUT\tARRAY\t1\t0_0a
OUTPUT\tRESULT\t0\t1_0a0r
OUTPUT\tARRAY\t2\t2_1a
OUTPUT\tRESULT\t1\t3_1a0r
OUTPUT\tRESULT\t1\t4_1a1r
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tARRAY\t1\t0_0a
OUTPUT\tRESULT\t1\t1_0a0r
OUTPUT\tARRAY\t2\t2_1a
OUTPUT\tRESULT\t1\t3_1a0r
OUTPUT\tRESULT\t1\t4_1a1r
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
OUTPUT\tARRAY\t1\t0_0a
OUTPUT\tRESULT\t0\t1_0a0r
OUTPUT\tARRAY\t2\t2_1a
OUTPUT\tRESULT\t1\t3_1a0r
OUTPUT\tRESULT\t1\t4_1a1r
END\t0
```

## Tuple Output 

Recording tuple output works much the same way as array output, but with a different delimiter character in the final processed output. So, a QIR program that returns a tuple of a measurement result and calculated double value would end with: 

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
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tRESULT\t0\t1_t0r
OUTPUT\tDOUBLE\t0.42\t2_t1d
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tRESULT\t1\t1_t0r
OUTPUT\tDOUBLE\t0.42\t2_t1d
END\t0
START
METADATA\tmetadata1_name_only
METADATA\tmetadata2_name\tmetadata2_value
METADATA\tmetadata3_name\tmetadata3_value
OUTPUT\tTUPLE\t2\t0_t
OUTPUT\tRESULT\t0\t1_t0r
OUTPUT\tDOUBLE\t0.25\t2_t1d
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
OUTPUT\tARRAY\t2\t0_a
OUTPUT\tTUPLE\t2\t1_a0t
OUTPUT\tINT\t42\t2_a0t0i
OUTPUT\tRESULT\t3_a0t1r
OUTPUT\tTUPLE\t2\t4_a1t
OUTPUT\tINT\t33\t5_a1t0i
OUTPUT\tRESULT\t1\6_a1t1r
END\t0
```

[base profile]: ../profiles/Base_Profile.md
[ordered format]: No_Labels_And_Ordered.md
 