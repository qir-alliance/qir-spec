# Appendix: Library Reference

This table lists all of the runtime functions specified by QIR:

| Function                        | Signature                                  | Description |
|---------------------------------|--------------------------------------------|-------------|
| __quantum__rt__array_concatenate | `ptr(ptr, ptr)`          | Returns a new array which is the concatenation of the two passed-in one-dimensional arrays. If either array is not one-dimensional or if the array element sizes are not the same, then a runtime failure should occur. |
| __quantum__rt__array_copy        | `ptr(ptr, i1)`                   | Creates a shallow copy of the array if the alias count is larger than 0 or the second argument is `true`. Returns the given array pointer (the first parameter) otherwise, after increasing its reference count by 1. The reference count of the array elements remains unchanged. |
| __quantum__rt__array_create      | `ptr void(i32, i32, ptr)`       | Creates a new array. The first `i32` is the size of each element in bytes. The second `i32` is the dimension count. The `ptr` should point to an array of `i64`s contains the length of each dimension. The bytes of the new array should be set to zero. If any length is zero, the result should be an empty array with the given number of dimensions. |
| __quantum__rt__array_create_1d   | `ptr void(i32, i64)`             | Creates a new 1-dimensional array. The `i32` is the size of each element in bytes. The `i64` is the length of the array. The bytes of the new array should be set to zero. If the length is zero, the result should be an empty 1-dimensional array. |
| __quantum__rt__array_get_dim     | `i32(ptr)`                       | Returns the number of dimensions in the array. |
| __quantum__rt__array_get_element_ptr | `ptr(ptr, ptr)`             | Returns a pointer to the indicated element of the array. The `ptr` should point to an array of `i64`s that are the indices for each dimension. |
| __quantum__rt__array_get_element_ptr_1d | `ptr(ptr, i64)`           | Returns a pointer to the element of the array at the zero-based index given by the `i64`. |
| __quantum__rt__array_get_size  | `i64(ptr, i32)`                  | Returns the length of a dimension of the array. The `i32` is the zero-based dimension to return the length of; it must be smaller than the number of dimensions in the array. |
| __quantum__rt__array_get_size_1d  | `i64(ptr)`                  | Returns the length of a 1-dimensional array. |
| __quantum__rt__array_project     | `ptr(ptr, i32, i64, i1)`         | Creates and returns an array that is a projection of an existing array. The projection may be accessing the same memory as the given array unless its alias count is larger than 0 or the last argument is `true`. The `i32` indicates which dimension the projection is on, and the `i64` specifies the index in that dimension to project. The reference count of all array elements remains unchanged. If the existing array is one-dimensional then a runtime failure should occur. |
| __quantum__rt__array_slice       | `ptr(ptr, i32, {i64, i64, i64}, i1)`      | Creates and returns an array that is a slice of an existing array. The slice may be accessing the same memory as the given array unless its alias count is larger than 0 or the last argument is `true`. The `i32` indicates which dimension the slice is on, and must be smaller than the number of dimensions in the array. The `{i64, i64, i64}` range specifies the indices in that dimension that should be the elements of the returned array. The reference count of the elements remains unchanged. |
| __quantum__rt__array_slice_1d       | `ptr(ptr, {i64, i64, i64}, i1)`      | Creates and returns an array that is a slice of an existing 1-dimensional array. The slice may be accessing the same memory as the given array unless its alias count is larger than 0 or the last argument is `true`. The `{i64, i64, i64}` range specifies the indices that should be the elements of the returned array. The reference count of the elements remains unchanged. |
| __quantum__rt__array_update_alias_count | `void(ptr, i32)` | Adds the given integer value to the alias count for the array. Fails if either count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__array_update_reference_count   | `void(ptr, i32)` | Adds the given integer value to the reference count for the array. Deallocates the array if the reference count becomes 0. The behavior is undefined if the reference count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__bigint_add         | `ptr(ptr, ptr)` | Adds two big integers and returns their sum. |
| __quantum__rt__bigint_bitand      | `ptr(ptr, ptr)` | Returns the bitwise-AND of two big integers. |
| __quantum__rt__bigint_bitnot      | `ptr(ptr)`           | Returns the bitwise complement of the big integer. |
| __quantum__rt__bigint_bitor       | `ptr(ptr, ptr)` | Returns the bitwise-OR of two big integers. |
| __quantum__rt__bigint_bitxor      | `ptr(ptr, ptr)` | Returns the bitwise-XOR of two big integers. |
| __quantum__rt__bigint_create_array | `ptr(i32, ptr)`    | Creates a big integer with the value specified by the `i8` array. The 0-th element of the array is the highest-order byte, followed by the first element, etc. |
| __quantum__rt__bigint_create_i64  | `ptr(i64)`                | Creates a big integer with the specified initial value. |
| __quantum__rt__bigint_divide      | `ptr(ptr, ptr)` | Divides the first big integer by the second and returns their quotient. |
| __quantum__rt__bigint_equal       | `i1(ptr, ptr)`       | Returns true if the two big integers are equal, false otherwise. |
| __quantum__rt__bigint_get_data    | `ptr(ptr)`      | Returns a pointer to the `i8` array containing the value of the big integer. |
| __quantum__rt__bigint_get_length  | `i32(ptr)`      | Returns the length of the `i8` array that represents the big integer value. |
| __quantum__rt__bigint_greater     | `i1(ptr, ptr)`       | Returns true if the first big integer is greater than the second, false otherwise. |
| __quantum__rt__bigint_greater_eq  | `i1(ptr, ptr)`       | Returns true if the first big integer is greater than or equal to the second, false otherwise. |
| __quantum__rt__bigint_modulus     | `ptr(ptr, ptr)` | Returns the first big integer modulo the second. |
| __quantum__rt__bigint_multiply    | `ptr(ptr, ptr)` | Multiplies two big integers and returns their product. |
| __quantum__rt__bigint_negate      | `ptr(ptr)`           | Returns the negative of the big integer. |
| __quantum__rt__bigint_power       | `ptr(ptr, i32)`      | Returns the big integer raised to the integer power. As with standard integers, the exponent must fit in 32 bits. |
| __quantum__rt__bigint_shiftleft   | `ptr(ptr, i64)`      | Returns the big integer arithmetically shifted left by the (positive) integer amount of bits. |
| __quantum__rt__bigint_shiftright  | `ptr(ptr, i64)`      | Returns the big integer arithmetically shifted right by the (positive) integer amount of bits. |
| __quantum__rt__bigint_subtract    | `ptr(ptr, ptr)` | Subtracts the second big integer from the first and returns their difference. |
| __quantum__rt__bigint_to_string  | `ptr(ptr)` | Returns a string representation of the big integer. |
| __quantum__rt__bigint_update_reference_count   | `void(ptr, i32)` | Adds the given integer value to the reference count for the big integer. Deallocates the big integer if the reference count becomes 0. The behavior is undefined if the reference count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__bool_to_string    | `ptr(i1)`       | Returns a string representation of the Boolean. |
| __quantum__rt__callable_copy    | `ptr(ptr, i1)`             | Creates a shallow copy of the callable if the alias count is larger than 0 or the second argument is `true`. Returns the given callable pointer (the first parameter) otherwise, after increasing its reference count by 1. The reference count of the capture tuple remains unchanged. If the `ptr` parameter is null, a runtime failure should occur. |
| __quantum__rt__callable_create  | `ptr(ptr, ptr, ptr)` | Initializes the callable with the provided function table, memory management table, and capture tuple. The memory management table pointer and the capture tuple pointer should be null if there is no capture. |
| __quantum__rt__callable_invoke  | `void(ptr, ptr, ptr)` | Invokes the callable with the provided argument tuple and fills in the result tuple. The `ptr` parameters may be null if the callable either takes no arguments or returns `Unit`. If the `ptr` parameter is null, a runtime failure should occur. |
| __quantum__rt__callable_make_adjoint | `void(ptr)`                         | Updates the callable by applying the Adjoint functor. If the `ptr` parameter is null or if the corresponding entry in the callable's function table is null, a runtime failure should occur. |
| __quantum__rt__callable_make_controlled | `void(ptr)`                      | Updates the callable by applying the Controlled functor. If the `ptr` parameter is null or if the corresponding entry in the callable's function table is null, a runtime failure should occur. |
| __quantum__rt__callable_update_alias_count | `void(ptr, i32)`                      | Adds the given integer value to the alias count for the callable. Fails if the count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__callable_update_reference_count | `void(ptr, i32)`                      | Adds the given integer value to the reference count for the callable. Deallocates the callable if the reference count becomes 0. The behavior is undefined if the reference count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__capture_update_alias_count | `void(ptr, i32)`                      | Invokes the function at index 1 in the memory management table of the callable with the capture tuple and the given 32-bit integer. Does nothing if the memory management table pointer or the function pointer at that index is null, or if the given `ptr` is a null pointer. |
| __quantum__rt__capture_update_reference_count | `void(ptr, i32)`                      | Invokes the function at index 0 in the memory management table of the callable with the capture tuple and the given 32-bit integer. Does nothing if if the memory management table pointer or the function pointer at that index is null, or if the given `ptr` is a null pointer. |
| __quantum__rt__double_to_string  | `ptr(Double)`   | Returns a string representation of the double. |
| __quantum__rt__fail       | `void(ptr)`  | Fail the computation with the given error message. |
| __quantum__rt__int_to_string     | `ptr(i64)`      | Returns a string representation of the integer. |
| __quantum__rt__message    | `void(ptr)`  | Include the given message in the computation's execution log or equivalent. |
| __quantum__rt__pauli_to_string   | `ptr(i2)`   | Returns a string representation of the Pauli. |
| __quantum__rt__qubit_allocate       | `ptr()`     | Allocates a single qubit. |
| __quantum__rt__qubit_allocate_array | `ptr(i64)`  | Creates an array of the given size and populates it with newly-allocated qubits. |
| __quantum__rt__qubit_release        | `void(ptr)` | Releases a single qubit. Passing a null pointer as argument should cause a runtime failure. |
| __quantum__rt__qubit_release_array  | `void(ptr)` | Releases an array of qubits; each qubit in the array is released, and the array itself is unreferenced. Passing a null pointer as argument should cause a runtime failure. |
| __quantum__rt__qubit_to_string   | `ptr(ptr)`  | Returns a string representation of the qubit. |
| __quantum__rt__range_to_string   | `ptr({i64, i64, i64})`   | Returns a string representation of the range. |
| __quantum__rt__result_equal       | `i1(ptr, ptr)` | Returns true if the two results are the same, and false if they are different. If a `ptr` parameter is null, a runtime failure should occur. |
| __quantum__rt__result_get_one     | `ptr()`             | Returns a constant representing a measurement result one.  |
| __quantum__rt__result_get_zero    | `ptr()`             | Returns a constant representing a measurement result zero. |
| __quantum__rt__result_to_string  | `ptr(ptr)` | Returns a string representation of the result. |
| __quantum__rt__result_update_reference_count   | `void(ptr, i32)` | Adds the given integer value to the reference count for the result. Deallocates the result if the reference count becomes 0. The behavior is undefined if the reference count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__string_concatenate | `ptr(ptr, ptr)` | Creates a new string that is the concatenation of the two argument strings. If a `ptr` parameter is null, a runtime failure should occur. |
| __quantum__rt__string_create      | `ptr(ptr)`      | Creates a string from an array of UTF-8 bytes. The byte array is expected to be zero-terminated. |
| __quantum__rt__string_equal       | `i1(ptr, ptr)`       | Returns true if the two strings are equal, false otherwise. If a `ptr` parameter is null, a runtime failure should occur. |
| __quantum__rt__string_get_data    | `ptr(ptr)`      | Returns a pointer to the zero-terminated array of UTF-8 bytes. |
| __quantum__rt__string_get_length  | `i32(ptr)`      | Returns the length of the byte array that contains the string data. |
| __quantum__rt__string_update_reference_count   | `void(ptr, i32)` | Adds the given integer value to the reference count for the string. Deallocates the string if the reference count becomes 0. The behavior is undefined if the reference count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__tuple_copy      | `ptr(ptr, i1)`  | Creates a shallow copy of the tuple if the alias count is larger than 0 or the second argument is `true`. Returns the given tuple pointer (the first parameter) otherwise, after increasing its reference count by 1. The reference count of the tuple elements remains unchanged. If the `ptr` parameter is null, a runtime failure should occur. |
| __quantum__rt__tuple_create      | `ptr(i64)`  | Allocates space for a tuple requiring the given number of bytes, sets the reference count to 1 and the alias count to 0. |
| __quantum__rt__tuple_update_alias_count | `void(ptr, i32)` | Adds the given integer value to the alias count for the tuple. Fails if the count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |
| __quantum__rt__tuple_update_reference_count   | `void(ptr, i32)` | Adds the given integer value to the reference count for the tuple. Deallocates the tuple if the reference count becomes 0. The behavior is undefined if the reference count becomes negative. The call should be ignored if the given `ptr` is a null pointer. |

---

*[Back to index](README.md)*
