# Output Schemas

Output schemas specify how backends generate the output of a QIR program based
on calls to output recording functions in the
[Base](../profiles/Base_Profile.md#output-recording) and
[Adaptive](../profiles/Adaptive_Profile.md#output-recording) Profiles.

Each backend can decide which output schema to use depending on the
characteristics of their system.

There are two output schemas:

- **[Ordered](./Ordered.md)**: for backends that synchronously emit output
records and do not support strings as arguments to functions.
- **[Labeled](./Labeled.md)**: for backends that asynchronously emit output
records and support strings as arguments to functions.

Grammars that define the structure and valid values for these schemas are
available in [Grammars.md](./Grammars.md).

Additional information and examples for implementers can be found in
[Notes.md](./Notes.md).
