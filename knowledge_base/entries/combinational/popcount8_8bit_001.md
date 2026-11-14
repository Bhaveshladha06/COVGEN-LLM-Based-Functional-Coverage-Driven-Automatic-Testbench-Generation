---
id: "popcount8_8bit_001"
context.module: "POPCOUNT8"
context.data_width: 8
context.type: "8-bit population counter"
signals: ["din", "count"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the 8-bit population counter for every possible set-bit count from zero through eight, including the all-zero and all-one inputs.

## Notes
(none)

## RTL
```verilog
module popcount8(din, count);
  input [7:0] din;
  output [3:0] count;
  assign count = din[0] + din[1] + din[2] + din[3] +
                 din[4] + din[5] + din[6] + din[7];
endmodule
```

## Coverage model
```systemverilog
covergroup cg_popcount (ref logic [7:0] din, ref logic [3:0] count);
  din_cp : coverpoint din {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins others   = {[8'h01:8'hFE]};
  }
  count_cp : coverpoint count {
    bins n[] = {[0:8]};
    illegal_bins impossible = {[9:15]};
  }
endgroup
```
