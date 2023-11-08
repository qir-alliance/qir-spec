# Back End Support for Adaptive Profile

The following table contains rows listing of each optional feature in the adaptive profile via [module flags](../Adaptive_Profile.md#module-flags-metadata)
as described in the [program structure](../Adaptive_Profile.md#program-structure), and
columns with hardware providers using the adaptive profile to indicate whether or not they support each feature via a ✓ or x.

|                           | Placeholder Backend 0                    | Placeholder Backend 1 | Placeholder Backend 2 | Placeholder Backend 3 |
| :------------------------ | :--------------------------------------- | :-------------------- | :-------------------- | :-------------------- |
| qubit_resetting           | ✓                                        | ?                     | ?                     | ?                     |
| classical_ints            | ✓                                        | ?                     | ?                     | ?                     |
| classical_floats          | x                                        | ?                     | ?                     | ?                     |
| classical_fixed_points    | x                                        | ?                     | ?                     | ?                     |
| user_functions            | x                                        | ?                     | ?                     | ?                     |
| dynamic_float_args        | x                                        | ?                     | ?                     | ?                     |
| extern_functions          | ✓                                        | ?                     | ?                     | ?                     |
| backwards_branching       | x                                        | ?                     | ?                     | ?                     |
| multiple_target_branching | X                                        | ?                     | ?                     | ?                     |

