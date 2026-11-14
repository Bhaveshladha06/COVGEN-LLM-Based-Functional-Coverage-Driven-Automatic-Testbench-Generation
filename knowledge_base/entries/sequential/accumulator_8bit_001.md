---
id: "accumulator_8bit_001"
context.module: "ACCUMULATOR"
context.data_width: 8
context.type: "8-bit accumulator"
signals: ["clk", "rst_n", "en", "din", "acc", "ovf"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the accumulator summing input values across ranges, holding when disabled, clearing on reset, and asserting the overflow flag when the accumulated total wraps.

## Notes
(none)

## RTL
```verilog
module accumulator(clk, rst_n, en, din, acc, ovf);
  input clk, rst_n, en;
  input [7:0] din;
  output reg [7:0] acc;
  output reg ovf;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      acc <= 8'b0;
      ovf <= 1'b0;
    end else if (en) begin
      {ovf, acc} <= acc + din;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_accum (ref logic [7:0] din, acc, ref logic en, ovf) @(posedge clk);
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  acc_cp : coverpoint acc {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins accum = {1};
  }
  ovf_cp : coverpoint ovf {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  din_x_ovf : cross din_cp, ovf_cp;
  acc_x_en  : cross acc_cp, en_cp;
endgroup
```
