# Back End Support for Adaptive Profile
The following table contains rows listing of each optional feature in the adaptive profile via [module flags](../Adaptive_Profile.md#module-flags-metadata)
as described in the [program structure](../Adaptive_Profile.md##program-structure), and
columns with hardware providers using the adaptive profile to indicate whether or not they support each feature via a ✓ or x.

|                         | Quantinuum                              | Placeholder Backend 1 | Placeholder Backend 2 | Placeholder Backend 3 |
| :-----------------------| :---------------------------------------| :---------------------| :---------------------| :---------------------|
| qubit_resetting         | ✓ | ? | ? | ? |
| classical_ints          | ✓ (\*constant denominators for div/rem) | ? | ? | ? |
| classical_floats        | x | ? | ? | ? |
| classical_fixed_points  | x | ? | ? | ? |
| user_functions          | x | ? | ? | ? |
| dynamic_float_args      | x | ? | ? | ? |
| extern_functions        | ✓ (\*via web assembly) | ? | ? | ? |
| backwards_branching     | x | ? | ? | ? |
| multiple_target_branching| X | ? | ? | ? |

For now, only the Quantinuum support is specified above, but other providers should put in pull requests.
When a change to add more functionality is publicly available from a provider or to add a provider's description of support for the adaptive profile,
then a pull request should be made by the provider to update the above table.


