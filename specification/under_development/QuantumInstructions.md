# Quantum Instruction Set

All quantum instructions are represented by LLVM external functions.
Quantum instructions may take qubits, doubles, or integers as parameters,
and should all have no return; that is, they should be void.

Measurements should take an offset into the `ClassicalStorage` global as a parameter.
The measurement result should be stored into the corresponding bit in `ClassicalStorage`.

The LLVM functions that implement the quantum instruction set should all have
names that start with `__quantum__qis__`.

QIR does not specify the contents of the quantum instruction set.
However, in order to ensure some amount of uniformity, implementations that provide
any of the following quantum instructions must match the specified definition:

| Operation Name | LLVM Function Declaration  | Description | Matrix |
|----------------|----------------------------|-------------|--------|
| CCx, CCNOT, Toffoli | `__quantum__qis__toffoli__body (%Qubit control1, %Qubit control1, %Qubit target)` | Toffoli or doubly-controlled X | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+1+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+1+%26+0+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+1+%26+0+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+0+%26+1+%26+0+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+0+%26+0+%26+1+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+1+%5C%5C+0+%26+0+%26+0+%26+0+%26+0+%26+0+%26+1+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Cx, CNOT | `__quantum__qis__cnot__body (%Qubit control, %Qubit target)` | CNOT or singly-controlled X | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%26+0+%26+0+%5C%5C+0+%26+1+%26+0+%26+0+%5C%5C+0+%26+0+%26+0+%26+1+%5C%5C+0+%26+0+%26+1+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Cz | `__quantum__qis__cz__body (%Qubit control, %Qubit target)` | Singly-controlled Z | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%26+0+%26+0+%5C%5C+0+%26+1+%26+0+%26+0+%5C%5C+0+%26+0+%26+1+%26+0+%5C%5C+0+%26+0+%26+0+%26+-1+%5C%5C+%5Cend%7Bbmatrix%7D) |
| H | `__quantum__qis__h__body (%Qubit q)` | Hadamard | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cfrac%7B1%7D%7B%5Csqrt%7B2%7D%7D%5Cbegin%7Bbmatrix%7D+1+%26+1+%5C%5C+1+%26+-1+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Mz or Measure | `__quantum__qis__mz__body (%Qubit q, i32 result_offset)` | Measure a qubit along the the Pauli Z axis |
| Reset | `__quantum__qis__reset__body (%Qubit q)` | Prepare a qubit in the \|0⟩ state |
| Rx | `__quantum__qis__rx__body (%Qubit q, double theta)` | Rotate a qubit around the Pauli X axis | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+-i%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+-i%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Ry | `__quantum__qis__ry__body (%Qubit q, double theta)` | Rotate a qubit around the Pauli Y axis | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+-%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+%5Csin+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%26+%5Ccos+%5Cfrac+%7B%5Ctheta%7D+%7B2%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Rz | `__quantum__qis__rz__body (%Qubit q, double theta)` | Rotate a qubit around the Pauli Z axis | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+e%5E%7B-i+%5Ctheta%2F2%7D+%26+0+%5C%5C+0+%26+e%5E%7Bi+%5Ctheta%2F2%7D+%5C%5C+%5Cend%7Bbmatrix%7D) | |
| S | `__quantum__qis__s__body (%Qubit q)` | S (phase gate)  | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+i+%5C%5C+%5Cend%7Bbmatrix%7D) |
| S&dagger; | `__quantum__qis__s_adj (%Qubit q)` | The adjoint of S | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+-i+%5C%5C+%5Cend%7Bbmatrix%7D) |
| T | `__quantum__qis__t__body (%Qubit q)` | T | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+e%5E%7Bi%5Cpi%2F4%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| T&dagger; | `__quantum__qis__t__adj (%Qubit q)` | The adjoint of T operation | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+e%5E%7B-i%5Cpi%2F4%7D+%5C%5C+%5Cend%7Bbmatrix%7D) |
| X | `__quantum__qis__x__body (%Qubit q)` | Pauli X | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+0+%26+1+%5C%5C+1+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Y | `__quantum__qis__y__body (%Qubit q)` | Pauli Y | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+0+%26+-i+%5C%5C+i+%26+0+%5C%5C+%5Cend%7Bbmatrix%7D) |
| Z | `__quantum__qis__z__body (%Qubit q)` | Pauli Z | ![latex](https://render.githubusercontent.com/render/math?math=%5Cdisplaystyle+%5Cbegin%7Bbmatrix%7D+1+%26+0+%5C%5C+0+%26+-1+%5C%5C+%5Cend%7Bbmatrix%7D) |
