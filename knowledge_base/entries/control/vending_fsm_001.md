---
id: "vending_fsm_001"
context.module: "VENDING"
context.data_width: 2
context.type: "vending machine FSM"
signals: ["clk", "rst_n", "coin", "total", "dispense", "change"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the vending machine accumulating each accepted coin value, reaching and exceeding the item price, dispensing the item, and returning change when overpaid.

## Notes
(none)

## RTL
```verilog
module vending(clk, rst_n, coin, total, dispense, change);
  input clk, rst_n;
  input [1:0] coin;
  output reg [3:0] total;
  output dispense, change;
  assign dispense = (total >= 4'd10);
  assign change   = (total > 4'd10);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)          total <= 4'd0;
    else if (dispense)   total <= 4'd0;
    else begin
      case (coin)
        2'd1: total <= total + 4'd1;
        2'd2: total <= total + 4'd5;
        default: total <= total;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_vending (ref logic [1:0] coin, ref logic [3:0] total, ref logic dispense, change) @(posedge clk);
  coin_cp : coverpoint coin {
    bins none    = {2'd0};
    bins nickel  = {2'd1};
    bins dime    = {2'd2};
    bins invalid = {2'd3};
  }
  total_cp : coverpoint total {
    bins empty_t  = {0};
    bins partial  = {[1:9]};
    bins exact    = {10};
    bins over     = {[11:15]};
  }
  dispense_cp : coverpoint dispense {
    bins waiting   = {0};
    bins dispensed = {1};
  }
  change_cp : coverpoint change {
    bins no_change = {0};
    bins change    = {1};
  }
  coin_x_total     : cross coin_cp, total_cp;
  dispense_x_change: cross dispense_cp, change_cp;
endgroup
```
