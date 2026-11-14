---
id: "parity8_8bit_001"
context.module: "PARITY8"
context.data_width: 8
context.type: "8-bit parity generator"
signals: ["din", "even", "odd"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-bit parity generator behavior for both even and odd parity results, the all-zero and all-one inputs, and inputs across a spread of set-bit counts.

## Notes
(none)

## RTL
```verilog
module parity8(din, even, odd);
  input [7:0] din;
  output even, odd;
  assign odd  = ^din;
  assign even = ~(^din);
endmodule
```

## Coverage model
```systemverilog
covergroup cg_parity8 (ref logic [7:0] din, ref logic even, odd);
  din_cp : coverpoint din {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins low      = {[8'h01:8'h7F]};
    bins high     = {[8'h80:8'hFE]};
  }
  odd_cp : coverpoint odd {
    bins even_parity = {0};
    bins odd_parity  = {1};
  }
  din_x_odd : cross din_cp, odd_cp;
endgroup
```
