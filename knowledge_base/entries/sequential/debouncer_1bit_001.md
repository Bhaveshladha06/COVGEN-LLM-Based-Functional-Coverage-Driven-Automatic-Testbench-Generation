---
id: "debouncer_1bit_001"
context.module: "DEBOUNCER"
context.data_width: 1
context.type: "switch debouncer"
signals: ["clk", "rst_n", "noisy", "clean"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the debouncer holding its output stable while the input is bouncing, propagating a change only after the input has been stable for the full count, and both output states.

## Notes
(none)

## RTL
```verilog
module debouncer(clk, rst_n, noisy, clean);
  input clk, rst_n, noisy;
  output reg clean;
  reg [3:0] cnt;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt   <= 4'b0;
      clean <= 1'b0;
    end else if (noisy != clean) begin
      if (cnt == 4'hF) begin
        clean <= noisy;
        cnt   <= 4'b0;
      end else cnt <= cnt + 1'b1;
    end else cnt <= 4'b0;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_debounce (ref logic noisy, clean) @(posedge clk);
  noisy_cp : coverpoint noisy {
    bins low  = {0};
    bins high = {1};
  }
  clean_cp : coverpoint clean {
    bins low  = {0};
    bins high = {1};
  }
  clean_trans_cp : coverpoint clean {
    bins settle_high = (0 => 1);
    bins settle_low  = (1 => 0);
    bins stable_low  = (0 => 0);
    bins stable_high = (1 => 1);
  }
  noisy_x_clean : cross noisy_cp, clean_cp;
endgroup
```
