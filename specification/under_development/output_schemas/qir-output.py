# /// script
# dependencies = [
#   "lark>=1.2.2",
#   "rich>=14.1.0",
# ]
# ///

# =============================================================================
# NOTE: Run this script using:
#       uv run qir-output.py < qir-output.txt
# =============================================================================

import sys

from lark import Lark
from rich import print as rprint


def main():
    grammar = r"""
        start: file

        file: header_schema_name header_schema_version (header)* (shot)+
        header_schema_name: HEADER_LIT TAB SCHEMA_NAME_LIT TAB (ORDERED_SCHEMA_LIT | LABELED_SCHEMA_LIT)
        header_schema_version: HEADER_LIT TAB SCHEMA_VERSION_LIT TAB field
        header: HEADER_LIT TAB field TAB field
        shot: START_LIT (record)* END_LIT
        record: metadata | output
        metadata: METADATA_LIT TAB field (TAB field)?
        output: container | value
        container: tuple | array

        // Labeled
        value: OUTPUT_LIT TAB (RESULT_LIT TAB BIT | BOOL_LIT TAB (TRUE_LIT | FALSE_LIT) | INT_LIT TAB SIGNED_DIGIT | DOUBLE_LIT TAB DOUBLE_VALUE) (TAB label)?
        tuple: OUTPUT_LIT TAB TUPLE_LIT TAB DIGITS (TAB label)?
        array: OUTPUT_LIT TAB ARRAY_LIT TAB DIGITS (TAB label)?

        // Ordered
        // (Extend as needed for ordered/collection-items)

        label: ESCAPED | NON_ESCAPED
        field: ESCAPED | NON_ESCAPED

        ESCAPED: DQUOTE NON_ESCAPED DQUOTE
        NON_ESCAPED: /[ !#-\[\]-~]+/

        TAB: /\t/ | "\\t"
        DQUOTE: "\""

        HEADER_LIT: "HEADER"
        SCHEMA_NAME_LIT: "schema_id"
        SCHEMA_VERSION_LIT: "schema_version"
        ORDERED_SCHEMA_LIT: "ordered"
        LABELED_SCHEMA_LIT: "labeled"
        START_LIT: "START"
        END_LIT: "END" TAB "0"
        METADATA_LIT: "METADATA"
        OUTPUT_LIT: "OUTPUT"
        BOOL_LIT: "BOOL"
        INT_LIT: "INT"
        DOUBLE_LIT: "DOUBLE"
        RESULT_LIT: "RESULT"
        TUPLE_LIT: "TUPLE"
        ARRAY_LIT: "ARRAY"
        TRUE_LIT: "true"
        FALSE_LIT: "false"
        INF_LIT: "INF"
        INFINITY_LIT: "INFINITY"
        NAN_LIT: "NAN"
        BIT: "0" | "1"
        SIGN: "+" | "-"
        DIGIT: /[0-9]/
        DIGITS: DIGIT+
        SIGNED_DIGIT: SIGN? DIGITS
        DOUBLE_VALUE: SIGN? (INF_LIT | INFINITY_LIT | NAN_LIT | FLOAT)
        FLOAT: DIGITS ("." DIGITS)? EXPONENT?
        EXPONENT: "e" SIGN? DIGITS

        # Ignore all whitespace except TAB characters
        %ignore /[ \r\n\f]+/
    """

    parser = Lark(grammar, start="file", parser="lalr")

    if sys.stdin.isatty():
        rprint("[red]Error:[/red] No input detected. Provide QIR output using stdin.")
        sys.exit(1)
    output_str = sys.stdin.read()
    rprint(parser.parse(output_str))


if __name__ == "__main__":
    main()
