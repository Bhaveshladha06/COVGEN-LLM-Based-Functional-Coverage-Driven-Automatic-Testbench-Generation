---
id: "spi_master_001"
context.module: "SPI_MASTER"
context.data_width: 8
context.type: "SPI master"
signals: ["clk", "rst_n", "start", "mosi_data", "sclk", "mosi", "cs_n", "busy", "bitcnt"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the SPI master asserting and releasing chip select, shifting all eight bit positions, both clock phases within a transfer, and the busy flag spanning a complete transaction.

## Notes
(none)

## RTL
```verilog
module spi_master(clk, rst_n, start, mosi_data, sclk, mosi, cs_n, busy, bitcnt);
  input clk, rst_n, start;
  input [7:0] mosi_data;
  output reg sclk, mosi, cs_n, busy;
  output reg [3:0] bitcnt;
  reg [7:0] shifter;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      cs_n <= 1'b1; busy <= 1'b0; bitcnt <= 4'd0; sclk <= 1'b0;
    end else if (!busy && start) begin
      shifter <= mosi_data; cs_n <= 1'b0; busy <= 1'b1; bitcnt <= 4'd0;
    end else if (busy) begin
      sclk <= ~sclk;
      if (sclk) begin
        mosi   <= shifter[7];
        shifter<= {shifter[6:0], 1'b0};
        if (bitcnt == 4'd7) begin busy <= 1'b0; cs_n <= 1'b1; end
        else bitcnt <= bitcnt + 1'b1;
      end
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_spi (ref logic [3:0] bitcnt, ref logic cs_n, busy, sclk, start) @(posedge clk);
  bitcnt_cp : coverpoint bitcnt {
    bins bit_n[] = {[0:7]};
    illegal_bins overflow = {[8:15]};
  }
  cs_cp : coverpoint cs_n {
    bins selected   = {0};
    bins deselected = {1};
  }
  busy_cp : coverpoint busy {
    bins idle = {0};
    bins busy = {1};
  }
  sclk_cp : coverpoint sclk {
    bins low  = {0};
    bins high = {1};
  }
  cs_trans_cp : coverpoint cs_n {
    bins assert_cs  = (1 => 0);
    bins release_cs = (0 => 1);
  }
  bitcnt_x_sclk : cross bitcnt_cp, sclk_cp;
  cs_x_busy     : cross cs_cp, busy_cp;
endgroup
```
