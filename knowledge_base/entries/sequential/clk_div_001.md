---
id: "clk_div_001"
context.module: "CLK_DIV"
context.data_width: 4
context.type: "clock divider"
signals: ["clk", "rst_n", "en", "clk_out"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the clock divider producing both output phases, the internal divide counter across its full range, and the output toggling only while the enable is asserted.

## Notes
(none)

## RTL
```verilog
module clk_div(clk, rst_n, en, clk_out);
  input clk, rst_n, en;
  output reg clk_out;
  reg [3:0] cnt;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt     <= 4'b0;
      clk_out <= 1'b0;
    end else if (en) begin
      if (cnt == 4'hF) begin
        cnt     <= 4'b0;
        clk_out <= ~clk_out;
      end else cnt <= cnt + 1'b1;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_clkdiv (ref logic [3:0] cnt, ref logic en, clk_out) @(posedge clk);
  cnt_cp : coverpoint cnt {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  en_cp : coverpoint en {
    bins stopped = {0};
    bins running = {1};
  }
  out_trans_cp : coverpoint clk_out {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
  }
  cnt_x_en : cross cnt_cp, en_cp;
endgroup
```
