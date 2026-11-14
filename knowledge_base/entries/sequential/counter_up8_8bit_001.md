---
id: "counter_up8_8bit_001"
context.module: "COUNTER_UP8"
context.data_width: 8
context.type: "8-bit up counter"
signals: ["clk", "rst_n", "en", "count"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the 8-bit up counter reaching its maximum value and wrapping around to zero on the next enabled clock edge, holding its value while the enable is deasserted, and the reset returning the count to zero.

## Notes
(none)

## RTL
```verilog
module counter_up8(clk, rst_n, en, count);
  input clk, rst_n, en;
  output reg [7:0] count;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 8'b0;
    else if (en) count <= count + 1'b1;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_cnt_up8 (ref logic [7:0] count, ref logic en, rst_n) @(posedge clk);
  count_cp : coverpoint count {
    bins zero = {8'h00};
    bins low  = {[8'h01:8'h7F]};
    bins high = {[8'h80:8'hFE]};
    bins max  = {8'hFF};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  rst_cp : coverpoint rst_n {
    bins asserted  = {0};
    bins deasserted= {1};
  }
  count_trans_cp : coverpoint count {
    bins wrap      = (8'hFF => 8'h00);
    bins hold_zero = (8'h00 => 8'h00);
    bins hold_max  = (8'hFF => 8'hFF);
  }
  count_x_en : cross count_cp, en_cp;
  en_x_rst   : cross en_cp, rst_cp;
endgroup
```
