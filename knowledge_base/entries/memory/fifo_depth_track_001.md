---
id: "fifo_depth_track_001"
context.module: "FIFO_WATERMARK"
context.data_width: 8
context.type: "FIFO with watermark flags"
signals: ["clk", "rst_n", "wr_en", "rd_en", "count", "almost_full", "almost_empty"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the FIFO watermark flags asserting and deasserting as occupancy crosses the programmable thresholds, and the occupancy transitioning across each watermark boundary in both directions.

## Notes
(none)

## RTL
```verilog
module fifo_watermark(clk, rst_n, wr_en, rd_en, count, almost_full, almost_empty);
  input clk, rst_n, wr_en, rd_en;
  output reg [3:0] count;
  output almost_full, almost_empty;
  assign almost_full  = (count >= 4'd12);
  assign almost_empty = (count <= 4'd2);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) count <= 4'b0;
    else begin
      case ({wr_en && count < 15, rd_en && count > 0})
        2'b10: count <= count + 1'b1;
        2'b01: count <= count - 1'b1;
        default: count <= count;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_fifo_wm (ref logic [3:0] count, ref logic wr_en, rd_en, almost_full, almost_empty) @(posedge clk);
  count_cp : coverpoint count {
    bins very_low  = {[0:2]};
    bins low       = {[3:7]};
    bins high      = {[8:11]};
    bins very_high = {[12:15]};
  }
  af_cp : coverpoint almost_full {
    bins clear = {0};
    bins set   = {1};
  }
  ae_cp : coverpoint almost_empty {
    bins clear = {0};
    bins set   = {1};
  }
  count_trans_cp : coverpoint count {
    bins cross_ae_up   = (2 => 3);
    bins cross_ae_down = (3 => 2);
    bins cross_af_up   = (11 => 12);
    bins cross_af_down = (12 => 11);
  }
  af_x_ae : cross af_cp, ae_cp;
endgroup
```
