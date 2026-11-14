---
id: "fifo_sync_8bit_001"
context.module: "FIFO_SYNC"
context.data_width: 8
context.type: "synchronous FIFO"
signals: ["clk", "rst_n", "wr_en", "rd_en", "din", "dout", "full", "empty"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the synchronous FIFO going both full and empty, simultaneous read and write while partially filled, write attempts while full and read attempts while empty being rejected, and the cross of write against read enables.

## Notes
(none)

## RTL
```verilog
module fifo_sync(clk, rst_n, wr_en, rd_en, din, dout, full, empty);
  input clk, rst_n, wr_en, rd_en;
  input [7:0] din;
  output reg [7:0] dout;
  output full, empty;
  reg [7:0] mem [0:7];
  reg [3:0] cnt;
  reg [2:0] wptr, rptr;
  assign full  = (cnt == 4'd8);
  assign empty = (cnt == 4'd0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cnt <= 0; wptr <= 0; rptr <= 0;
    end else begin
      if (wr_en && !full)  begin mem[wptr] <= din; wptr <= wptr + 1'b1; end
      if (rd_en && !empty) begin dout <= mem[rptr]; rptr <= rptr + 1'b1; end
      case ({wr_en && !full, rd_en && !empty})
        2'b10: cnt <= cnt + 1'b1;
        2'b01: cnt <= cnt - 1'b1;
        default: cnt <= cnt;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_fifo (ref logic [3:0] cnt, ref logic wr_en, rd_en, full, empty) @(posedge clk);
  cnt_cp : coverpoint cnt {
    bins empty_c   = {0};
    bins almost_e  = {1};
    bins mid       = {[2:6]};
    bins almost_f  = {7};
    bins full_c    = {8};
    illegal_bins overflow = {[9:15]};
  }
  wr_cp : coverpoint wr_en {
    bins idle  = {0};
    bins write = {1};
  }
  rd_cp : coverpoint rd_en {
    bins idle = {0};
    bins read = {1};
  }
  full_cp : coverpoint full {
    bins not_full = {0};
    bins is_full  = {1};
  }
  empty_cp : coverpoint empty {
    bins not_empty = {0};
    bins is_empty  = {1};
  }
  cnt_trans_cp : coverpoint cnt {
    bins fill_up   = (7 => 8);
    bins drain_out = (1 => 0);
  }
  wr_x_rd    : cross wr_cp, rd_cp;
  wr_x_full  : cross wr_cp, full_cp;
  rd_x_empty : cross rd_cp, empty_cp;
endgroup
```
