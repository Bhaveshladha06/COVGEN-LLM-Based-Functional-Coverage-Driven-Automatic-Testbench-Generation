---
id: "bcd_counter_4bit_001"
context.module: "BCD_COUNTER"
context.data_width: 4
context.type: "BCD decade counter"
signals: ["clk", "rst_n", "en", "count", "carry"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the BCD decade counter visiting every decimal digit, rolling over from nine to zero, asserting the carry output on rollover, and never entering a non-decimal state.

## Notes
(none)

## RTL
```verilog
module bcd_counter(clk, rst_n, en, count, carry);
  input clk, rst_n, en;
  output reg [3:0] count;
  output carry;
  assign carry = en && (count == 4'd9);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)  count <= 4'd0;
    else if (en) count <= (count == 4'd9) ? 4'd0 : (count + 1'b1);
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_bcd_cnt (ref logic [3:0] count, ref logic en, carry) @(posedge clk);
  count_cp : coverpoint count {
    bins digit[] = {[0:9]};
    illegal_bins non_bcd = {[10:15]};
  }
  carry_cp : coverpoint carry {
    bins no_carry = {0};
    bins carry    = {1};
  }
  en_cp : coverpoint en {
    bins hold  = {0};
    bins count = {1};
  }
  count_trans_cp : coverpoint count {
    bins rollover = (9 => 0);
    bins step     = (0 => 1);
  }
  count_x_carry : cross count_cp, carry_cp;
endgroup
```
