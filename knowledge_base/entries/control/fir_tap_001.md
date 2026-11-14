---
id: "fir_tap_001"
context.module: "FIR_TAP"
context.data_width: 8
context.type: "FIR filter tap"
signals: ["clk", "rst_n", "en", "din", "coeff", "dout"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the FIR filter tap for zero, positive, and maximum sample and coefficient values, the delay line propagating samples, and the accumulated output range.

## Notes
(none)

## RTL
```verilog
module fir_tap(clk, rst_n, en, din, coeff, dout);
  input clk, rst_n, en;
  input [7:0] din, coeff;
  output reg [15:0] dout;
  reg [7:0] delay;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      delay <= 8'b0; dout <= 16'b0;
    end else if (en) begin
      delay <= din;
      dout  <= delay * coeff;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_fir (ref logic [7:0] din, coeff, delay, ref logic [15:0] dout, ref logic en) @(posedge clk);
  din_cp : coverpoint din {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  coeff_cp : coverpoint coeff {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  en_cp : coverpoint en {
    bins hold   = {0};
    bins filter = {1};
  }
  dout_cp : coverpoint dout {
    bins zero = {16'h0000};
    bins mid  = {[16'h0001:16'hFE00]};
    bins high = {[16'hFE01:16'hFFFF]};
  }
  din_x_coeff : cross din_cp, coeff_cp;
endgroup
```
