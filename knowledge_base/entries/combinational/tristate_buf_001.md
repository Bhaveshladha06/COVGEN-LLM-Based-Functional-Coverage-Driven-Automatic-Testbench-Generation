---
id: "tristate_buf_001"
context.module: "TRISTATE_BUF"
context.data_width: 8
context.type: "tri-state buffer"
signals: ["din", "oe", "dout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the tri-state buffer with the output enable asserted for a spread of data values and deasserted for the high-impedance state, crossing enable against data.

## Notes
(none)

## RTL
```verilog
module tristate_buf(din, oe, dout);
  input [7:0] din;
  input oe;
  output [7:0] dout;
  assign dout = oe ? din : 8'bz;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_tribuf (ref logic [7:0] din, ref logic oe);
  oe_cp : coverpoint oe {
    bins hiz    = {0};
    bins driven = {1};
  }
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  oe_x_din : cross oe_cp, din_cp;
endgroup
```
