---
id: "circular_buffer_8bit_001"
context.module: "CIRCULAR_BUFFER"
context.data_width: 8
context.type: "circular buffer"
signals: ["clk", "rst_n", "wr_en", "rd_en", "din", "dout", "count"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the circular buffer wrapping its write and read pointers past the end of storage, the occupancy count spanning empty through full, and simultaneous read and write.

## Notes
(none)

## RTL
```verilog
module circular_buffer(clk, rst_n, wr_en, rd_en, din, dout, count);
  input clk, rst_n, wr_en, rd_en;
  input [7:0] din;
  output reg [7:0] dout;
  output reg [2:0] count;
  reg [7:0] mem [0:3];
  reg [1:0] wptr, rptr;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wptr <= 0; rptr <= 0; count <= 0;
    end else begin
      if (wr_en && count < 4) begin mem[wptr] <= din; wptr <= wptr + 1'b1; end
      if (rd_en && count > 0) begin dout <= mem[rptr]; rptr <= rptr + 1'b1; end
      case ({wr_en && count < 4, rd_en && count > 0})
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
covergroup cg_circbuf (ref logic [2:0] count, ref logic [1:0] wptr, rptr, ref logic wr_en, rd_en) @(posedge clk);
  count_cp : coverpoint count {
    bins empty_c = {0};
    bins mid     = {[1:3]};
    bins full_c  = {4};
    illegal_bins overflow = {[5:7]};
  }
  wptr_cp : coverpoint wptr {
    bins p[] = {[0:3]};
  }
  wptr_trans_cp : coverpoint wptr {
    bins wrap = (3 => 0);
    bins step = (0 => 1);
  }
  wr_cp : coverpoint wr_en {
    bins idle  = {0};
    bins write = {1};
  }
  rd_cp : coverpoint rd_en {
    bins idle = {0};
    bins read = {1};
  }
  wr_x_rd    : cross wr_cp, rd_cp;
  count_x_wr : cross count_cp, wr_cp;
endgroup
```
