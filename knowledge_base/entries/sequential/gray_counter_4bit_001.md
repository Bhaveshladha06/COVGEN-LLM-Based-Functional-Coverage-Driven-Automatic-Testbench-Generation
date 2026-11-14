---
id: "gray_counter_4bit_001"
context.module: "GRAY_COUNTER"
context.data_width: 4
context.type: "4-bit Gray code counter"
signals: ["clk", "rst_n", "en", "gray"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the Gray counter producing every Gray code value, wrapping from the last code back to zero, and holding while disabled, confirming only one bit changes per step.

## Notes
(none)

## RTL
```verilog
module gray_counter(clk, rst_n, en, gray);
  input clk, rst_n, en;
  output [3:0] gray;
  reg [3:0] bin;
  assign gray = bin ^ (bin >> 1);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  bin <= 4'b0;
    else if (en) bin <= bin + 1'b1;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_gray_cnt (ref logic [3:0] gray, ref logic en) @(posedge clk);
  gray_cp : coverpoint gray {
    bins code[] = {[0:15]};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins count = {1};
  }
  gray_trans_cp : coverpoint gray {
    bins first_step = (4'b0000 => 4'b0001);
    bins wrap       = (4'b1000 => 4'b0000);
  }
  gray_x_en : cross gray_cp, en_cp;
endgroup
```
