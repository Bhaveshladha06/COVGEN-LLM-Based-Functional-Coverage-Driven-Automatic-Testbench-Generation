---
id: "barrel_shift8_8bit_001"
context.module: "BARREL_SHIFT8"
context.data_width: 8
context.type: "8-bit barrel shifter"
signals: ["din", "shamt", "dir", "dout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-bit barrel shifter behavior for every shift amount including zero and maximum, both shift directions, and the cross of direction against shift amount.

## Notes
(none)

## RTL
```verilog
module barrel_shift8(din, shamt, dir, dout);
  input [7:0] din;
  input [2:0] shamt;
  input dir;
  output [7:0] dout;
  assign dout = dir ? (din >> shamt) : (din << shamt);
endmodule
```

## Coverage model
```systemverilog
covergroup cg_barrel (ref logic [7:0] din, dout, ref logic [2:0] shamt, ref logic dir);
  shamt_cp : coverpoint shamt {
    bins no_shift = {0};
    bins small_sh  = {[1:3]};
    bins large_sh  = {[4:7]};
  }
  dir_cp : coverpoint dir {
    bins left  = {0};
    bins right = {1};
  }
  dout_cp : coverpoint dout {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  dir_x_shamt : cross dir_cp, shamt_cp;
endgroup
```
