---
id: "alu8_8bit_001"
context.module: "ALU8"
context.data_width: 8
context.type: "8-bit ALU"
signals: ["a", "b", "op", "result", "zero"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-bit ALU behavior for every opcode, operand value ranges, the zero flag in both states, and the cross of opcode against the zero flag to confirm each operation can produce zero.

## Notes
(none)

## RTL
```verilog
module alu8(a, b, op, result, zero);
  input [7:0] a, b;
  input [2:0] op;
  output reg [7:0] result;
  output zero;
  assign zero = (result == 8'b0);
  always @(*) begin
    case (op)
      3'd0: result = a + b;
      3'd1: result = a - b;
      3'd2: result = a & b;
      3'd3: result = a | b;
      3'd4: result = a ^ b;
      3'd5: result = ~a;
      3'd6: result = a << 1;
      3'd7: result = a >> 1;
    endcase
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_alu8 (ref logic [7:0] a, b, result, ref logic [2:0] op, ref logic zero);
  op_cp : coverpoint op {
    bins op_add = {0};
    bins op_sub = {1};
    bins op_and = {2};
    bins op_or  = {3};
    bins op_xor = {4};
    bins op_not = {5};
    bins op_shl = {6};
    bins op_shr = {7};
  }
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  result_cp : coverpoint result {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  zero_cp : coverpoint zero {
    bins nonzero = {0};
    bins is_zero = {1};
  }
  op_x_zero : cross op_cp, zero_cp;
  op_x_a    : cross op_cp, a_cp;
endgroup
```
