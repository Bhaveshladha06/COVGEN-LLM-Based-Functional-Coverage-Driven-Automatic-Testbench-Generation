---
id: "sign_extend_001"
context.module: "SIGN_EXTEND"
context.data_width: 8
context.type: "sign extension unit"
signals: ["din", "dout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the sign extension unit for positive and negative inputs, the zero input, and the extreme representable values, confirming the upper bits replicate the sign.

## Notes
(none)

## RTL
```verilog
module sign_extend(din, dout);
  input [7:0] din;
  output [15:0] dout;
  assign dout = {{8{din[7]}}, din};
endmodule
```

## Coverage model
```systemverilog
covergroup cg_sext (ref logic [7:0] din, ref logic [15:0] dout);
  din_cp : coverpoint din {
    bins zero     = {8'h00};
    bins positive = {[8'h01:8'h7F]};
    bins negative = {[8'h80:8'hFE]};
    bins neg_one  = {8'hFF};
  }
  sign_cp : coverpoint dout[15] {
    bins pos = {0};
    bins neg = {1};
  }
  din_x_sign : cross din_cp, sign_cp;
endgroup
```
