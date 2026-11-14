---
id: "uart_tx_001"
context.module: "UART_TX"
context.data_width: 8
context.type: "UART transmitter"
signals: ["clk", "rst_n", "start", "data", "tx", "busy", "state"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the UART transmitter through idle, start bit, all data bit positions, and stop bit states, transmitting both all-zero and all-one data payloads, and the busy flag across a full frame.

## Notes
(none)

## RTL
```verilog
module uart_tx(clk, rst_n, start, data, tx, busy, state);
  input clk, rst_n, start;
  input [7:0] data;
  output reg tx;
  output busy;
  output reg [1:0] state;
  reg [2:0] bitpos;
  reg [7:0] shifter;
  parameter IDLE=2'd0, START=2'd1, DATA=2'd2, STOP=2'd3;
  assign busy = (state != IDLE);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      state <= IDLE; tx <= 1'b1; bitpos <= 3'd0;
    end else begin
      case (state)
        IDLE:  if (start) begin shifter <= data; tx <= 1'b0; state <= START; end
        START: begin tx <= shifter[0]; bitpos <= 3'd0; state <= DATA; end
        DATA:  begin
                 tx <= shifter[bitpos];
                 if (bitpos == 3'd7) state <= STOP;
                 else bitpos <= bitpos + 1'b1;
               end
        STOP:  begin tx <= 1'b1; state <= IDLE; end
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_uart_tx (ref logic [1:0] state, ref logic [2:0] bitpos, ref logic [7:0] data, ref logic start, busy, tx) @(posedge clk);
  state_cp : coverpoint state {
    bins idle  = {2'd0};
    bins start = {2'd1};
    bins data  = {2'd2};
    bins stop  = {2'd3};
  }
  bitpos_cp : coverpoint bitpos {
    bins bit_n[] = {[0:7]};
  }
  data_cp : coverpoint data {
    bins all_zero = {8'h00};
    bins all_one  = {8'hFF};
    bins mid      = {[8'h01:8'hFE]};
  }
  busy_cp : coverpoint busy {
    bins idle_b = {0};
    bins busy_b = {1};
  }
  state_trans_cp : coverpoint state {
    bins begin_frame = (2'd0 => 2'd1);
    bins send_data   = (2'd1 => 2'd2);
    bins finish      = (2'd2 => 2'd3);
    bins back_idle   = (2'd3 => 2'd0);
  }
  state_x_data : cross state_cp, data_cp;
endgroup
```
