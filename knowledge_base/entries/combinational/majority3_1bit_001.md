---
id: "majority3_1bit_001"
context.module: "MAJORITY3"
context.data_width: 1
context.type: "3-input majority voter"
signals: ["a", "b", "c", "y"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the 3-input majority voter for all eight input combinations and both output values, confirming the output follows the majority of the inputs.

## Notes
(none)

## RTL
```verilog
module majority3(a, b, c, y);
  input a, b, c;
  output y;
  assign y = (a & b) | (b & c) | (a & c);
endmodule
```

## Coverage model
```systemverilog
covergroup cg_maj3 (ref logic a, b, c, y);
  abc_cp : coverpoint {a, b, c} {
    bins combo[] = {[3'b000:3'b111]};
  }
  y_cp : coverpoint y {
    bins minority = {0};
    bins majority = {1};
  }
  abc_x_y : cross abc_cp, y_cp;
endgroup
```
