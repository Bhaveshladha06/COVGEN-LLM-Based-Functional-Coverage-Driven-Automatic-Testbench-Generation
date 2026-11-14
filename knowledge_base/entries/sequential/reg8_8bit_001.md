---
id: "reg8_8bit_001"
context.module: "REG8"
context.data_width: 8
context.type: "8-bit register with load"
signals: ["clk", "rst_n", "load", "din", "dout"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the 8-bit register loading data across value ranges, holding its contents when load is deasserted, the reset-to-zero behaviour, and the cross of load against data range.

## Notes
(none)

## RTL
```verilog
module reg8(clk, rst_n, load, din, dout);
  input clk, rst_n, load;
  input [7:0] din;
  output reg [7:0] dout;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)    dout <= 8'b0;
    else if (load) dout <= din;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_reg8 (ref logic [7:0] din, dout, ref logic load) @(posedge clk);
  load_cp : coverpoint load {
    bins hold = {0};
    bins load = {1};
  }
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  dout_cp : coverpoint dout {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  load_x_din : cross load_cp, din_cp;
endgroup
```
