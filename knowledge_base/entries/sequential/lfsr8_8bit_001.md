---
id: "lfsr8_8bit_001"
context.module: "LFSR8"
context.data_width: 8
context.type: "8-bit LFSR"
signals: ["clk", "rst_n", "en", "lfsr"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the 8-bit linear feedback shift register producing values across its range, the seed value after reset, the feedback bit in both states, and the all-zero lock-up state treated as illegal.

## Notes
(none)

## RTL
```verilog
module lfsr8(clk, rst_n, en, lfsr);
  input clk, rst_n, en;
  output reg [7:0] lfsr;
  wire fb = lfsr[7] ^ lfsr[5] ^ lfsr[4] ^ lfsr[3];
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  lfsr <= 8'hFF;
    else if (en) lfsr <= {lfsr[6:0], fb};
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_lfsr8 (ref logic [7:0] lfsr, ref logic en) @(posedge clk);
  lfsr_cp : coverpoint lfsr {
    bins seed = {8'hFF};
    bins low  = {[8'h01:8'h7F]};
    bins high = {[8'h80:8'hFE]};
    illegal_bins lockup = {8'h00};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins shift = {1};
  }
  lsb_cp : coverpoint lfsr[0] {
    bins fb_zero = {0};
    bins fb_one  = {1};
  }
  lfsr_x_en : cross lfsr_cp, en_cp;
endgroup
```
