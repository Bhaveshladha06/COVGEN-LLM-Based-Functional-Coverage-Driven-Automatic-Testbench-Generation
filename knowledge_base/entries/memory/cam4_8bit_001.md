---
id: "cam4_8bit_001"
context.module: "CAM4"
context.data_width: 8
context.type: "content addressable memory"
signals: ["clk", "rst_n", "we", "waddr", "wdata", "search", "match", "match_addr"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the CAM reporting a match when the searched value is present and no match when absent, matches at the first and last entries, and writes to every entry.

## Notes
(none)

## RTL
```verilog
module cam4(clk, rst_n, we, waddr, wdata, search, match, match_addr);
  input clk, rst_n, we;
  input [1:0] waddr;
  input [7:0] wdata, search;
  output match;
  output reg [1:0] match_addr;
  reg [7:0] mem [0:3];
  wire [3:0] hit;
  assign hit[0] = (mem[0] == search);
  assign hit[1] = (mem[1] == search);
  assign hit[2] = (mem[2] == search);
  assign hit[3] = (mem[3] == search);
  assign match = |hit;
  always @(*) begin
    casex (hit)
      4'bxxx1: match_addr = 2'd0;
      4'bxx10: match_addr = 2'd1;
      4'bx100: match_addr = 2'd2;
      4'b1000: match_addr = 2'd3;
      default: match_addr = 2'd0;
    endcase
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      mem[0] <= 0; mem[1] <= 0; mem[2] <= 0; mem[3] <= 0;
    end else if (we) mem[waddr] <= wdata;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_cam4 (ref logic [1:0] waddr, match_addr, ref logic we, match) @(posedge clk);
  waddr_cp : coverpoint waddr {
    bins entry[] = {[0:3]};
  }
  match_cp : coverpoint match {
    bins miss = {0};
    bins hit  = {1};
  }
  match_addr_cp : coverpoint match_addr {
    bins entry[] = {[0:3]};
  }
  we_cp : coverpoint we {
    bins idle  = {0};
    bins write = {1};
  }
  match_x_addr : cross match_cp, match_addr_cp;
  we_x_waddr   : cross we_cp, waddr_cp;
endgroup
```
