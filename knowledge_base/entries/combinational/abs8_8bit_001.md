---
id: "abs8_8bit_001"
context.module: "ABS8"
context.data_width: 8
context.type: "8-bit absolute value"
signals: ["din", "dout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the 8-bit absolute value unit for positive, negative, and zero inputs, including the most-negative input where the magnitude cannot be represented.

## Notes
(none)

## RTL
```verilog
module abs8(din, dout);
  input signed [7:0] din;
  output [7:0] dout;
  assign dout = din[7] ? (~din + 1'b1) : din;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_abs8 (ref logic [7:0] din, dout);
  din_cp : coverpoint din {
    bins zero      = {8'h00};
    bins positive  = {[8'h01:8'h7F]};
    bins negative  = {[8'h81:8'hFF]};
    bins most_neg  = {8'h80};
  }
  dout_cp : coverpoint dout {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'h7F]};
    bins over = {8'h80};
  }
  din_x_dout : cross din_cp, dout_cp;
endgroup
```
